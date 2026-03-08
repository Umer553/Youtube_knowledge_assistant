"""
URL Parser Module
Resolves YouTube URLs (single video, playlist, channel) into a list of video IDs
with metadata. Handles all common YouTube URL formats.
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class VideoInfo:
    """Represents a single YouTube video's basic info."""
    video_id: str
    title: str = ""
    channel: str = ""
    duration: str = ""
    thumbnail_url: str = ""
    url: str = ""

    def __post_init__(self):
        if not self.url:
            self.url = f"https://www.youtube.com/watch?v={self.video_id}"
        if not self.thumbnail_url:
            self.thumbnail_url = f"https://img.youtube.com/vi/{self.video_id}/mqdefault.jpg"


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract video ID from various YouTube URL formats.
    Supports: youtube.com/watch, youtu.be, youtube.com/embed, etc.
    """
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def extract_playlist_id(url: str) -> Optional[str]:
    """Extract playlist ID from a YouTube playlist URL."""
    match = re.search(r'[?&]list=([a-zA-Z0-9_-]+)', url)
    return match.group(1) if match else None


def extract_channel_identifier(url: str) -> Optional[str]:
    """Extract channel ID or handle from YouTube channel URL."""
    patterns = [
        r'youtube\.com/channel/([a-zA-Z0-9_-]+)',
        r'youtube\.com/@([a-zA-Z0-9_.-]+)',
        r'youtube\.com/c/([a-zA-Z0-9_.-]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def classify_url(url: str) -> str:
    """
    Classify a YouTube URL into one of: 'video', 'playlist', 'channel', 'unknown'.
    """
    if extract_playlist_id(url):
        return "playlist"
    if extract_video_id(url):
        return "video"
    if extract_channel_identifier(url):
        return "channel"
    return "unknown"


def resolve_video_ids(url: str, youtube_api_key: str = "", max_videos: int = 50) -> list[VideoInfo]:
    """
    Master resolver: takes any YouTube URL and returns a list of VideoInfo objects.
    
    For single videos: returns a list with one VideoInfo.
    For playlists: uses yt-dlp to extract all video IDs in the playlist.
    For channels: fetches recent uploads via YouTube Data API or yt-dlp.
    
    Args:
        url: Any YouTube URL
        youtube_api_key: YouTube Data API key (needed for channel/playlist metadata)
        max_videos: Maximum number of videos to resolve from playlists/channels
        
    Returns:
        List of VideoInfo objects
    """
    url_type = classify_url(url)

    if url_type == "video":
        video_id = extract_video_id(url)
        return [VideoInfo(video_id=video_id)] if video_id else []

    if url_type == "playlist":
        return _resolve_playlist(url, max_videos)

    if url_type == "channel":
        return _resolve_channel(url, max_videos)

    return []


def _resolve_playlist(url: str, max_videos: int) -> list[VideoInfo]:
    """
    Resolve all video IDs from a YouTube playlist using yt-dlp.
    yt-dlp is used because it doesn't require an API key and handles
    all playlist types including mixes and auto-generated playlists.
    """
    try:
        import yt_dlp

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,      # Don't download, just get metadata
            'playlistend': max_videos,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if not info or 'entries' not in info:
            return []

        videos = []
        for entry in info['entries']:
            if entry and entry.get('id'):
                videos.append(VideoInfo(
                    video_id=entry['id'],
                    title=entry.get('title', ''),
                    channel=entry.get('uploader', ''),
                    duration=str(entry.get('duration', '')),
                ))
        return videos[:max_videos]

    except ImportError:
        print("yt-dlp not installed. Install with: pip install yt-dlp")
        return []
    except Exception as e:
        print(f"Error resolving playlist: {e}")
        return []


def _resolve_channel(url: str, max_videos: int) -> list[VideoInfo]:
    """
    Resolve recent uploads from a YouTube channel.
    Uses yt-dlp to get the channel's uploads playlist.
    """
    try:
        import yt_dlp

        # yt-dlp can handle channel URLs directly
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'playlistend': max_videos,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if not info:
            return []

        entries = info.get('entries', [])
        videos = []
        for entry in entries:
            if entry and entry.get('id'):
                videos.append(VideoInfo(
                    video_id=entry['id'],
                    title=entry.get('title', ''),
                    channel=entry.get('uploader', info.get('uploader', '')),
                    duration=str(entry.get('duration', '')),
                ))
        return videos[:max_videos]

    except Exception as e:
        print(f"Error resolving channel: {e}")
        return []


def get_video_metadata_batch(video_ids: list[str], api_key: str) -> dict:
    """
    Fetch detailed metadata for multiple videos using YouTube Data API v3.
    More efficient than individual calls — batches up to 50 IDs per request.
    
    Returns:
        Dict mapping video_id -> {title, channel, duration, description, ...}
    """
    if not api_key:
        return {}

    try:
        from googleapiclient.discovery import build

        youtube = build('youtube', 'v3', developerKey=api_key)
        metadata = {}

        # Process in batches of 50 (API limit)
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i:i + 50]
            request = youtube.videos().list(
                part='snippet,contentDetails,statistics',
                id=','.join(batch)
            )
            response = request.execute()

            for item in response.get('items', []):
                vid = item['id']
                snippet = item.get('snippet', {})
                stats = item.get('statistics', {})
                metadata[vid] = {
                    'title': snippet.get('title', ''),
                    'channel': snippet.get('channelTitle', ''),
                    'description': snippet.get('description', ''),
                    'published_at': snippet.get('publishedAt', ''),
                    'duration': item.get('contentDetails', {}).get('duration', ''),
                    'view_count': int(stats.get('viewCount', 0)),
                    'like_count': int(stats.get('likeCount', 0)),
                    'comment_count': int(stats.get('commentCount', 0)),
                }

        return metadata

    except Exception as e:
        print(f"Error fetching video metadata: {e}")
        return {}
