"""
Configuration settings for YouTube Knowledge Assistant.
Loads environment variables and defines constants used across the app.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env ──────────────────────────────────────────────
load_dotenv()

# ── API Keys ───────────────────────────────────────────────
OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY", "")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")

# ── Paths ──────────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parent.parent
DATA_DIR    = BASE_DIR / "data"
CHROMA_DIR  = DATA_DIR / "chroma_db"
SQLITE_PATH = DATA_DIR / "metadata.db"
PROMPTS_DIR = BASE_DIR / "prompts"

# Ensure data directories exist
DATA_DIR.mkdir(exist_ok=True)
CHROMA_DIR.mkdir(exist_ok=True)

# ── LLM Settings ──────────────────────────────────────────
LLM_MODEL                = "gpt-4o-mini"
LLM_TEMPERATURE          = 0.7
LLM_TEMPERATURE_CREATIVE = 0.9
LLM_MAX_TOKENS           = 2048

# ── Embedding Settings ─────────────────────────────────────
EMBEDDING_MODEL      = "text-embedding-3-small"
CHROMA_COLLECTION    = "youtube_transcripts"

# ── Chunking Settings ──────────────────────────────────────
CHUNK_SIZE    = 1500
CHUNK_OVERLAP = 200
SEPARATORS    = ["\n\n", "\n", ". ", " ", ""]

# ── Retrieval Settings ─────────────────────────────────────
RETRIEVER_K       = 6
RETRIEVER_FETCH_K = 20
MMR_LAMBDA        = 0.75
MULTI_QUERY_COUNT = 3

# ── Comment Settings ───────────────────────────────────────
MAX_COMMENTS_PER_VIDEO = 100
SENTIMENT_THEMES_COUNT = 5

# ── Conversation Memory ────────────────────────────────────
MEMORY_WINDOW_SIZE = 10

# ── Query Intent Types ─────────────────────────────────────
INTENT_TYPES = [
    "factual_qa",
    "summarize",
    "compare_videos",
    "sentiment_query",
    "generate_quiz",
    "generate_flashcards",
]
