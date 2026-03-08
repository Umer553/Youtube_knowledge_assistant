"""
Comment Fetcher Module
Fetches top comments from YouTube videos via the YouTube Data API v3.
Handles pagination and rate limiting.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class YouTubeComment:
    """Represents a single YouTube comment."""
    comment_id: str
    video_id: str
    author: str
    text: str
    like_count: int = 0
    reply_count: int = 0
    published_at: str = ""

    @property
    def is_popular(self) -> bool:
        """A comment is considered popular if it has 5+ likes."""
        return self.like_count >= 5


def fetch_comments(
    video_id: str,
    api_key: str,
    max_comments: int = 100,
    order: str = "relevance"
) -> list[YouTubeComment]:
    """
    Fetch top comments for a YouTube video.
    
    Args:
        video_id: YouTube video ID
        api_key: YouTube Data API v3 key
        max_comments: Maximum number of comments to fetch (max 100 per page)
        order: 'relevance' (default, best comments) or 'time' (newest first)
        
    Returns:
        List of YouTubeComment objects sorted by relevance/likes
    """
    if not api_key:
        print("Warning: No YouTube API key provided. Skipping comment fetch.")
        return []

    try:
        from googleapiclient.discovery import build

        youtube = build('youtube', 'v3', developerKey=api_key)
        comments = []
        next_page_token = None
        fetched = 0

        while fetched < max_comments:
            page_size = min(100, max_comments - fetched)

            request = youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=page_size,
                order=order,
                pageToken=next_page_token,
                textFormat='plainText',
            )

            try:
                response = request.execute()
            except Exception as e:
                error_str = str(e)
                if 'commentsDisabled' in error_str:
                    print(f"Comments are disabled for video {video_id}")
                elif 'quotaExceeded' in error_str:
                    print("YouTube API quota exceeded. Try again tomorrow.")
                else:
                    print(f"API error for video {video_id}: {e}")
                break

            for item in response.get('items', []):
                snippet = item['snippet']['topLevelComment']['snippet']
                comments.append(YouTubeComment(
                    comment_id=item['id'],
                    video_id=video_id,
                    author=snippet.get('authorDisplayName', 'Unknown'),
                    text=snippet.get('textDisplay', ''),
                    like_count=snippet.get('likeCount', 0),
                    reply_count=item['snippet'].get('totalReplyCount', 0),
                    published_at=snippet.get('publishedAt', ''),
                ))
                fetched += 1

            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break

        return comments

    except ImportError:
        print("google-api-python-client not installed.")
        return []
    except Exception as e:
        print(f"Error fetching comments for {video_id}: {e}")
        return []


def fetch_comments_batch(
    video_ids: list[str],
    api_key: str,
    max_comments_per_video: int = 100
) -> dict[str, list[YouTubeComment]]:
    """
    Fetch comments for multiple videos.
    
    Returns:
        Dict mapping video_id -> list of YouTubeComment
    """
    results = {}
    for vid in video_ids:
        print(f"  Fetching comments for {vid}...")
        results[vid] = fetch_comments(vid, api_key, max_comments_per_video)
    return results


def comments_to_dataframe(comments: list[YouTubeComment]):
    """Convert a list of comments to a pandas DataFrame for analysis."""
    try:
        import pandas as pd

        data = [
            {
                'comment_id': c.comment_id,
                'video_id': c.video_id,
                'author': c.author,
                'text': c.text,
                'like_count': c.like_count,
                'reply_count': c.reply_count,
                'published_at': c.published_at,
            }
            for c in comments
        ]
        return pd.DataFrame(data)

    except ImportError:
        print("pandas not installed.")
        return None
