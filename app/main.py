"""
YouTube Knowledge Assistant — Streamlit Application
Run with: streamlit run app/main.py  (from project root)
"""

import streamlit as st
import sys
import os
import uuid
import traceback

# ── Path fix: ensure project root is on sys.path ───────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ── Safe config import ─────────────────────────────────────
try:
    from app.config import (
        OPENAI_API_KEY, YOUTUBE_API_KEY,
        LLM_MODEL, EMBEDDING_MODEL, CHROMA_COLLECTION,
        LLM_TEMPERATURE, LLM_MAX_TOKENS,
        RETRIEVER_K, MEMORY_WINDOW_SIZE,
    )
except Exception as _cfg_err:
    OPENAI_API_KEY     = os.getenv("OPENAI_API_KEY", "")
    YOUTUBE_API_KEY    = os.getenv("YOUTUBE_API_KEY", "")
    LLM_MODEL          = "gpt-4o-mini"
    EMBEDDING_MODEL    = "text-embedding-3-small"
    CHROMA_COLLECTION  = "youtube_transcripts"
    LLM_TEMPERATURE    = 0.3
    LLM_MAX_TOKENS     = 2048
    RETRIEVER_K        = 6
    MEMORY_WINDOW_SIZE = 10
    st.warning(f"⚠️ Config load failed ({_cfg_err}). Using defaults.")

# ── Safe CSS import ────────────────────────────────────────
_CSS = ""
try:
    from app.components.styles import get_css
    _CSS = get_css()
except Exception:
    pass  # No CSS is better than a broken app

