"""
Sentiment Analysis Module
Two-pass analysis of YouTube comments:
  Pass 1: VADER for quick polarity scoring (positive/negative/neutral)
  Pass 2: LLM-based topic clustering to group comments by theme
"""

from dataclasses import dataclass, field
from typing import Optional

from core.ingestion.comments import YouTubeComment


@dataclass
class CommentSentiment:
    """Sentiment scores for a single comment."""
    comment_id: str
    text: str
    compound: float         # -1 (most negative) to +1 (most positive)
    positive: float
    negative: float
    neutral: float
    label: str              # 'positive', 'negative', 'neutral'


@dataclass
class SentimentSummary:
    """Aggregated sentiment analysis for a video's comments."""
    video_id: str
    total_comments: int
    positive_count: int
    negative_count: int
    neutral_count: int
    average_compound: float
    themes: list[dict] = field(default_factory=list)
    # Each theme: {'topic': str, 'sentiment': str, 'count': int, 'sample_comments': list[str]}

    @property
    def positive_pct(self) -> float:
        if self.total_comments == 0:
            return 0
        return round(self.positive_count / self.total_comments * 100, 1)

    @property
    def negative_pct(self) -> float:
        if self.total_comments == 0:
            return 0
        return round(self.negative_count / self.total_comments * 100, 1)

    @property
    def neutral_pct(self) -> float:
        if self.total_comments == 0:
            return 0
        return round(self.neutral_count / self.total_comments * 100, 1)

    @property
    def overall_sentiment(self) -> str:
        if self.average_compound >= 0.05:
            return "positive"
        elif self.average_compound <= -0.05:
            return "negative"
        return "neutral"


def analyze_sentiment_vader(comments: list[YouTubeComment]) -> list[CommentSentiment]:
    """
    Pass 1: Run VADER sentiment analysis on all comments.
    VADER is specifically designed for social media text — handles
    emojis, slang, and informal language well.
    
    Args:
        comments: List of YouTubeComment objects
        
    Returns:
        List of CommentSentiment with polarity scores
    """
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

    analyzer = SentimentIntensityAnalyzer()
    results = []

    for comment in comments:
        scores = analyzer.polarity_scores(comment.text)

        # Classify based on compound score
        compound = scores['compound']
        if compound >= 0.05:
            label = "positive"
        elif compound <= -0.05:
            label = "negative"
        else:
            label = "neutral"

        results.append(CommentSentiment(
            comment_id=comment.comment_id,
            text=comment.text,
            compound=compound,
            positive=scores['pos'],
            negative=scores['neg'],
            neutral=scores['neu'],
            label=label,
        ))

    return results


def aggregate_sentiment(
    video_id: str,
    sentiments: list[CommentSentiment]
) -> SentimentSummary:
    """
    Aggregate individual comment sentiments into a video-level summary.
    """
    if not sentiments:
        return SentimentSummary(
            video_id=video_id,
            total_comments=0,
            positive_count=0,
            negative_count=0,
            neutral_count=0,
            average_compound=0.0,
        )

    positive = sum(1 for s in sentiments if s.label == "positive")
    negative = sum(1 for s in sentiments if s.label == "negative")
    neutral = sum(1 for s in sentiments if s.label == "neutral")
    avg_compound = sum(s.compound for s in sentiments) / len(sentiments)

    return SentimentSummary(
        video_id=video_id,
        total_comments=len(sentiments),
        positive_count=positive,
        negative_count=negative,
        neutral_count=neutral,
        average_compound=round(avg_compound, 4),
    )


def cluster_comment_themes(
    comments: list[YouTubeComment],
    sentiments: list[CommentSentiment],
    llm=None,
    num_themes: int = 5,
) -> list[dict]:
    """
    Pass 2: Use LLM to cluster comments into themes/topics.
    
    This identifies what viewers are actually talking about:
    e.g., "tutorial quality", "audio issues", "requests for part 2"
    
    Args:
        comments: Raw comments
        sentiments: VADER sentiment results
        llm: LangChain LLM instance
        num_themes: Number of themes to identify
        
    Returns:
        List of theme dicts: [{topic, sentiment, count, sample_comments}]
    """
    if not comments or llm is None:
        return []

    # Build a sentiment-tagged comment list for the LLM
    # Only send top 50 comments to stay within token limits
    tagged_comments = []
    sentiment_map = {s.comment_id: s for s in sentiments}

    sorted_comments = sorted(comments, key=lambda c: c.like_count, reverse=True)[:50]

    for comment in sorted_comments:
        sent = sentiment_map.get(comment.comment_id)
        label = sent.label if sent else "unknown"
        tagged_comments.append(f"[{label}] {comment.text[:200]}")

    comments_text = "\n".join(tagged_comments)

    prompt = f"""Analyze these YouTube video comments and identify the {num_themes} main themes/topics 
viewers are discussing. Each comment has a sentiment label [positive/negative/neutral].

Comments:
{comments_text}

Respond in this exact JSON format only, no other text:
[
  {{"topic": "theme name", "sentiment": "overall sentiment of this theme", "count": approximate_count, "sample_comments": ["example 1", "example 2"]}},
  ...
]"""

    try:
        response = llm.invoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)

        import json
        # Clean potential markdown fences
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()

        themes = json.loads(cleaned)
        return themes if isinstance(themes, list) else []

    except Exception as e:
        print(f"Theme clustering failed: {e}")
        return []


def run_full_analysis(
    video_id: str,
    comments: list[YouTubeComment],
    llm=None,
    num_themes: int = 5,
) -> SentimentSummary:
    """
    Run the complete sentiment analysis pipeline:
    1. VADER scoring
    2. Aggregation
    3. LLM theme clustering (if LLM provided)
    
    Returns:
        SentimentSummary with themes attached
    """
    if not comments:
        return SentimentSummary(
            video_id=video_id,
            total_comments=0,
            positive_count=0,
            negative_count=0,
            neutral_count=0,
            average_compound=0.0,
        )

    # Pass 1: VADER
    sentiments = analyze_sentiment_vader(comments)

    # Aggregate
    summary = aggregate_sentiment(video_id, sentiments)

    # Pass 2: LLM theme clustering
    if llm is not None:
        themes = cluster_comment_themes(comments, sentiments, llm, num_themes)
        summary.themes = themes

    return summary
