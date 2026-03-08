<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/LangChain-RAG-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white" />
  <img src="https://img.shields.io/badge/Streamlit-Chat_UI-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" />
  <img src="https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?style=for-the-badge&logo=openai&logoColor=white" />
  <img src="https://img.shields.io/badge/ChromaDB-Vector_Store-FF6F00?style=for-the-badge" />
</p>

<h1 align="center">🎬 YouTube Knowledge Assistant</h1>

<p align="center">
  <b>Chat with any YouTube video — get timestamped answers, summaries, flashcards, and more.</b><br>
  A multi-video RAG chatbot built with LangChain, ChromaDB, and GPT-4o-mini.
</p>

<p align="center">
  <i>Final Year Project by Muhammad Saad</i>
</p>

---

## What It Does

Paste a YouTube video URL (or a full playlist) → the system extracts the transcript, chunks it with timestamps, embeds it into a vector database, and lets you **ask questions in natural language**. Every answer comes with a clickable timestamp link that jumps you to the exact moment in the video.

It goes beyond basic Q&A:

- **Ask questions** about the video content and get cited, timestamped answers
- **Summarize** entire videos or specific topics
- **Compare** information across multiple loaded videos
- **Generate flashcards & quizzes** for study/revision
- **See what viewers think** through comment sentiment analysis
- **Follow-up naturally** — conversation memory handles multi-turn chat

---

## How It Works

```
YouTube URL → Transcript Extraction → Timestamp-Aware Chunking → ChromaDB Embeddings
                                                                        ↓
User Question → Query Router → Intent Detection → Appropriate Chain → LLM (GPT-4o-mini)
                                                                        ↓
                                                          Timestamped Answer + Sources
```

**The pipeline in simple terms:**

1. You paste a YouTube URL (video, playlist, or channel)
2. The system fetches the transcript using YouTube's caption API (or Whisper if no captions exist)
3. The transcript is split into chunks — each chunk remembers its start and end timestamp
4. Chunks are embedded and stored in ChromaDB for semantic search
5. When you ask a question, the system retrieves the most relevant chunks
6. GPT-4o-mini generates an answer, citing the exact video timestamps
7. A smart router auto-detects whether you want Q&A, a summary, a comparison, flashcards, or a quiz

---

## Features

| Feature | Description |
|---|---|
| Multi-Video Support | Load single videos, entire playlists, or channel URLs |
| Timestamped Answers | Every answer links to the exact moment in the video |
| Smart Query Routing | Auto-detects intent — Q&A, summary, compare, quiz, sentiment |
| Cross-Video Comparison | Compare what different videos say about the same topic |
| Comment Sentiment Analysis | VADER + LLM-based theme clustering on viewer comments |
| Flashcard & Quiz Generation | Create study material directly from video content |
| Conversation Memory | Follow-up questions work naturally with context preservation |
| Whisper Fallback | Handles videos without captions via OpenAI Whisper |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit, streamlit-chat |
| Framework | LangChain (LCEL) |
| LLM | OpenAI GPT-4o-mini |
| Embeddings | text-embedding-3-small |
| Vector Store | ChromaDB |
| Metadata DB | SQLite |
| Transcripts | youtube-transcript-api, OpenAI Whisper |
| Comments | YouTube Data API v3 |
| Sentiment | VADER Sentiment Analysis |
| Deployment | Streamlit Cloud, Docker |

---

## Project Structure

```
youtube-knowledge-assistant/
│
├── app/
│   ├── main.py                  # Streamlit entry point
│   ├── config.py                # API keys, model settings, constants
│   └── components/              # UI components
│
├── core/
│   ├── ingestion/
│   │   ├── url_parser.py        # Resolves video / playlist / channel URLs
│   │   ├── transcript.py        # Transcript extraction (API + Whisper)
│   │   └── comments.py          # YouTube comment fetcher
│   │
│   ├── processing/
│   │   ├── chunker.py           # Timestamp-aware text splitting
│   │   ├── embedder.py          # Embedding pipeline
│   │   └── sentiment.py         # VADER + LLM comment analysis
│   │
│   ├── retrieval/
│   │   ├── vector_store.py      # ChromaDB wrapper
│   │   ├── retriever.py         # MultiQuery retriever + MMR
│   │   └── metadata_store.py    # SQLite for metadata & history
│   │
│   └── chains/
│       ├── router.py            # Query intent classification
│       ├── qa_chain.py          # Q&A with timestamped citations
│       ├── summary_chain.py     # Video summarization
│       ├── compare_chain.py     # Cross-video comparison
│       ├── sentiment_chain.py   # Comment-aware responses
│       └── formatter.py         # Flashcard & quiz generator
│
├── data/                        # ChromaDB + SQLite (auto-created)
├── tests/
├── .env.example
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- An OpenAI API key ([get one here](https://platform.openai.com/api-keys)) — $5 credit is more than enough
- A YouTube Data API v3 key ([get one here](https://console.cloud.google.com/apis/library/youtube.googleapis.com)) — free, optional but needed for comments

### Installation

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/youtube-knowledge-assistant.git
cd youtube-knowledge-assistant

# Create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up your API keys
cp .env.example .env
# Open .env and paste your OPENAI_API_KEY and YOUTUBE_API_KEY
```

### Run

```bash
streamlit run app/main.py
```

Open `http://localhost:8501` in your browser. Paste a YouTube URL in the sidebar, click **Process**, and start chatting.

### Docker (Alternative)

```bash
docker build -t youtube-assistant .
docker run -p 8501:8501 --env-file .env youtube-assistant
```

---

## Usage Examples

| What you ask | What happens |
|---|---|
| *"What is the main topic of this video?"* | Factual Q&A with timestamp links |
| *"Summarize this video"* | Structured summary with key points |
| *"Compare what both videos say about X"* | Side-by-side comparison |
| *"What do viewers think about this?"* | Comment sentiment + video content |
| *"Generate flashcards"* | Q&A pairs with timestamps |
| *"Create a 5-question quiz"* | MCQs with answer key |

---

## API Cost Estimate

This project is designed to be cheap to run:

| Model | Cost | Usage |
|---|---|---|
| GPT-4o-mini | $0.15 / 1M input tokens | LLM for Q&A, summaries, quizzes |
| text-embedding-3-small | $0.02 / 1M tokens | Vector embeddings |
| YouTube Data API v3 | Free (10,000 units/day) | Comments & metadata |

A typical session of 20 questions costs roughly **$0.01–0.03**. The $5 starting credit covers thousands of queries.

---

## License

This project was built as a Final Year Project for academic purposes.

---

## Author

**Umer Aftab**

---