# ── Page config (must come before any other st.* call) ─────
st.set_page_config(
    page_title="YT Knowledge Assistant",
    page_icon="▶",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject CSS only if it loaded successfully
if _CSS:
    st.markdown(_CSS, unsafe_allow_html=True)


# ── Session state ──────────────────────────────────────────
def _init_session():
    defaults = {
        "session_id":        str(uuid.uuid4()),
        "messages":          [],
        "loaded_videos":     {},
        "vector_store":      None,
        "metadata_store":    None,
        "llm":               None,
        "embeddings":        None,
        "retriever":         None,
        "chat_history_text": "",
        "output_format":     "Auto",
        # Track runtime API keys so user can override config values in-session
        "runtime_openai_key": OPENAI_API_KEY,
        "runtime_yt_key":     YOUTUBE_API_KEY,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_session()


# ── Cached resource initialisers ───────────────────────────
@st.cache_resource
def init_llm(api_key: str):
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        openai_api_key=api_key,
        max_tokens=LLM_MAX_TOKENS,
    )

@st.cache_resource
def init_embeddings(api_key: str):
    from core.processing.embedder import get_embedding_model
    return get_embedding_model(provider="openai", api_key=api_key, model_name=EMBEDDING_MODEL)

@st.cache_resource
def init_stores(_emb):
    from core.retrieval.vector_store import VectorStoreManager
    from core.retrieval.metadata_store import MetadataStore
    return VectorStoreManager(embedding_model=_emb, collection_name=CHROMA_COLLECTION), MetadataStore()


# ── Constants ──────────────────────────────────────────────
INTENT_META = {
    "factual_qa":          ("Q&A",        "intent-qa"),
    "summarize":           ("Summary",    "intent-summarize"),
    "compare_videos":      ("Compare",    "intent-compare"),
    "sentiment_query":     ("Sentiment",  "intent-sentiment"),
    "generate_flashcards": ("Flashcards", "intent-flashcards"),
    "generate_quiz":       ("Quiz",       "intent-quiz"),
}

FORMAT_OPTIONS = {
    "Auto":           "Auto — let the AI decide",
    "Detailed Answer": "Detailed Q&A answer",
    "Summary":        "Structured summary",
    "Study Notes":    "Study notes",
    "Flashcards":     "Flashcard set",
    "Quiz":           "Multiple-choice quiz",
    "Compare Videos": "Cross-video comparison",
}

FORMAT_TO_INTENT = {
    "Detailed Answer": "factual_qa",
    "Summary":         "summarize",
    "Study Notes":     "summarize",
    "Flashcards":      "generate_flashcards",
    "Quiz":            "generate_quiz",
    "Compare Videos":  "compare_videos",
}


def total_chunks() -> int:
    return sum(v.get("chunks", 0) for v in st.session_state.loaded_videos.values())


# ══════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════
with st.sidebar:

    # ── Brand ──────────────────────────────────────────────
    st.markdown("""
    <div class="sb-logo">
        <div class="sb-logo-icon">▶</div>
        <div>
            <p class="sb-logo-title">YT Knowledge</p>
            <p class="sb-logo-sub">openai · rag · chromadb</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── API Keys ───────────────────────────────────────────
    st.markdown('<div class="sb-section-label">🔑 API Keys</div>', unsafe_allow_html=True)

    if st.session_state.runtime_openai_key:
        st.markdown(
            '<div class="api-status ok">⬤ OpenAI ready</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="api-status warn">⚠ OpenAI key missing</div>',
            unsafe_allow_html=True,
        )

    if st.session_state.runtime_yt_key:
        st.markdown(
            '<div class="api-status ok" style="margin-top:5px">⬤ YouTube key loaded</div>',
            unsafe_allow_html=True,
        )

    with st.expander("Change keys", expanded=False):
        new_openai = st.text_input(
            "OpenAI API Key",
            value=st.session_state.runtime_openai_key,
            type="password",
            placeholder="sk-...",
            key="input_openai_key",
        )
        new_yt = st.text_input(
            "YouTube Data Key",
            value=st.session_state.runtime_yt_key,
            type="password",
            placeholder="AIza... (optional)",
            key="input_yt_key",
        )
        if st.button("💾 Save Keys", use_container_width=True):
            st.session_state.runtime_openai_key = new_openai.strip()
            st.session_state.runtime_yt_key     = new_yt.strip()
            st.rerun()

    st.divider()

    # ── Add Video ──────────────────────────────────────────
    st.markdown('<div class="sb-section-label">▶ Add Video</div>', unsafe_allow_html=True)
    url_input = st.text_input(
        "YouTube URL",
        placeholder="youtube.com/watch?v=...  or  playlist...",
        label_visibility="visible",
        key="url_input",
    )
    _can_process = url_input.strip() and bool(st.session_state.runtime_openai_key)
    process_btn = st.button(
        "▶  Process Video",
        type="primary",
        use_container_width=True,
        disabled=not _can_process,
    )

    st.divider()

    # ── Loaded videos (compact) ────────────────────────────
    if st.session_state.loaded_videos:
        n_vids  = len(st.session_state.loaded_videos)
        n_chunks = sum(v.get("chunks", 0) for v in st.session_state.loaded_videos.values())
        st.markdown(f"""
        <div class="sb-status-row">
            <span class="sb-status-dot"></span>
            <span class="sb-status-text">{n_vids} video{"s" if n_vids != 1 else ""} · {n_chunks} chunks indexed</span>
        </div>
        """, unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Clear All", type="secondary", use_container_width=True):
                if st.session_state.vector_store:
                    try:
                        st.session_state.vector_store.clear_all()
                    except Exception:
                        pass
                st.session_state.loaded_videos     = {}
                st.session_state.messages          = []
                st.session_state.chat_history_text = ""
                st.rerun()
        with col_b:
            if st.session_state.messages:
                if st.button("Clear Chat", type="secondary", use_container_width=True):
                    st.session_state.messages          = []
                    st.session_state.chat_history_text = ""
                    st.rerun()

        st.divider()

    # ── Response Format ────────────────────────────────────
    st.markdown('<div class="sb-section-label">🎛 Format</div>', unsafe_allow_html=True)
    fmt_keys   = list(FORMAT_OPTIONS.keys())
    fmt_labels = list(FORMAT_OPTIONS.values())

    # BUG FIX: guard against output_format being an invalid key after code changes
    cur_fmt = st.session_state.output_format
    cur_idx = fmt_keys.index(cur_fmt) if cur_fmt in fmt_keys else 0

    chosen_label = st.radio(
        "format",
        options=fmt_labels,
        index=cur_idx,
        label_visibility="collapsed",
    )
    chosen_key = fmt_keys[fmt_labels.index(chosen_label)]
    if chosen_key != st.session_state.output_format:
        st.session_state.output_format = chosen_key
        st.rerun()

    st.divider()

    # ── Tech Stack ─────────────────────────────────────────
    st.markdown('<div class="sb-section-label">⚙ Stack</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="model-info-card">
        <div class="model-row">
            <span class="model-label">LLM</span>
            <span class="model-value">{LLM_MODEL}</span>
        </div>
        <div class="model-row">
            <span class="model-label">Embeddings</span>
            <span class="model-value">{EMBEDDING_MODEL}</span>
        </div>
        <div class="model-row">
            <span class="model-label">Vector DB</span>
            <span class="model-value">ChromaDB</span>
        </div>
        <div class="model-row">
            <span class="model-label">Retrieval</span>
            <span class="model-value">MMR · K={RETRIEVER_K}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# MAIN AREA — Header + Stats
# ══════════════════════════════════════════════════════════
st.markdown("""
<div class="page-header">
    <div class="page-header-left">
        <h1 class="page-title">YouTube <span class="hl">Knowledge</span> Assistant</h1>
        <p class="page-sub">RAG · Multi-Video · Timestamped Answers</p>
    </div>
</div>
""", unsafe_allow_html=True)

vcount = len(st.session_state.loaded_videos)
ccount = total_chunks()
mcount = len(st.session_state.messages) // 2
fmt    = st.session_state.output_format

st.markdown(f"""
<div class="stats-strip">
    <div class="stat-item">
        <div class="stat-dot amber"></div>
        <div class="stat-text">
            <span class="stat-number">{vcount}</span>
            <span class="stat-desc">Videos</span>
        </div>
    </div>
    <div class="stat-item">
        <div class="stat-dot teal"></div>
        <div class="stat-text">
            <span class="stat-number">{ccount}</span>
            <span class="stat-desc">Chunks</span>
        </div>
    </div>
    <div class="stat-item">
        <div class="stat-dot sky"></div>
        <div class="stat-text">
            <span class="stat-number">{mcount}</span>
            <span class="stat-desc">Exchanges</span>
        </div>
    </div>
    <div class="stat-item">
        <div class="stat-dot emerald"></div>
        <div class="stat-text">
            <span class="stat-number-sm">{fmt}</span>
            <span class="stat-desc">Format</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Loaded video pills (main area) ─────────────────────
if st.session_state.loaded_videos:
    _pill_parts = []
    for vid, info in st.session_state.loaded_videos.items():
        _t = info.get("title", vid)
        _pill_parts.append(f'<span class="video-pill" title="{_t}">{_t[:40]}</span>')
    st.markdown(
        f'<div class="video-pills-row">{"".join(_pill_parts)}</div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════
# VIDEO PROCESSING
# ══════════════════════════════════════════════════════════
if process_btn and url_input.strip():
    _openai_key = st.session_state.runtime_openai_key
    yt_key      = st.session_state.runtime_yt_key

    if not _openai_key:
        st.error("OpenAI API key is required. Add it to your .env file or expand 'Change keys' in the sidebar.")
        st.stop()

    with st.status("Processing video…", expanded=True) as status:
        try:
            st.write("Initialising OpenAI models…")
            llm        = init_llm(_openai_key)
            embeddings = init_embeddings(_openai_key)
            vector_store, metadata_store = init_stores(embeddings)
            st.session_state.llm            = llm
            st.session_state.vector_store   = vector_store
            st.session_state.metadata_store = metadata_store

            st.write("Resolving URL…")
            from core.ingestion.url_parser import resolve_video_ids
            videos = resolve_video_ids(url_input.strip(), yt_key)
            if not videos:
                st.error("Could not resolve any videos from that URL. Check the URL and try again.")
                status.update(label="Failed — no videos found.", state="error")
                st.stop()

            processed = 0
            for video_info in videos:
                vid = video_info.video_id
                st.write(f"Fetching transcript: **{video_info.title or vid}**")

                from core.ingestion.transcript import fetch_transcript
                transcript = fetch_transcript(vid)
                if not transcript:
                    st.warning(f"No transcript available for `{vid}` — skipping.")
                    continue

                st.write("Chunking & embedding…")
                from core.processing.chunker import chunk_transcript, chunks_to_documents
                title     = video_info.title or vid
                chunks    = chunk_transcript(transcript, video_title=title)
                if not chunks:
                    st.warning(f"No chunks produced for `{vid}` — skipping.")
                    continue
                documents = chunks_to_documents(chunks)

                st.write("Saving to vector store…")
                vector_store.add_documents(documents)
                metadata_store.save_video(
                    video_id=vid,
                    title=title,
                    channel=video_info.channel,
                    duration=video_info.duration,
                    thumbnail_url=video_info.thumbnail_url,
                    transcript_source=transcript.source,
                    chunk_count=len(chunks),
                )

                # Optional: comment sentiment (requires YT key)
                if yt_key:
                    st.write("Analysing comments & sentiment…")
                    try:
                        from core.ingestion.comments import fetch_comments
                        from core.processing.sentiment import run_full_analysis
                        comments = fetch_comments(vid, yt_key)
                        if comments:
                            sentiment = run_full_analysis(vid, comments, llm)
                            metadata_store.save_sentiment(vid, sentiment)
                    except Exception as _sent_err:
                        st.warning(f"Sentiment analysis skipped: {_sent_err}")

                st.session_state.loaded_videos[vid] = {
                    "title":     title,
                    "thumbnail": video_info.thumbnail_url,
                    "chunks":    len(chunks),
                    "channel":   video_info.channel or "",
                }
                processed += 1

            if processed == 0:
                status.update(label="No videos could be processed.", state="error")
                st.stop()

            st.write("Building retriever…")
            from core.retrieval.retriever import get_multi_query_retriever
            st.session_state.retriever = get_multi_query_retriever(
                vector_store, llm, search_type="mmr", k=RETRIEVER_K,
            )

            status.update(
                label=f"✅ Done — {processed} video(s) indexed. Start chatting!",
                state="complete",
            )
            st.rerun()

        except Exception as e:
            status.update(label="Processing failed.", state="error")
            st.error(f"Error: {e}")
            st.code(traceback.format_exc())


# ══════════════════════════════════════════════════════════
# WELCOME SCREEN  (shown when no videos loaded)
# ══════════════════════════════════════════════════════════
if not st.session_state.loaded_videos:
    st.markdown("""
    <div class="welcome-wrap">
        <div class="welcome-title">No videos loaded yet</div>
        <div class="welcome-sub">
            Paste a YouTube URL in the sidebar and click
            <strong style="color:#f59e0b">▶ Process Video</strong>.<br>
            Supports individual videos, playlists, and channels.
        </div>
        <div class="feature-grid">
            <div class="feature-card">
                <span class="fc-icon">⏱</span>
                <div class="fc-title">Timestamped Answers</div>
                <div class="fc-desc">Every answer links back to the exact moment in the video.</div>
            </div>
            <div class="feature-card">
                <span class="fc-icon">⚖️</span>
                <div class="fc-title">Cross-Video Compare</div>
                <div class="fc-desc">Load multiple videos and ask comparative questions.</div>
            </div>
            <div class="feature-card">
                <span class="fc-icon">❤️</span>
                <div class="fc-title">Sentiment Analysis</div>
                <div class="fc-desc">Understand how the community reacted to the content.</div>
            </div>
            <div class="feature-card">
                <span class="fc-icon">🎴</span>
                <div class="fc-title">Flashcards</div>
                <div class="fc-desc">Auto-generate study flashcards from video content.</div>
            </div>
            <div class="feature-card">
                <span class="fc-icon">🧩</span>
                <div class="fc-title">Quizzes</div>
                <div class="fc-desc">Test your knowledge with AI-generated MCQ quizzes.</div>
            </div>
            <div class="feature-card">
                <span class="fc-icon">🧠</span>
                <div class="fc-title">Memory</div>
                <div class="fc-desc">Conversational context persists across follow-up questions.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    # ── Chat history ───────────────────────────────────────
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            intent = msg.get("intent", "")
            badge_label, badge_cls = INTENT_META.get(intent, ("", ""))
            with st.chat_message("assistant"):
                if badge_label:
                    st.markdown(
                        f'<span class="intent-badge {badge_cls}">{badge_label}</span>',
                        unsafe_allow_html=True,
                    )
                st.markdown(msg["content"])


# ══════════════════════════════════════════════════════════
# CHAT INPUT
# ══════════════════════════════════════════════════════════
prompt = st.chat_input(
    "Ask anything about the video(s)…",
    disabled=not st.session_state.loaded_videos,
)

if prompt and st.session_state.loaded_videos:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            try:
                llm          = st.session_state.llm
                retriever    = st.session_state.retriever
                vs           = st.session_state.vector_store
                ms           = st.session_state.metadata_store
                video_ids    = list(st.session_state.loaded_videos.keys())
                video_titles = {v: i["title"] for v, i in st.session_state.loaded_videos.items()}
                titles_str   = ", ".join(video_titles.values())
                fmt          = st.session_state.output_format

                # BUG FIX: guard against llm/retriever being None if page was
                # refreshed after videos were indexed in a previous session
                if llm is None or retriever is None:
                    st.error(
                        "Session expired — please re-process the video(s) using the sidebar."
                    )
                    st.stop()

                # ── Intent routing ──────────────────────────────
                if fmt == "Auto":
                    from core.chains.router import classify_intent
                    intent = classify_intent(llm, prompt, len(video_ids), titles_str)
                else:
                    intent = FORMAT_TO_INTENT.get(fmt, "factual_qa")

                # ── Chain execution ─────────────────────────────
                if intent == "factual_qa":
                    from core.chains.qa_chain import run_qa
                    result   = run_qa(llm, retriever, prompt, st.session_state.chat_history_text)
                    response = result["answer"]

                elif intent == "summarize":
                    from core.chains.summary_chain import run_summary
                    style    = "study_notes" if fmt == "Study Notes" else "detailed"
                    response = run_summary(llm, retriever, style=style)

                elif intent == "compare_videos":
                    from core.chains.compare_chain import run_comparison
                    if len(video_ids) < 2:
                        response = (
                            "I need at least **2 videos** loaded to compare. "
                            "Add another video using the sidebar."
                        )
                    else:
                        response = run_comparison(llm, vs, prompt, video_ids, video_titles)

                elif intent == "sentiment_query":
                    from core.chains.sentiment_chain import run_sentiment_query
                    sentiment_data = {}
                    for v in video_ids:
                        s = ms.get_sentiment(v)
                        if s:
                            sentiment_data = s
                            break
                    if not sentiment_data:
                        response = (
                            "No sentiment data available. Make sure you provided a YouTube "
                            "API key before processing the video."
                        )
                    else:
                        response = run_sentiment_query(llm, retriever, prompt, sentiment_data)

                elif intent == "generate_flashcards":
                    from core.chains.formatter import generate_flashcards, format_flashcards_markdown
                    cards    = generate_flashcards(llm, retriever, topic=prompt)
                    response = format_flashcards_markdown(cards)

                elif intent == "generate_quiz":
                    from core.chains.formatter import generate_quiz, format_quiz_markdown
                    quiz     = generate_quiz(llm, retriever, topic=prompt)
                    response = format_quiz_markdown(quiz)

                else:
                    # Fallback — always safe to run QA
                    from core.chains.qa_chain import run_qa
                    result   = run_qa(llm, retriever, prompt, st.session_state.chat_history_text)
                    response = result["answer"]

                # ── Display response ────────────────────────────
                badge_label, badge_cls = INTENT_META.get(intent, ("", ""))
                if badge_label:
                    st.markdown(
                        f'<span class="intent-badge {badge_cls}">{badge_label}</span>',
                        unsafe_allow_html=True,
                    )
                st.markdown(response)

                # ── Persist to session state ────────────────────
                st.session_state.messages.append({
                    "role":    "assistant",
                    "content": response,
                    "intent":  intent,
                })

                # Sliding memory window
                recent = st.session_state.messages[-(MEMORY_WINDOW_SIZE * 2):]
                st.session_state.chat_history_text = "\n".join(
                    f"{'Human' if m['role'] == 'user' else 'Assistant'}: {m['content'][:200]}"
                    for m in recent
                )

                # Persist chat to metadata store (best-effort)
                if ms:
                    try:
                        ms.save_chat_message(st.session_state.session_id, "user", prompt)
                        ms.save_chat_message(
                            st.session_state.session_id, "assistant", response[:500]
                        )
                    except Exception:
                        pass  # Non-critical — don't surface to user

            except Exception as e:
                st.error(f"Error generating response: {e}")
                st.code(traceback.format_exc())


# ══════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════
st.markdown("""
<div class="app-footer">
    youtube knowledge assistant &nbsp;·&nbsp;
    <span class="hl-a">openai</span> &nbsp;·&nbsp;
    <span class="hl-t">langchain</span> &nbsp;·&nbsp;
    <span class="hl-s">chromadb</span> &nbsp;·&nbsp;
    <span class="hl-e">streamlit</span>
</div>
""", unsafe_allow_html=True)