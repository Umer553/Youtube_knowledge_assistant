"""
YouTube Knowledge Assistant — Main Streamlit Application
A multi-video RAG chatbot with sentiment analysis, timestamped answers,
and intelligent summarization built with LangChain.

Run with: streamlit run app/main.py
"""

import streamlit as st
import sys
import os
import uuid

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.config import (
    OPENAI_API_KEY, YOUTUBE_API_KEY, LLM_MODEL,
    LLM_TEMPERATURE, RETRIEVER_K, MEMORY_WINDOW_SIZE,
)

# ── Page Config ────────────────────────────────────────────
st.set_page_config(
    page_title="YouTube Knowledge Assistant",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

    .main-header {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #ff3366, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .sub-header {
        color: #888;
        font-size: 0.95rem;
        margin-top: -8px;
        margin-bottom: 20px;
    }
    .video-card {
        background: #1a1a2e;
        border: 1px solid #2a2a3a;
        border-radius: 12px;
        padding: 12px;
        margin: 6px 0;
    }
    .timestamp-link {
        color: #06b6d4;
        text-decoration: none;
        font-weight: 500;
    }
    .sentiment-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .sentiment-positive { background: rgba(16,185,129,0.2); color: #10b981; }
    .sentiment-negative { background: rgba(255,51,102,0.2); color: #ff3366; }
    .sentiment-neutral { background: rgba(136,136,160,0.2); color: #8888a0; }
    .stChatMessage { border-radius: 12px; }
</style>
""", unsafe_allow_html=True)


# ── Session State Initialization ───────────────────────────
def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        'session_id': str(uuid.uuid4()),
        'messages': [],
        'loaded_videos': {},          # video_id -> {title, thumbnail, ...}
        'vector_store': None,
        'metadata_store': None,
        'llm': None,
        'embeddings': None,
        'retriever': None,
        'processing': False,
        'chat_history_text': "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


# ── Initialize LLM & Embeddings ───────────────────────────
@st.cache_resource
def init_llm(api_key: str):
    """Initialize the LLM (cached across reruns)."""
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        openai_api_key=api_key,
    )


@st.cache_resource
def init_embeddings(api_key: str):
    """Initialize embedding model (cached)."""
    from core.processing.embedder import get_embedding_model
    return get_embedding_model(provider="openai", api_key=api_key)


@st.cache_resource
def init_stores(_embedding_model):
    """Initialize vector store and metadata store (cached)."""
    from core.retrieval.vector_store import VectorStoreManager
    from core.retrieval.metadata_store import MetadataStore
    vs = VectorStoreManager(embedding_model=_embedding_model)
    ms = MetadataStore()
    return vs, ms


# ── Sidebar ────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="main-header">🎬 YT Assistant</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Chat with any YouTube video</p>', unsafe_allow_html=True)

    # API Key inputs
    with st.expander("🔑 API Keys", expanded=not bool(OPENAI_API_KEY)):
        openai_key = st.text_input(
            "OpenAI API Key",
            value=OPENAI_API_KEY,
            type="password",
            help="Required for GPT-4o-mini and embeddings"
        )
        yt_key = st.text_input(
            "YouTube API Key",
            value=YOUTUBE_API_KEY,
            type="password",
            help="Required for comments & metadata (optional)"
        )

    st.divider()

    # Video URL input
    st.subheader("📺 Add Videos")
    url_input = st.text_input(
        "YouTube URL",
        placeholder="Paste video, playlist, or channel URL...",
        help="Supports single videos, playlists, and channel URLs"
    )

    process_btn = st.button("⚡ Process Video(s)", type="primary", use_container_width=True)

    # Loaded videos display
    if st.session_state.loaded_videos:
        st.divider()
        st.subheader(f"📚 Loaded Videos ({len(st.session_state.loaded_videos)})")

        for vid, info in st.session_state.loaded_videos.items():
            with st.container():
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.image(info.get('thumbnail', f"https://img.youtube.com/vi/{vid}/mqdefault.jpg"), width=80)
                with col2:
                    st.markdown(f"**{info.get('title', vid)[:40]}**")
                    chunks = info.get('chunks', 0)
                    st.caption(f"{chunks} chunks indexed")

        if st.button("🗑️ Clear All Videos", use_container_width=True):
            if st.session_state.vector_store:
                st.session_state.vector_store.clear_all()
            st.session_state.loaded_videos = {}
            st.session_state.messages = []
            st.session_state.chat_history_text = ""
            st.rerun()

    st.divider()

    # Output format selector
    st.subheader("📋 Output Format")
    output_format = st.selectbox(
        "Response style",
        ["Auto (Smart Routing)", "Detailed Answer", "Summary",
         "Study Notes", "Flashcards", "Quiz", "Compare Videos"],
        help="Choose how the assistant formats its responses"
    )


# ── Video Processing Logic ─────────────────────────────────
if process_btn and url_input and openai_key:
    with st.spinner("🔄 Processing video(s)... This may take a moment."):
        try:
            # Initialize models
            llm = init_llm(openai_key)
            embeddings = init_embeddings(openai_key)
            vector_store, metadata_store = init_stores(embeddings)

            st.session_state.llm = llm
            st.session_state.vector_store = vector_store
            st.session_state.metadata_store = metadata_store
            st.session_state.embeddings = embeddings

            # Step 1: Resolve URLs
            from core.ingestion.url_parser import resolve_video_ids
            st.info("🔗 Resolving video URL(s)...")
            videos = resolve_video_ids(url_input, yt_key)

            if not videos:
                st.error("Could not resolve any videos from the URL.")
                st.stop()

            st.success(f"Found {len(videos)} video(s)")

            for video_info in videos:
                vid = video_info.video_id

                # Step 2: Fetch transcript
                from core.ingestion.transcript import fetch_transcript
                st.info(f"📝 Fetching transcript for {vid}...")
                transcript = fetch_transcript(vid)

                if not transcript:
                    st.warning(f"Could not get transcript for {vid}. Skipping.")
                    continue

                # Step 3: Chunk with timestamps
                from core.processing.chunker import chunk_transcript, chunks_to_documents
                title = video_info.title or vid
                chunks = chunk_transcript(transcript, video_title=title)
                documents = chunks_to_documents(chunks)

                st.info(f"✂️ Created {len(chunks)} chunks for '{title}'")

                # Step 4: Add to vector store
                vector_store.add_documents(documents)

                # Step 5: Save metadata
                metadata_store.save_video(
                    video_id=vid,
                    title=title,
                    channel=video_info.channel,
                    duration=video_info.duration,
                    thumbnail_url=video_info.thumbnail_url,
                    transcript_source=transcript.source,
                    chunk_count=len(chunks),
                )

                # Step 6: Fetch & analyze comments (if API key available)
                if yt_key:
                    from core.ingestion.comments import fetch_comments
                    from core.processing.sentiment import run_full_analysis
                    st.info(f"💬 Analyzing comments for '{title}'...")
                    comments = fetch_comments(vid, yt_key)
                    if comments:
                        sentiment = run_full_analysis(vid, comments, llm)
                        metadata_store.save_sentiment(vid, sentiment)
                        st.info(f"📊 Sentiment: {sentiment.overall_sentiment} "
                               f"({sentiment.positive_pct}% positive)")

                # Track loaded video
                st.session_state.loaded_videos[vid] = {
                    'title': title,
                    'thumbnail': video_info.thumbnail_url,
                    'chunks': len(chunks),
                    'channel': video_info.channel,
                }

            # Setup retriever
            from core.retrieval.retriever import get_multi_query_retriever
            st.session_state.retriever = get_multi_query_retriever(
                vector_store, llm, search_type="mmr", k=RETRIEVER_K,
            )

            st.success("✅ All videos processed! Start chatting below.")

        except Exception as e:
            st.error(f"Error processing video: {e}")
            import traceback
            st.code(traceback.format_exc())


# ── Main Chat Interface ────────────────────────────────────
st.markdown('<p class="main-header">YouTube Knowledge Assistant</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Ask anything about the loaded videos — get answers with timestamps</p>',
            unsafe_allow_html=True)

if not st.session_state.loaded_videos:
    st.info("👈 Paste a YouTube URL in the sidebar and click **Process** to get started.")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"], unsafe_allow_html=True)

# Chat input
if prompt := st.chat_input("Ask about the video(s)...", disabled=not st.session_state.loaded_videos):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        if not st.session_state.retriever or not st.session_state.llm:
            st.warning("Please process a video first.")
        else:
            with st.spinner("Thinking..."):
                try:
                    llm = st.session_state.llm
                    retriever = st.session_state.retriever
                    vector_store = st.session_state.vector_store
                    metadata_store = st.session_state.metadata_store

                    video_ids = list(st.session_state.loaded_videos.keys())
                    video_titles = {
                        vid: info['title']
                        for vid, info in st.session_state.loaded_videos.items()
                    }
                    titles_str = ", ".join(video_titles.values())

                    # Route based on selected format or auto-detect
                    if output_format == "Auto (Smart Routing)":
                        from core.chains.router import classify_intent
                        intent = classify_intent(
                            llm, prompt, len(video_ids), titles_str
                        )
                    else:
                        format_to_intent = {
                            "Detailed Answer": "factual_qa",
                            "Summary": "summarize",
                            "Study Notes": "summarize",
                            "Flashcards": "generate_flashcards",
                            "Quiz": "generate_quiz",
                            "Compare Videos": "compare_videos",
                        }
                        intent = format_to_intent.get(output_format, "factual_qa")

                    # Execute the appropriate chain
                    if intent == "factual_qa":
                        from core.chains.qa_chain import run_qa
                        result = run_qa(
                            llm, retriever, prompt,
                            st.session_state.chat_history_text,
                        )
                        response = result["answer"]

                    elif intent == "summarize":
                        from core.chains.summary_chain import run_summary
                        style = "study_notes" if output_format == "Study Notes" else "detailed"
                        response = run_summary(llm, retriever, style=style)

                    elif intent == "compare_videos":
                        from core.chains.compare_chain import run_comparison
                        if len(video_ids) < 2:
                            response = "I need at least 2 videos loaded to make a comparison. Please add more videos in the sidebar."
                        else:
                            response = run_comparison(
                                llm, vector_store, prompt,
                                video_ids, video_titles,
                            )

                    elif intent == "sentiment_query":
                        from core.chains.sentiment_chain import run_sentiment_query
                        # Get sentiment data for the first video (or merge)
                        sentiment_data = {}
                        for vid in video_ids:
                            s = metadata_store.get_sentiment(vid)
                            if s:
                                sentiment_data = s
                                break
                        response = run_sentiment_query(
                            llm, retriever, prompt, sentiment_data,
                        )

                    elif intent == "generate_flashcards":
                        from core.chains.formatter import generate_flashcards, format_flashcards_markdown
                        cards = generate_flashcards(llm, retriever, topic=prompt)
                        response = format_flashcards_markdown(cards)

                    elif intent == "generate_quiz":
                        from core.chains.formatter import generate_quiz, format_quiz_markdown
                        quiz = generate_quiz(llm, retriever, topic=prompt)
                        response = format_quiz_markdown(quiz)

                    else:
                        from core.chains.qa_chain import run_qa
                        result = run_qa(llm, retriever, prompt, st.session_state.chat_history_text)
                        response = result["answer"]

                    # Display response
                    st.markdown(response, unsafe_allow_html=True)

                    # Update conversation history
                    st.session_state.messages.append({"role": "assistant", "content": response})

                    # Update chat history text for context condensing
                    history_lines = []
                    recent = st.session_state.messages[-MEMORY_WINDOW_SIZE * 2:]
                    for msg in recent:
                        role = "Human" if msg["role"] == "user" else "Assistant"
                        history_lines.append(f"{role}: {msg['content'][:200]}")
                    st.session_state.chat_history_text = "\n".join(history_lines)

                    # Save to persistent history
                    if metadata_store:
                        metadata_store.save_chat_message(
                            st.session_state.session_id, "user", prompt
                        )
                        metadata_store.save_chat_message(
                            st.session_state.session_id, "assistant", response[:500]
                        )

                except Exception as e:
                    st.error(f"Error generating response: {e}")
                    import traceback
                    st.code(traceback.format_exc())


# ── Footer ─────────────────────────────────────────────────
st.divider()
st.caption("YouTube Knowledge Assistant — Built with LangChain, ChromaDB & Streamlit | Final Year Project")
