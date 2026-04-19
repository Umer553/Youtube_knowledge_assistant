# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

```bash
# Install dependencies (requires Python 3.10+)
pip install -r requirements.txt

# Copy and fill in environment variables
cp .env.example .env

# Run Streamlit app
streamlit run app/main.py
```

App runs at `http://localhost:8501`. API keys can also be entered at runtime in the sidebar.

**Docker:**
```bash
docker build -t youtube-assistant .
docker run -p 8501:8501 --env-file .env youtube-assistant
```

**Tests:**
```bash
pytest tests/
```

## Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Claude (claude-sonnet-4-6) LLM |
| `YOUTUBE_API_KEY` | No | Comment fetching and video metadata |
| `LANGCHAIN_API_KEY` | No | LangSmith tracing |

## Architecture

This is a multi-video RAG (Retrieval-Augmented Generation) chatbot. The data flow on video ingestion:

1. **`core/ingestion/url_parser.py`** — Resolves any YouTube URL (video/playlist/channel) into a list of `VideoInfo` objects with metadata
2. **`core/ingestion/transcript.py`** — Fetches captions via `youtube-transcript-api`, falls back to Whisper
3. **`core/processing/chunker.py`** — Splits transcripts into timestamp-aware chunks preserving `start_time`/`end_time` per chunk
4. **`core/processing/embedder.py`** — Creates `text-embedding-3-small` embeddings
5. **`core/retrieval/vector_store.py`** — Persists chunks to ChromaDB at `data/chroma_db/` with video metadata filters
6. **`core/retrieval/metadata_store.py`** — Stores video info, sentiment results, and chat history in SQLite at `data/metadata.db`

On each user query:

1. **`core/chains/router.py`** — LLM classifies intent into: `factual_qa`, `summarize`, `compare_videos`, `sentiment_query`, `generate_quiz`, `generate_flashcards`
2. The appropriate chain runs:
   - `qa_chain.py` — retrieves top-k chunks, answers with timestamp sources
   - `summary_chain.py` — retrieves broadly, produces structured summary
   - `compare_chain.py` — runs per-video retrieval then synthesizes differences
   - `sentiment_chain.py` — merges VADER/LLM-clustered comment data with content retrieval
   - `formatter.py` — generates flashcards or MCQ quizzes from retrieved content
3. **`core/retrieval/retriever.py`** — Multi-query MMR retriever (generates 3 query variations, re-ranks with MMR for diversity)

## Key Config (`app/config.py`)

All tunable constants live here: chunk size (1000 chars, 150 overlap), retriever K (5), MMR lambda (0.7), LLM model (`gpt-4o-mini`), and intent type list. Changing these affects retrieval quality and cost.

## Streamlit Session State

`app/main.py` stores all runtime objects in `st.session_state`: `llm`, `embeddings`, `vector_store`, `metadata_store`, `retriever`, `loaded_videos` (dict of `video_id → info`), and `messages`. LLM/embeddings/stores are `@st.cache_resource`-decorated to survive reruns.

Comment sentiment is optional — only runs when `YOUTUBE_API_KEY` is present. Sentiment data is stored per `video_id` in SQLite and merged into responses by `sentiment_chain.py`.
