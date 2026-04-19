"""
YouTube Knowledge Assistant — Streamlit Application
Run with: streamlit run app/main.py
"""

import streamlit as st
import sys
import os
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.config import (
    ANTHROPIC_API_KEY, YOUTUBE_API_KEY, LLM_MODEL,
    LLM_TEMPERATURE, RETRIEVER_K, MEMORY_WINDOW_SIZE,
)
from app.components.styles import get_css

# ── Page config ────────────────────────────────────────────
st.set_page_config(
    page_title="YT Knowledge Assistant",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(get_css(), unsafe_allow_html=True)


# ── Session state ──────────────────────────────────────────
def _init():
    defaults = {
        'session_id': str(uuid.uuid4()),
        'messages': [],
        'loaded_videos': {},
        'vector_store': None,
        'metadata_store': None,
        'llm': None,
        'embeddings': None,
        'retriever': None,
        'chat_history_text': "",
        'output_format': "Auto",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()


# ── Cached initialisers ────────────────────────────────────
@st.cache_resource
def init_llm(api_key: str):
    from langchain_anthropic import ChatAnthropic
    return ChatAnthropic(model=LLM_MODEL, temperature=LLM_TEMPERATURE,
                         anthropic_api_key=api_key)

@st.cache_resource
def init_embeddings():
    from core.processing.embedder import get_embedding_model
    return get_embedding_model(provider="huggingface")

@st.cache_resource
def init_stores(_emb):
    from core.retrieval.vector_store import VectorStoreManager
    from core.retrieval.metadata_store import MetadataStore
    return VectorStoreManager(embedding_model=_emb), MetadataStore()


# ── Helpers ────────────────────────────────────────────────
INTENT_META = {
    "factual_qa":        ("◈ Q&A",        "intent-qa"),
    "summarize":         ("◈ Summary",     "intent-summarize"),
    "compare_videos":    ("◈ Compare",     "intent-compare"),
    "sentiment_query":   ("◈ Sentiment",   "intent-sentiment"),
    "generate_flashcards": ("◈ Flashcards","intent-flashcards"),
    "generate_quiz":     ("◈ Quiz",        "intent-quiz"),
}

FORMAT_OPTIONS = [
    ("✦ Auto",       "Auto"),
    ("◈ Q&A",        "Detailed Answer"),
    ("◗ Summary",    "Summary"),
    ("✎ Notes",      "Study Notes"),
    ("⬡ Flashcards", "Flashcards"),
    ("◎ Quiz",       "Quiz"),
    ("⇔ Compare",    "Compare Videos"),
]

FORMAT_TO_INTENT = {
    "Detailed Answer": "factual_qa",
    "Summary":         "summarize",
    "Study Notes":     "summarize",
    "Flashcards":      "generate_flashcards",
    "Quiz":            "generate_quiz",
    "Compare Videos":  "compare_videos",
}


def total_chunks():
    return sum(v.get('chunks', 0) for v in st.session_state.loaded_videos.values())


# ── Sidebar ────────────────────────────────────────────────
with st.sidebar:

    # Logo
    st.markdown("""
    <div class="sb-logo">
        <p class="sb-logo-title">🎬 YT Knowledge</p>
        <p class="sb-logo-sub">Powered by Claude · RAG · ChromaDB</p>
    </div>
    """, unsafe_allow_html=True)

    # API Keys
    st.markdown('<div class="sb-section-label">🔑 API Keys</div>', unsafe_allow_html=True)
    with st.expander("Configure keys", expanded=not bool(ANTHROPIC_API_KEY)):
        anthropic_key = st.text_input("Anthropic API Key", value=ANTHROPIC_API_KEY,
                                       type="password",
                                       placeholder="sk-ant-...")
        yt_key = st.text_input("YouTube API Key _(optional)_", value=YOUTUBE_API_KEY,
                                type="password",
                                placeholder="AIza...")

    # URL input
    st.markdown('<div class="sb-section-label">📺 Add Video</div>', unsafe_allow_html=True)
    url_input = st.text_input("", placeholder="youtube.com/watch?v=... or playlist...",
                               label_visibility="collapsed")
    process_btn = st.button("⚡  Process Video", type="primary", use_container_width=True)

    # Loaded videos
    if st.session_state.loaded_videos:
        st.markdown(
            f'<div class="sb-section-label">📚 Loaded &nbsp;'
            f'<span style="color:#a78bfa">({len(st.session_state.loaded_videos)})</span></div>',
            unsafe_allow_html=True,
        )
        for vid, info in st.session_state.loaded_videos.items():
            thumb = info.get('thumbnail') or f"https://img.youtube.com/vi/{vid}/mqdefault.jpg"
            title = info.get('title', vid)[:42]
            chunks = info.get('chunks', 0)
            channel = info.get('channel', '')[:22]
            st.markdown(f"""
            <div class="video-card-sb">
                <img class="video-thumb" src="{thumb}" onerror="this.src='https://img.youtube.com/vi/{vid}/mqdefault.jpg'"/>
                <div class="video-info">
                    <div class="video-title-sb" title="{info.get('title',vid)}">{title}</div>
                    <div class="video-meta">
                        <span class="badge badge-purple">{chunks} chunks</span>
                        {"<span class='badge badge-cyan'>"+channel+"</span>" if channel else ""}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        if st.button("🗑  Clear All", type="secondary", use_container_width=True):
            if st.session_state.vector_store:
                st.session_state.vector_store.clear_all()
            st.session_state.loaded_videos = {}
            st.session_state.messages = []
            st.session_state.chat_history_text = ""
            st.rerun()

    # Format selector
    st.markdown('<div class="sb-section-label">📋 Response Format</div>', unsafe_allow_html=True)
    current_fmt = st.session_state.output_format
    cols = st.columns(2)
    for i, (label, value) in enumerate(FORMAT_OPTIONS):
        active = "active" if current_fmt == value else ""
        with cols[i % 2]:
            if st.button(label, key=f"fmt_{value}", use_container_width=True,
                         type="secondary"):
                st.session_state.output_format = value
                st.rerun()

    # Model info
    st.markdown('<div class="sb-section-label">⚙ Model</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);
                border-radius:10px;padding:10px 12px;font-size:0.75rem;color:#475569;">
        <div style="color:#94a3b8;font-weight:600;margin-bottom:3px;">LLM</div>
        <div>{LLM_MODEL}</div>
        <div style="color:#94a3b8;font-weight:600;margin:6px 0 3px;">Embeddings</div>
        <div>HuggingFace · all-MiniLM-L6-v2</div>
        <div style="color:#94a3b8;font-weight:600;margin:6px 0 3px;">Vector DB</div>
        <div>ChromaDB · local</div>
    </div>
    """, unsafe_allow_html=True)


# ── Main area ──────────────────────────────────────────────

# Hero
st.markdown("""
<div class="hero-wrap">
    <div class="hero-badge">✦ RAG · Multi-Video · Timestamped</div>
    <h1 class="hero-title">YouTube Knowledge Assistant</h1>
    <p class="hero-sub">Ask anything about any YouTube video and get answers with timestamps</p>
</div>
""", unsafe_allow_html=True)

# Stats bar
vcount = len(st.session_state.loaded_videos)
ccount = total_chunks()
mcount = len(st.session_state.messages) // 2
st.markdown(f"""
<div class="stats-bar">
    <div class="stat-card purple">
        <div class="stat-label">Videos Loaded</div>
        <div class="stat-value">{vcount}</div>
        <div class="stat-icon">🎬</div>
    </div>
    <div class="stat-card cyan">
        <div class="stat-label">Chunks Indexed</div>
        <div class="stat-value">{ccount}</div>
        <div class="stat-icon">⬡</div>
    </div>
    <div class="stat-card pink">
        <div class="stat-label">Messages</div>
        <div class="stat-value">{mcount}</div>
        <div class="stat-icon">💬</div>
    </div>
    <div class="stat-card green">
        <div class="stat-label">Format</div>
        <div class="stat-value" style="font-size:0.9rem;margin-top:2px;">{st.session_state.output_format}</div>
        <div class="stat-icon">◈</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ── Video processing ───────────────────────────────────────
if process_btn and url_input and anthropic_key:
    step_ph = st.empty()

    def render_steps(steps):
        html = "".join(
            f'<div class="step-item {s["state"]}">'
            f'<div class="step-icon">{s["icon"]}</div>'
            f'<span>{s["label"]}</span></div>'
            for s in steps
        )
        step_ph.markdown(
            f'<div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.07);'
            f'border-radius:14px;padding:14px 18px;margin-bottom:16px">{html}</div>',
            unsafe_allow_html=True,
        )

    steps = [
        {"icon": "◌", "label": "Initialising models",        "state": "pending"},
        {"icon": "◌", "label": "Resolving URL",              "state": "pending"},
        {"icon": "◌", "label": "Fetching transcript",        "state": "pending"},
        {"icon": "◌", "label": "Chunking & embedding",       "state": "pending"},
        {"icon": "◌", "label": "Saving to vector store",     "state": "pending"},
        {"icon": "◌", "label": "Building retriever",         "state": "pending"},
    ]

    def set_step(i, state):
        steps[i]["state"] = state
        steps[i]["icon"] = "✓" if state == "done" else "◉"
        render_steps(steps)

    try:
        set_step(0, "active")
        llm = init_llm(anthropic_key)
        embeddings = init_embeddings()
        vector_store, metadata_store = init_stores(embeddings)
        st.session_state.llm = llm
        st.session_state.vector_store = vector_store
        st.session_state.metadata_store = metadata_store
        set_step(0, "done"); set_step(1, "active")

        from core.ingestion.url_parser import resolve_video_ids
        videos = resolve_video_ids(url_input, yt_key)
        if not videos:
            st.error("Could not resolve any videos from that URL.")
            st.stop()
        set_step(1, "done"); set_step(2, "active")

        for video_info in videos:
            vid = video_info.video_id
            from core.ingestion.transcript import fetch_transcript
            transcript = fetch_transcript(vid)
            if not transcript:
                st.warning(f"No transcript for {vid} — skipping.")
                continue
            set_step(2, "done"); set_step(3, "active")

            from core.processing.chunker import chunk_transcript, chunks_to_documents
            title = video_info.title or vid
            chunks = chunk_transcript(transcript, video_title=title)
            documents = chunks_to_documents(chunks)
            set_step(3, "done"); set_step(4, "active")

            vector_store.add_documents(documents)
            metadata_store.save_video(
                video_id=vid, title=title,
                channel=video_info.channel,
                duration=video_info.duration,
                thumbnail_url=video_info.thumbnail_url,
                transcript_source=transcript.source,
                chunk_count=len(chunks),
            )

            if yt_key:
                from core.ingestion.comments import fetch_comments
                from core.processing.sentiment import run_full_analysis
                comments = fetch_comments(vid, yt_key)
                if comments:
                    sentiment = run_full_analysis(vid, comments, llm)
                    metadata_store.save_sentiment(vid, sentiment)

            st.session_state.loaded_videos[vid] = {
                'title': title,
                'thumbnail': video_info.thumbnail_url,
                'chunks': len(chunks),
                'channel': video_info.channel,
            }
            set_step(4, "done")

        set_step(5, "active")
        from core.retrieval.retriever import get_multi_query_retriever
        st.session_state.retriever = get_multi_query_retriever(
            vector_store, llm, search_type="mmr", k=RETRIEVER_K)
        set_step(5, "done")

        st.success(f"✅ Ready — {len(videos)} video(s) indexed. Start chatting below!")
        st.rerun()

    except Exception as e:
        st.error(f"Error: {e}")
        import traceback
        st.code(traceback.format_exc())


# ── Welcome screen (no videos loaded) ─────────────────────
if not st.session_state.loaded_videos:
    st.markdown("""
    <div class="welcome-wrap">
        <div class="welcome-orb">🎬</div>
        <div class="welcome-title">No videos loaded yet</div>
        <div class="welcome-sub">Paste a YouTube URL in the sidebar and hit <strong>Process Video</strong> to get started.</div>
        <div class="feature-grid">
            <div class="feature-pill"><span>⏱</span> Timestamped answers</div>
            <div class="feature-pill"><span>⇔</span> Cross-video compare</div>
            <div class="feature-pill"><span>💬</span> Sentiment analysis</div>
            <div class="feature-pill"><span>⬡</span> Flashcards & quizzes</div>
            <div class="feature-pill"><span>◗</span> Smart summaries</div>
            <div class="feature-pill"><span>🧠</span> Conversation memory</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    # ── Chat messages ──────────────────────────────────────
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="chat-bubble-user">
                <div class="bubble-inner">{msg["content"]}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            intent = msg.get("intent", "")
            badge_label, badge_cls = INTENT_META.get(intent, ("", ""))
            badge_html = f'<div class="intent-badge {badge_cls}">{badge_label}</div>' if badge_label else ""
            st.markdown(f"""
            <div class="chat-bubble-ai">
                <div class="ai-avatar">✦</div>
                <div class="bubble-inner">
                    {badge_html}
                    {msg["content"]}
                </div>
            </div>
            """, unsafe_allow_html=True)


# ── Chat input ─────────────────────────────────────────────
prompt = st.chat_input(
    "Ask anything about the video(s)…",
    disabled=not st.session_state.loaded_videos,
)

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.markdown(f"""
    <div class="chat-bubble-user">
        <div class="bubble-inner">{prompt}</div>
    </div>
    """, unsafe_allow_html=True)

    thinking_ph = st.empty()
    thinking_ph.markdown("""
    <div class="chat-bubble-ai">
        <div class="ai-avatar">✦</div>
        <div class="bubble-inner">
            <div class="thinking-wrap">
                <div class="dot-wave"><span></span><span></span><span></span></div>
                Thinking…
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    try:
        llm        = st.session_state.llm
        retriever  = st.session_state.retriever
        vs         = st.session_state.vector_store
        ms         = st.session_state.metadata_store
        video_ids  = list(st.session_state.loaded_videos.keys())
        video_titles = {v: i['title'] for v, i in st.session_state.loaded_videos.items()}
        titles_str = ", ".join(video_titles.values())
        fmt        = st.session_state.output_format

        # Intent routing
        if fmt == "Auto":
            from core.chains.router import classify_intent
            intent = classify_intent(llm, prompt, len(video_ids), titles_str)
        else:
            intent = FORMAT_TO_INTENT.get(fmt, "factual_qa")

        # Execute chain
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
                response = "I need at least **2 videos** loaded to compare. Add another video in the sidebar."
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
            from core.chains.qa_chain import run_qa
            result   = run_qa(llm, retriever, prompt, st.session_state.chat_history_text)
            response = result["answer"]

        # Render response
        badge_label, badge_cls = INTENT_META.get(intent, ("", ""))
        badge_html = f'<div class="intent-badge {badge_cls}">{badge_label}</div>' if badge_label else ""
        thinking_ph.markdown(f"""
        <div class="chat-bubble-ai">
            <div class="ai-avatar">✦</div>
            <div class="bubble-inner">
                {badge_html}
                {response}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.session_state.messages.append({"role": "assistant", "content": response, "intent": intent})

        # Update chat history window
        recent = st.session_state.messages[-(MEMORY_WINDOW_SIZE * 2):]
        st.session_state.chat_history_text = "\n".join(
            f"{'Human' if m['role']=='user' else 'Assistant'}: {m['content'][:200]}"
            for m in recent
        )

        if ms:
            ms.save_chat_message(st.session_state.session_id, "user", prompt)
            ms.save_chat_message(st.session_state.session_id, "assistant", response[:500])

    except Exception as e:
        thinking_ph.empty()
        st.error(f"Error: {e}")
        import traceback
        st.code(traceback.format_exc())


# ── Footer ─────────────────────────────────────────────────
st.markdown("""
<div class="app-footer">
    YouTube Knowledge Assistant &nbsp;·&nbsp; Claude · LangChain · ChromaDB · Streamlit
</div>
""", unsafe_allow_html=True)
