# 🎬 YouTube Knowledge Assistant

A multi-video, multimodal RAG chatbot that lets you **chat with YouTube videos** — powered by LangChain, ChromaDB, and GPT-4o-mini.

> **Final Year Project** — Goes beyond basic YouTube Q&A with cross-video comparison, timestamped answers, comment sentiment analysis, and smart output formatting.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Multi-Video Ingestion** | Load single videos, playlists, or entire channels |
| **Timestamped Answers** | Every answer links back to the exact moment in the video |
| **Cross-Video Comparison** | Compare perspectives across multiple videos |
| **Comment Sentiment Analysis** | Understand what viewers think using VADER + LLM clustering |
| **Smart Query Routing** | Auto-detects if you're asking a question, requesting a summary, or comparing |
| **Multiple Output Formats** | Summaries, study notes, flashcards, quizzes — all from video content |
| **Conversation Memory** | Follow-up questions work naturally with context preservation |

---

## 🏗️ Architecture

```
User → Streamlit UI
         ↓
    URL Parser (video/playlist/channel)
         ↓
    ┌─────────────────┬──────────────────┐
    │ Transcript Engine │  Comment Fetcher │
    │ (YT API/Whisper) │  (YT Data API)   │
    └────────┬────────┘──────┬───────────┘
             ↓               ↓
    Timestamp-Aware      Sentiment Analysis
    Chunker              (VADER + LLM)
             ↓               ↓
    ChromaDB             SQLite
    (Vector Store)       (Metadata Store)
             ↓               ↓
    ┌────────┴───────────────┴──────────┐
    │        Query Router (LLM)          │
    │  factual_qa | summarize | compare  │
    │  sentiment | quiz | flashcards     │
    └────────────────┬──────────────────┘
                     ↓
              LLM Response + Sources
              + Timestamp Links
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- OpenAI API key (for GPT-4o-mini + embeddings)
- YouTube Data API v3 key (optional, for comments)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/youtube-knowledge-assistant.git
cd youtube-knowledge-assistant

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env and add your API keys
```

### Run the App

```bash
streamlit run app/main.py
```

The app will open at `http://localhost:8501`

### Docker (Alternative)

```bash
docker build -t youtube-assistant .
docker run -p 8501:8501 --env-file .env youtube-assistant
```

---

## 📖 Usage

1. **Add API Keys** — Enter your OpenAI and YouTube API keys in the sidebar
2. **Paste a URL** — Any YouTube video, playlist, or channel URL
3. **Click Process** — The system extracts transcripts, chunks them, and indexes everything
4. **Start Chatting** — Ask questions, request summaries, or generate study materials
5. **Choose Format** — Use the dropdown to get flashcards, quizzes, or comparisons

### Example Queries

| Query | What Happens |
|-------|-------------|
| "What is the main topic?" | Factual Q&A with timestamp sources |
| "Summarize this video" | Structured summary with section timestamps |
| "Compare what both videos say about X" | Side-by-side comparison from multiple videos |
| "What do viewers think?" | Comment sentiment analysis integrated with content |
| "Generate flashcards" | Q&A flashcard pairs from video content |
| "Create a quiz" | MCQ quiz with answer key and explanations |

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Streamlit | Chat UI with video previews |
| Orchestration | LangChain (LCEL) | RAG pipeline, chains, routing |
| LLM | GPT-4o-mini | Generation, classification, analysis |
| Embeddings | text-embedding-3-small | Semantic search |
| Vector Store | ChromaDB | Transcript embeddings + metadata |
| Metadata DB | SQLite | Video info, sentiment, chat history |
| Transcripts | youtube-transcript-api + Whisper | Caption extraction |
| Comments | YouTube Data API v3 | Comment fetching |
| Sentiment | VADER + LLM | Comment polarity + theme clustering |

---

## 📁 Project Structure

```
youtube-knowledge-assistant/
├── app/
│   ├── main.py                 # Streamlit entry point
│   ├── config.py               # Settings & constants
│   └── components/             # UI components
├── core/
│   ├── ingestion/
│   │   ├── url_parser.py       # URL resolution
│   │   ├── transcript.py       # Transcript extraction
│   │   └── comments.py         # Comment fetching
│   ├── processing/
│   │   ├── chunker.py          # Timestamp-aware splitting
│   │   ├── embedder.py         # Embedding pipeline
│   │   └── sentiment.py        # Sentiment analysis
│   ├── retrieval/
│   │   ├── vector_store.py     # ChromaDB wrapper
│   │   ├── retriever.py        # Multi-query retriever
│   │   └── metadata_store.py   # SQLite operations
│   └── chains/
│       ├── router.py           # Query intent classification
│       ├── qa_chain.py         # Q&A with sources
│       ├── summary_chain.py    # Summarization
│       ├── compare_chain.py    # Cross-video comparison
│       ├── sentiment_chain.py  # Comment-aware responses
│       └── formatter.py        # Flashcards, quizzes
├── data/                       # ChromaDB + SQLite storage
├── tests/
├── .env.example
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## 📊 Evaluation Metrics (For FYP Report)

- **Retrieval Accuracy**: Measure if the correct video segments are retrieved (Precision@K, Recall@K)
- **Answer Quality**: Human evaluation of factual correctness and completeness
- **Timestamp Accuracy**: Whether cited timestamps actually contain the referenced content
- **Sentiment Accuracy**: Compare VADER results with manual annotation on a sample
- **Response Latency**: End-to-end time from query to response
- **Chunk Size Analysis**: Compare different chunk sizes and overlaps on retrieval quality

---

## 📄 License

This project is built for educational purposes as a Final Year Project.

---

## 🙏 Acknowledgments

- [LangChain](https://langchain.com) — RAG framework
- [ChromaDB](https://trychroma.com) — Vector database
- [OpenAI](https://openai.com) — LLM and embeddings
- [Streamlit](https://streamlit.io) — Frontend framework
- [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) — Transcript extraction
