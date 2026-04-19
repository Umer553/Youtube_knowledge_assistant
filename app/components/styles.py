"""All CSS for the YouTube Knowledge Assistant UI."""


def get_css() -> str:
    return """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Inter:wght@300;400;500&display=swap');

/* ── Reset & Base ────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    background: #07071a !important;
    color: #e2e8f0 !important;
    font-family: 'Inter', sans-serif;
}

[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed;
    inset: 0;
    background:
        radial-gradient(ellipse 80% 50% at 20% -10%, rgba(124,58,237,0.18) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 110%, rgba(255,51,102,0.12) 0%, transparent 55%),
        radial-gradient(ellipse 50% 60% at 50% 50%, rgba(6,182,212,0.05) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
}

[data-testid="stMain"] { background: transparent !important; }
[data-testid="block-container"] { padding-top: 1.5rem !important; }

/* ── Sidebar ─────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: rgba(10,10,30,0.95) !important;
    border-right: 1px solid rgba(124,58,237,0.2) !important;
    backdrop-filter: blur(20px);
}
[data-testid="stSidebar"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #7c3aed, #ff3366, #06b6d4);
}
[data-testid="stSidebar"] > div { padding-top: 0 !important; }

/* ── Scrollbar ───────────────────────────────────── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(124,58,237,0.4); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(124,58,237,0.7); }

/* ── Hero Header ─────────────────────────────────── */
.hero-wrap {
    text-align: center;
    padding: 2.5rem 1rem 1.5rem;
    position: relative;
}
.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(124,58,237,0.12);
    border: 1px solid rgba(124,58,237,0.35);
    border-radius: 50px;
    padding: 5px 14px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    color: #a78bfa;
    text-transform: uppercase;
    margin-bottom: 14px;
}
.hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: clamp(2rem, 4vw, 3rem);
    font-weight: 700;
    line-height: 1.15;
    background: linear-gradient(135deg, #e2e8f0 0%, #a78bfa 40%, #ff3366 70%, #06b6d4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 10px;
    letter-spacing: -0.02em;
}
.hero-sub {
    color: #64748b;
    font-size: 1rem;
    font-weight: 400;
    margin: 0;
}

/* ── Stats Bar ───────────────────────────────────── */
.stats-bar {
    display: flex;
    gap: 12px;
    margin: 0 0 24px;
    flex-wrap: wrap;
}
.stat-card {
    flex: 1;
    min-width: 120px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 14px 18px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.3s;
}
.stat-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    border-radius: 2px 2px 0 0;
}
.stat-card.purple::before { background: linear-gradient(90deg, #7c3aed, #a78bfa); }
.stat-card.pink::before   { background: linear-gradient(90deg, #ff3366, #fb7185); }
.stat-card.cyan::before   { background: linear-gradient(90deg, #06b6d4, #67e8f9); }
.stat-card.green::before  { background: linear-gradient(90deg, #10b981, #6ee7b7); }
.stat-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #64748b;
    margin-bottom: 4px;
}
.stat-value {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: #e2e8f0;
    line-height: 1;
}
.stat-icon {
    position: absolute;
    right: 14px; top: 50%;
    transform: translateY(-50%);
    font-size: 1.4rem;
    opacity: 0.15;
}

/* ── Welcome Screen ──────────────────────────────── */
.welcome-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
    text-align: center;
}
.welcome-orb {
    width: 90px; height: 90px;
    border-radius: 50%;
    background: linear-gradient(135deg, rgba(124,58,237,0.3), rgba(255,51,102,0.3));
    border: 1px solid rgba(124,58,237,0.4);
    display: flex; align-items: center; justify-content: center;
    font-size: 2.4rem;
    margin-bottom: 24px;
    box-shadow: 0 0 40px rgba(124,58,237,0.2), 0 0 80px rgba(124,58,237,0.08);
    animation: pulse-orb 3s ease-in-out infinite;
}
@keyframes pulse-orb {
    0%, 100% { box-shadow: 0 0 40px rgba(124,58,237,0.2), 0 0 80px rgba(124,58,237,0.08); }
    50%       { box-shadow: 0 0 60px rgba(124,58,237,0.35), 0 0 100px rgba(124,58,237,0.15); }
}
.welcome-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.3rem;
    font-weight: 600;
    color: #e2e8f0;
    margin: 0 0 8px;
}
.welcome-sub {
    color: #475569;
    font-size: 0.9rem;
    max-width: 380px;
    line-height: 1.6;
}
.feature-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin-top: 28px;
    max-width: 560px;
    width: 100%;
}
.feature-pill {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px;
    padding: 10px 12px;
    font-size: 0.78rem;
    color: #64748b;
    display: flex;
    align-items: center;
    gap: 6px;
}
.feature-pill span { color: #a78bfa; font-size: 1rem; }

/* ── Chat Messages ───────────────────────────────── */
.chat-bubble-user {
    display: flex;
    justify-content: flex-end;
    margin: 8px 0;
    animation: slide-in-right 0.25s ease;
}
@keyframes slide-in-right {
    from { opacity: 0; transform: translateX(16px); }
    to   { opacity: 1; transform: translateX(0); }
}
.chat-bubble-user .bubble-inner {
    background: linear-gradient(135deg, #7c3aed, #6d28d9);
    border: 1px solid rgba(167,139,250,0.3);
    border-radius: 18px 18px 4px 18px;
    padding: 11px 16px;
    max-width: 75%;
    font-size: 0.92rem;
    line-height: 1.55;
    color: #ede9fe;
    box-shadow: 0 4px 20px rgba(124,58,237,0.25);
}
.chat-bubble-ai {
    display: flex;
    gap: 10px;
    margin: 8px 0;
    animation: slide-in-left 0.25s ease;
}
@keyframes slide-in-left {
    from { opacity: 0; transform: translateX(-16px); }
    to   { opacity: 1; transform: translateX(0); }
}
.ai-avatar {
    width: 34px; height: 34px;
    border-radius: 50%;
    background: linear-gradient(135deg, #7c3aed, #ff3366);
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem;
    flex-shrink: 0;
    box-shadow: 0 0 16px rgba(124,58,237,0.35);
    margin-top: 2px;
}
.chat-bubble-ai .bubble-inner {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 4px 18px 18px 18px;
    padding: 13px 16px;
    max-width: 85%;
    font-size: 0.92rem;
    line-height: 1.6;
    color: #cbd5e1;
    backdrop-filter: blur(10px);
}

/* ── Source Citation Cards ───────────────────────── */
.sources-wrap {
    margin-top: 12px;
    display: flex;
    flex-direction: column;
    gap: 6px;
}
.source-card {
    background: rgba(6,182,212,0.05);
    border: 1px solid rgba(6,182,212,0.18);
    border-radius: 10px;
    padding: 8px 12px;
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.78rem;
    color: #94a3b8;
}
.source-ts {
    background: rgba(6,182,212,0.15);
    color: #06b6d4;
    border-radius: 6px;
    padding: 2px 8px;
    font-weight: 600;
    white-space: nowrap;
    font-family: 'Space Grotesk', sans-serif;
}
.source-title { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.source-link {
    color: #06b6d4;
    text-decoration: none;
    font-weight: 600;
    font-size: 0.75rem;
    white-space: nowrap;
    padding: 2px 8px;
    border: 1px solid rgba(6,182,212,0.3);
    border-radius: 6px;
    transition: all 0.2s;
}
.source-link:hover { background: rgba(6,182,212,0.15); }

/* ── Sidebar Logo ────────────────────────────────── */
.sb-logo {
    padding: 22px 16px 14px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 4px;
}
.sb-logo-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.15rem;
    font-weight: 700;
    background: linear-gradient(135deg, #a78bfa, #ff3366);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    line-height: 1.2;
}
.sb-logo-sub {
    font-size: 0.73rem;
    color: #475569;
    margin: 2px 0 0;
}

/* ── Section Labels ──────────────────────────────── */
.sb-section-label {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #475569;
    margin: 16px 0 8px;
    display: flex;
    align-items: center;
    gap: 6px;
}
.sb-section-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: rgba(255,255,255,0.06);
}

/* ── Video Cards in Sidebar ──────────────────────── */
.video-card-sb {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 10px;
    margin: 6px 0;
    display: flex;
    gap: 10px;
    align-items: flex-start;
    transition: border-color 0.2s;
    position: relative;
    overflow: hidden;
}
.video-card-sb::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 2px;
    background: linear-gradient(180deg, #7c3aed, #ff3366);
    border-radius: 2px 0 0 2px;
}
.video-thumb {
    width: 72px; height: 44px;
    border-radius: 7px;
    object-fit: cover;
    flex-shrink: 0;
    border: 1px solid rgba(255,255,255,0.08);
}
.video-info { flex: 1; overflow: hidden; }
.video-title-sb {
    font-size: 0.78rem;
    font-weight: 600;
    color: #cbd5e1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-bottom: 4px;
}
.video-meta { display: flex; gap: 5px; flex-wrap: wrap; }
.badge {
    font-size: 0.65rem;
    font-weight: 600;
    padding: 2px 7px;
    border-radius: 5px;
}
.badge-purple { background: rgba(124,58,237,0.2); color: #a78bfa; }
.badge-cyan   { background: rgba(6,182,212,0.15);  color: #67e8f9; }
.badge-green  { background: rgba(16,185,129,0.15); color: #6ee7b7; }
.badge-pink   { background: rgba(255,51,102,0.15); color: #fb7185; }

/* ── Format Pills ────────────────────────────────── */
.format-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
    margin-top: 4px;
}
.format-pill {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 9px;
    padding: 7px 10px;
    font-size: 0.75rem;
    font-weight: 500;
    color: #64748b;
    cursor: pointer;
    text-align: center;
    transition: all 0.2s;
    user-select: none;
}
.format-pill:hover {
    border-color: rgba(124,58,237,0.4);
    color: #a78bfa;
    background: rgba(124,58,237,0.08);
}
.format-pill.active {
    background: rgba(124,58,237,0.18);
    border-color: rgba(124,58,237,0.5);
    color: #c4b5fd;
    box-shadow: 0 0 12px rgba(124,58,237,0.15);
}

/* ── Processing Steps ────────────────────────────── */
.step-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 7px 0;
    font-size: 0.85rem;
    color: #64748b;
}
.step-icon {
    width: 26px; height: 26px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.8rem;
    flex-shrink: 0;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
}
.step-item.done   .step-icon { background: rgba(16,185,129,0.2);  border-color: rgba(16,185,129,0.4);  color: #10b981; }
.step-item.active .step-icon { background: rgba(124,58,237,0.2); border-color: rgba(124,58,237,0.5); color: #a78bfa; animation: spin 1s linear infinite; }
.step-item.done   { color: #94a3b8; }
.step-item.active { color: #e2e8f0; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Inputs override ─────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-family: 'Inter', sans-serif !important;
    transition: border-color 0.2s !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: rgba(124,58,237,0.6) !important;
    box-shadow: 0 0 0 2px rgba(124,58,237,0.12) !important;
}
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stSelectbox"] label {
    color: #64748b !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em !important;
}

/* ── Buttons ─────────────────────────────────────── */
[data-testid="stButton"] button[kind="primary"] {
    background: linear-gradient(135deg, #7c3aed, #6d28d9) !important;
    border: none !important;
    border-radius: 10px !important;
    color: #fff !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 16px rgba(124,58,237,0.3) !important;
}
[data-testid="stButton"] button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 24px rgba(124,58,237,0.45) !important;
}
[data-testid="stButton"] button[kind="secondary"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    color: #94a3b8 !important;
    transition: all 0.2s !important;
}
[data-testid="stButton"] button[kind="secondary"]:hover {
    border-color: rgba(255,51,102,0.4) !important;
    color: #fb7185 !important;
}

/* ── Expander ────────────────────────────────────── */
[data-testid="stExpander"] {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 12px !important;
}
[data-testid="stExpander"] summary {
    color: #94a3b8 !important;
    font-size: 0.82rem !important;
}

/* ── Alerts ──────────────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    font-size: 0.85rem !important;
}

/* ── Selectbox ───────────────────────────────────── */
[data-testid="stSelectbox"] > div > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
}

/* ── Chat input ──────────────────────────────────── */
[data-testid="stChatInput"] {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(124,58,237,0.3) !important;
    border-radius: 14px !important;
    box-shadow: 0 0 20px rgba(124,58,237,0.08) !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: rgba(124,58,237,0.6) !important;
    box-shadow: 0 0 0 2px rgba(124,58,237,0.15), 0 0 30px rgba(124,58,237,0.12) !important;
}
[data-testid="stChatInput"] textarea {
    color: #e2e8f0 !important;
    background: transparent !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── Spinner ─────────────────────────────────────── */
[data-testid="stSpinner"] { color: #a78bfa !important; }

/* ── Divider ─────────────────────────────────────── */
hr { border-color: rgba(255,255,255,0.06) !important; margin: 12px 0 !important; }

/* ── Hide default Streamlit chrome ───────────────── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }

/* ── Thinking indicator ──────────────────────────── */
.thinking-wrap {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 0;
    color: #64748b;
    font-size: 0.85rem;
}
.dot-wave { display: flex; gap: 4px; }
.dot-wave span {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #7c3aed;
    display: inline-block;
    animation: wave 1.2s ease-in-out infinite;
}
.dot-wave span:nth-child(2) { animation-delay: 0.2s; }
.dot-wave span:nth-child(3) { animation-delay: 0.4s; }
@keyframes wave {
    0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
    40%           { transform: translateY(-6px); opacity: 1; }
}

/* ── Intent badge ────────────────────────────────── */
.intent-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 2px 8px;
    border-radius: 6px;
    margin-bottom: 8px;
}
.intent-qa         { background: rgba(124,58,237,0.15); color: #a78bfa; border: 1px solid rgba(124,58,237,0.3); }
.intent-summarize  { background: rgba(6,182,212,0.12);  color: #67e8f9; border: 1px solid rgba(6,182,212,0.25); }
.intent-compare    { background: rgba(245,158,11,0.12); color: #fbbf24; border: 1px solid rgba(245,158,11,0.25); }
.intent-sentiment  { background: rgba(255,51,102,0.12); color: #fb7185; border: 1px solid rgba(255,51,102,0.25); }
.intent-flashcards { background: rgba(16,185,129,0.12); color: #6ee7b7; border: 1px solid rgba(16,185,129,0.25); }
.intent-quiz       { background: rgba(251,146,60,0.12); color: #fdba74; border: 1px solid rgba(251,146,60,0.25); }

/* ── Footer ──────────────────────────────────────── */
.app-footer {
    text-align: center;
    padding: 20px 0 8px;
    font-size: 0.72rem;
    color: #1e293b;
    letter-spacing: 0.04em;
}
</style>
"""
