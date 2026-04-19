"""
Transcript Engine
Extracts timestamped transcripts from YouTube videos.
Primary: youtube-transcript-api (fast, no download needed)
Fallback: OpenAI Whisper (for videos without captions)
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TranscriptSegment:
    """A single segment of a transcript with timing information."""
    text: str
    start: float        # Start time in seconds
    duration: float     # Duration in seconds

    @property
    def end(self) -> float:
        return self.start + self.duration

    @property
    def start_formatted(self) -> str:
        """Format start time as HH:MM:SS or MM:SS."""
        return _format_seconds(self.start)

    @property
    def end_formatted(self) -> str:
        return _format_seconds(self.end)

    @property
    def timestamp_url_param(self) -> int:
        """Return start time as integer seconds for YouTube URL ?t= parameter."""
        return int(self.start)


@dataclass
class VideoTranscript:
    """Complete transcript for a video with all segments."""
    video_id: str
    segments: list[TranscriptSegment]
    language: str = "en"
    source: str = "youtube_api"    # 'youtube_api' or 'whisper'

    @property
    def full_text(self) -> str:
        """Concatenate all segments into full text."""
        return " ".join(seg.text for seg in self.segments)

    @property
    def total_duration(self) -> float:
        if not self.segments:
            return 0.0
        last = self.segments[-1]
        return last.start + last.duration

    def get_text_at_time(self, time_seconds: float, window: float = 30.0) -> str:
        """Get transcript text around a specific timestamp."""
        relevant = [
            seg for seg in self.segments
            if seg.start >= time_seconds - window and seg.start <= time_seconds + window
        ]
        return " ".join(seg.text for seg in relevant)


def fetch_transcript(video_id: str, languages: list[str] = None) -> Optional[VideoTranscript]:
    """
    Fetch transcript for a YouTube video.
    
    Tries YouTube's caption API first (fast, free).
    Falls back to Whisper if no captions are available.
    
    Args:
        video_id: YouTube video ID
        languages: Preferred languages in order (default: ['en'])
        
    Returns:
        VideoTranscript object or None if extraction fails
    """
    if languages is None:
        languages = ['en', 'en-US', 'en-GB']

    # Try YouTube Transcript API first
    transcript = _fetch_from_youtube_api(video_id, languages)
    if transcript:
        return transcript

    # Fallback: try auto-generated captions in any language
    transcript = _fetch_from_youtube_api(video_id, languages=None)
    if transcript:
        return transcript

    # Last resort: Whisper (requires downloading audio)
    print(f"No captions found for {video_id}. Attempting Whisper transcription...")
    return _fetch_from_whisper(video_id)


def _fetch_from_youtube_api(
    video_id: str, languages: Optional[list[str]]
) -> Optional[VideoTranscript]:
    """Extract transcript using youtube-transcript-api.
    Handles both the legacy dict-based API (<0.6.x) and newer object-based API.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        transcript_data = None

        # Try newer API style first (0.6.3+): fetch() as class method
        if languages:
            try:
                transcript_data = YouTubeTranscriptApi.fetch(
                    video_id, languages=languages
                )
            except AttributeError:
                pass

        # Try legacy API style: get_transcript()
        if transcript_data is None and languages:
            try:
                transcript_data = YouTubeTranscriptApi.get_transcript(
                    video_id, languages=languages
                )
            except AttributeError:
                pass

        # Fallback: use list_transcripts to find any available transcript
        if transcript_data is None:
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                try:
                    transcript_obj = transcript_list.find_manually_created_transcript(
                        ['en', 'en-US', 'en-GB']
                    )
                except Exception:
                    try:
                        transcript_obj = transcript_list.find_generated_transcript(
                            ['en', 'en-US', 'en-GB']
                        )
                    except Exception:
                        transcript_obj = next(iter(transcript_list), None)
                        if transcript_obj is None:
                            return None

                transcript_data = transcript_obj.fetch()
            except AttributeError:
                pass

        # Last fallback: instantiate the class (newest API style)
        if transcript_data is None:
            try:
                api = YouTubeTranscriptApi()
                transcript_data = api.fetch(video_id, languages=languages or ['en', 'en-US'])
            except Exception:
                pass

        if transcript_data is None:
            return None

        # Normalise: support both dict entries and object entries
        segments = []
        for entry in transcript_data:
            if isinstance(entry, dict):
                text = entry.get('text', '').replace('\n', ' ').strip()
                start = entry.get('start', 0.0)
                duration = entry.get('duration', 0.0)
            else:
                text = getattr(entry, 'text', '').replace('\n', ' ').strip()
                start = getattr(entry, 'start', 0.0)
                duration = getattr(entry, 'duration', 0.0)

            if text:
                segments.append(TranscriptSegment(text=text, start=start, duration=duration))

        if not segments:
            return None

        return VideoTranscript(
            video_id=video_id,
            segments=segments,
            language="en",
            source="youtube_api",
        )

    except Exception as e:
        print(f"YouTube Transcript API failed for {video_id}: {e}")
        return None


def _fetch_from_whisper(video_id: str) -> Optional[VideoTranscript]:
    """
    Download audio and transcribe using OpenAI Whisper.
    This is the fallback for videos without captions.
    Requires: openai-whisper, yt-dlp
    """
    try:
        import whisper
        import yt_dlp
        import tempfile
        import os

        # Download audio only
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = os.path.join(tmpdir, "audio.mp3")

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(tmpdir, 'audio.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '64',   # Low quality is fine for speech
                }],
                'quiet': True,
                'no_warnings': True,
            }

            url = f"https://www.youtube.com/watch?v={video_id}"
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # Transcribe with Whisper (use 'base' model for speed)
            model = whisper.load_model("base")
            result = model.transcribe(audio_path)

            segments = []
            for seg in result.get('segments', []):
                segments.append(TranscriptSegment(
                    text=seg['text'].strip(),
                    start=seg['start'],
                    duration=seg['end'] - seg['start'],
                ))

            if not segments:
                return None

            return VideoTranscript(
                video_id=video_id,
                segments=segments,
                language=result.get('language', 'en'),
                source="whisper",
            )

    except ImportError as e:
        print(f"Whisper dependencies not available: {e}")
        return None
    except Exception as e:
        msg = str(e)
        if "ffprobe" in msg or "ffmpeg" in msg:
            print(
                f"Whisper transcription requires ffmpeg. "
                f"Install it from https://ffmpeg.org/download.html and add to PATH."
            )
        else:
            print(f"Whisper transcription failed for {video_id}: {e}")
        return None


def fetch_transcripts_batch(
    video_ids: list[str], languages: list[str] = None
) -> dict[str, Optional[VideoTranscript]]:
    """
    Fetch transcripts for multiple videos.
    Returns a dict mapping video_id -> VideoTranscript (or None).
    """
    results = {}
    for vid in video_ids:
        print(f"  Fetching transcript for {vid}...")
        results[vid] = fetch_transcript(vid, languages)
    return results


def _format_seconds(seconds: float) -> str:
    """Convert seconds to HH:MM:SS or MM:SS format."""
    total = int(seconds)
    hours = total // 3600
    minutes = (total % 3600) // 60
    secs = total % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"
