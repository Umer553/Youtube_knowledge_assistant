"""
Sentiment Chain
Handles queries about viewer opinions and audience reactions.
Combines video transcript context with comment sentiment analysis.
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


SENTIMENT_PROMPT = """You are analyzing both the content of a YouTube video and 
the audience's reaction to it through comments.

VIDEO CONTENT (relevant transcript excerpts):
{video_context}

COMMENT ANALYSIS:
{sentiment_data}

USER'S QUESTION: {question}

INSTRUCTIONS:
1. Answer the question by combining insights from both the video content and comments
2. Clearly distinguish between what the video says vs what viewers think
3. Include specific sentiment statistics when relevant (e.g., "65% of comments were positive")
4. Mention specific themes that viewers discussed
5. Cite video timestamps where relevant: [@ MM:SS](url)

Response:"""


def run_sentiment_query(
    llm,
    retriever,
    question: str,
    sentiment_summary: dict,
) -> str:
    """
    Answer a question about viewer opinions by combining
    video content with comment sentiment analysis.
    
    Args:
        llm: LangChain LLM
        retriever: Retriever for video transcript content
        question: User's question about viewer sentiment
        sentiment_summary: Dict from MetadataStore.get_sentiment()
        
    Returns:
        Response combining video content and sentiment insights
    """
    from core.retrieval.retriever import format_retrieved_context

    # Get relevant video content
    docs = retriever.invoke(question)
    video_context = format_retrieved_context(docs)

    # Format sentiment data
    sentiment_data = _format_sentiment_data(sentiment_summary)

    # Run the chain
    prompt = ChatPromptTemplate.from_template(SENTIMENT_PROMPT)
    chain = prompt | llm | StrOutputParser()

    return chain.invoke({
        "video_context": video_context,
        "sentiment_data": sentiment_data,
        "question": question,
    })


def _format_sentiment_data(summary: dict) -> str:
    """Format a sentiment summary dict into readable text for the LLM."""
    if not summary:
        return "No comment analysis available for this video."

    parts = [
        f"Total comments analyzed: {summary.get('total_comments', 0)}",
        f"Positive: {summary.get('positive_count', 0)} ({_pct(summary.get('positive_count', 0), summary.get('total_comments', 1))}%)",
        f"Negative: {summary.get('negative_count', 0)} ({_pct(summary.get('negative_count', 0), summary.get('total_comments', 1))}%)",
        f"Neutral: {summary.get('neutral_count', 0)} ({_pct(summary.get('neutral_count', 0), summary.get('total_comments', 1))}%)",
        f"Average sentiment score: {summary.get('average_compound', 0):.3f} (scale: -1 to +1)",
    ]

    themes = summary.get('themes', [])
    if themes:
        parts.append("\nMain discussion themes:")
        for theme in themes:
            topic = theme.get('topic', 'Unknown')
            sent = theme.get('sentiment', 'mixed')
            count = theme.get('count', 0)
            samples = theme.get('sample_comments', [])
            parts.append(f"  - {topic} (sentiment: {sent}, ~{count} comments)")
            for sample in samples[:2]:
                parts.append(f"    > \"{sample[:100]}\"")

    return "\n".join(parts)


def _pct(count, total):
    if total == 0:
        return 0
    return round(count / total * 100, 1)
