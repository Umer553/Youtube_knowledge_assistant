"""Quick end-to-end pipeline test — run from project root."""
import sys, os
sys.path.insert(0, ".")

print("=" * 55)
print("YouTube Knowledge Assistant — Pipeline Test")
print("=" * 55)

# ── 1. Config ──────────────────────────────────────────────
from app.config import (
    OPENAI_API_KEY, YOUTUBE_API_KEY, LLM_MODEL, EMBEDDING_MODEL,
    CHROMA_COLLECTION, CHUNK_SIZE, CHUNK_OVERLAP, RETRIEVER_K,
    LLM_TEMPERATURE, LLM_MAX_TOKENS,
)
assert OPENAI_API_KEY, "OPENAI_API_KEY is not set in .env"
print("\n[1/6] Config")
print(f"  LLM:        {LLM_MODEL}")
print(f"  Embeddings: {EMBEDDING_MODEL}")
print(f"  Collection: {CHROMA_COLLECTION}")
print(f"  OpenAI key: SET ({OPENAI_API_KEY[:8]}...)")
print(f"  YT key:     {'SET' if YOUTUBE_API_KEY else 'not set'}")

# ── 2. Transcript fetch ────────────────────────────────────
VIDEO_ID = "4hgOD8b56VM"
print(f"\n[2/6] Fetching transcript for {VIDEO_ID}...")
from core.ingestion.transcript import fetch_transcript
transcript = fetch_transcript(VIDEO_ID)
assert transcript and transcript.segments, "No transcript returned"
print(f"  OK — {len(transcript.segments)} segments, {transcript.total_duration:.0f}s")
print(f"  Sample: \"{transcript.segments[0].text[:80]}\"")

# ── 3. Chunking ────────────────────────────────────────────
print(f"\n[3/6] Chunking...")
from core.processing.chunker import chunk_transcript, chunks_to_documents
chunks = chunk_transcript(transcript, video_title="Test Video")
docs   = chunks_to_documents(chunks)
assert docs, "No chunks produced"
print(f"  OK — {len(docs)} chunks (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")

# ── 4. Embeddings ──────────────────────────────────────────
print(f"\n[4/6] Initialising embeddings ({EMBEDDING_MODEL})...")
from core.processing.embedder import get_embedding_model
emb = get_embedding_model(provider="openai", api_key=OPENAI_API_KEY, model_name=EMBEDDING_MODEL)
test_vec = emb.embed_query("What is this video about?")
print(f"  OK — vector dim: {len(test_vec)}")

# ── 5. Vector store ────────────────────────────────────────
print(f"\n[5/6] Storing chunks in ChromaDB ({CHROMA_COLLECTION})...")
import chromadb
from app.config import CHROMA_DIR
_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
try:
    _client.delete_collection(CHROMA_COLLECTION)
    print(f"  Dropped stale collection '{CHROMA_COLLECTION}'")
except Exception:
    pass  # collection didn't exist yet

from core.retrieval.vector_store import VectorStoreManager
vs = VectorStoreManager(embedding_model=emb, collection_name=CHROMA_COLLECTION)
vs.add_documents(docs)
print(f"  OK — {len(docs)} docs indexed")

# ── 6. LLM + retrieval ─────────────────────────────────────
print(f"\n[6/6] Running QA with {LLM_MODEL}...")
from langchain_openai import ChatOpenAI
from core.retrieval.retriever import get_multi_query_retriever
from core.chains.qa_chain import run_qa

llm       = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE,
                       openai_api_key=OPENAI_API_KEY, max_tokens=LLM_MAX_TOKENS)
retriever = get_multi_query_retriever(vs, llm, search_type="mmr", k=RETRIEVER_K)
result    = run_qa(llm, retriever, "Give me a brief summary of what this video covers.", "")
answer    = result.get("answer", "")
assert answer, "No answer returned"
print(f"  OK — answer ({len(answer)} chars):")
print()
print(answer[:500])

print("\n" + "=" * 55)
print("All 6 steps passed. Pipeline is working correctly.")
print("=" * 55)
