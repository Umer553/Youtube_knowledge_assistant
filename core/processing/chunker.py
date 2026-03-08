"""
Chunking Module — Timestamp-Aware Text Splitting
Splits video transcripts into chunks while preserving timestamp metadata.
Each chunk knows its start_time, end_time, and source video — enabling
clickable timestamp links in the chatbot's responses.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from dataclasses import dataclass
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

from core.ingestion.transcript import VideoTranscript, TranscriptSegment
from app.config import CHUNK_SIZE, CHUNK_OVERLAP, SEPARATORS


@dataclass
class TimestampedChunk:
    """A text chunk with timestamp and video metadata."""
    text: str
    video_id: str
    video_title: str
    start_time: float       # seconds
    end_time: float          # seconds
    chunk_index: int
    total_chunks: int

    @property
    def start_formatted(self) -> str:
        return _format_seconds(self.start_time)

    @property
    def end_formatted(self) -> str:
        return _format_seconds(self.end_time)

    @property
    def youtube_timestamp_url(self) -> str:
        """Generate a clickable YouTube URL that jumps to this chunk's timestamp."""
        t = int(self.start_time)
        return f"https://youtu.be/{self.video_id}?t={t}"

    def to_langchain_document(self) -> Document:
        """Convert to a LangChain Document with rich metadata for filtered retrieval."""
        return Document(
            page_content=self.text,
            metadata={
                'video_id': self.video_id,
                'video_title': self.video_title,
                'start_time': self.start_time,
                'end_time': self.end_time,
                'start_formatted': self.start_formatted,
                'end_formatted': self.end_formatted,
                'timestamp_url': self.youtube_timestamp_url,
                'chunk_index': self.chunk_index,
                'total_chunks': self.total_chunks,
                'source': f"{self.video_title} [{self.start_formatted}]",
            }
        )


def chunk_transcript(
    transcript: VideoTranscript,
    video_title: str = "",
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[TimestampedChunk]:
    """
    Split a VideoTranscript into timestamped chunks.
    
    Strategy:
    1. Group transcript segments into windows by time
    2. Concatenate text within each window
    3. Use RecursiveCharacterTextSplitter to split into chunks
    4. Map each chunk back to its approximate timestamp range
    
    This preserves the connection between text content and video position.
    
    Args:
        transcript: VideoTranscript with timestamped segments
        video_title: Title of the video (for metadata)
        chunk_size: Target chunk size in characters
        chunk_overlap: Overlap between chunks in characters
        
    Returns:
        List of TimestampedChunk objects
    """
    if not transcript or not transcript.segments:
        return []

    # Step 1: Build a mapping of character positions to timestamps
    # This lets us trace back from chunk text to its time range
    segments = transcript.segments
    position_map = []   # List of (char_start, char_end, segment)

    full_text_parts = []
    current_pos = 0

    for seg in segments:
        text = seg.text.strip()
        if not text:
            continue
        # Add space separator between segments
        if full_text_parts:
            current_pos += 1   # for the space
        
        start_pos = current_pos
        end_pos = current_pos + len(text)
        position_map.append((start_pos, end_pos, seg))
        full_text_parts.append(text)
        current_pos = end_pos

    full_text = " ".join(full_text_parts)

    if not full_text.strip():
        return []

    # Step 2: Split the full text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=SEPARATORS,
        length_function=len,
    )

    text_chunks = text_splitter.split_text(full_text)
    total_chunks = len(text_chunks)

    # Step 3: Map each chunk back to its timestamp range
    timestamped_chunks = []
    search_start = 0

    for idx, chunk_text in enumerate(text_chunks):
        # Find where this chunk starts in the full text
        chunk_start_pos = full_text.find(chunk_text, search_start)
        if chunk_start_pos == -1:
            chunk_start_pos = full_text.find(chunk_text)
        
        chunk_end_pos = chunk_start_pos + len(chunk_text) if chunk_start_pos >= 0 else 0

        # Find which segments overlap with this chunk's character range
        start_time = None
        end_time = None

        for seg_start, seg_end, seg in position_map:
            # Check if segment overlaps with chunk
            if seg_end > chunk_start_pos and seg_start < chunk_end_pos:
                if start_time is None:
                    start_time = seg.start
                end_time = seg.end

        # Fallback if mapping fails
        if start_time is None:
            start_time = 0.0
        if end_time is None:
            end_time = start_time + 30.0

        timestamped_chunks.append(TimestampedChunk(
            text=chunk_text,
            video_id=transcript.video_id,
            video_title=video_title or transcript.video_id,
            start_time=start_time,
            end_time=end_time,
            chunk_index=idx,
            total_chunks=total_chunks,
        ))

        # Move search forward (but allow overlap)
        if chunk_start_pos >= 0:
            search_start = max(search_start, chunk_start_pos + len(chunk_text) - chunk_overlap)

    return timestamped_chunks


def chunks_to_documents(chunks: list[TimestampedChunk]) -> list[Document]:
    """Convert a list of TimestampedChunks to LangChain Documents."""
    return [chunk.to_langchain_document() for chunk in chunks]


def chunk_multiple_transcripts(
    transcripts: dict[str, VideoTranscript],
    titles: dict[str, str] = None,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[TimestampedChunk]:
    """
    Chunk multiple video transcripts at once.
    
    Args:
        transcripts: Dict mapping video_id -> VideoTranscript
        titles: Dict mapping video_id -> video title
        
    Returns:
        Combined list of TimestampedChunks from all videos
    """
    if titles is None:
        titles = {}

    all_chunks = []
    for video_id, transcript in transcripts.items():
        if transcript is None:
            continue
        title = titles.get(video_id, video_id)
        chunks = chunk_transcript(transcript, title, chunk_size, chunk_overlap)
        all_chunks.extend(chunks)
        print(f"  Chunked '{title}': {len(chunks)} chunks")

    return all_chunks


def _format_seconds(seconds: float) -> str:
    """Convert seconds to HH:MM:SS or MM:SS format."""
    total = int(seconds)
    hours = total // 3600
    minutes = (total % 3600) // 60
    secs = total % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"
