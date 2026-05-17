"""All CSS for the YouTube Knowledge Assistant UI."""


def get_css() -> str:
    return """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Palette (amber / teal / slate) ───────────────────── */
:root {
    --amber:        #f59e0b;
    --amber-light:  #fcd34d;
    --amber-dim:    rgba(245,158,11,0.14);
    --amber-border: rgba(245,158,11,0.30);
    --teal:         #0d9488;
    --teal-light:   #2dd4bf;
    --teal-dim:     rgba(13,148,136,0.14);
    --sky:          #38bdf8;
    --rose:         #fb7185;
    --emerald:      #34d399;
    --bg:           #07090f;
    --bg-2:         #0d1117;
    --bg-3:         #111722;
    --border:       rgba(255,255,255,0.07);
    --border-hi:    rgba(255,255,255,0.13);
    --txt-1:        #f1f5f9;
    --txt-2:        #94a3b8;
    --txt-3:        #475569;
}

/* ── Reset & Base ─────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--txt-1) !important;
    font-family: 'Outfit', sans-serif;
}

/* Warm ambient blobs */
[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed;
    inset: 0;
    background:
        radial-gradient(ellipse 70% 45% at 10% 0%,   rgba(245,158,11,0.10) 0%, transparent 55%),
        radial-gradient(ellipse 55% 40% at 90% 100%,  rgba(13,148,136,0.10) 0%, transparent 55%),
        radial-gradient(ellipse 40% 50% at 55% 45%,   rgba(56,189,248,0.04) 0%, transparent 65%);
    pointer-events: none;
    z-index: 0;
}

[data-testid="stMain"]          { background: transparent !important; }
[data-testid="block-container"] { padding-top: 1.2rem !important; }

/* ── Scrollbar ─────────────────────────────────────────── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--amber-border); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(245,158,11,0.55); }

/* ═══════════════════════════════════════════════════════
   SIDEBAR — FIX: target BOTH old and new Streamlit testids
   Streamlit renamed stSidebar inner div to stSidebarContent
   in v1.29+. We cover both so it works across versions.
   ═══════════════════════════════════════════════════════ */

/* Sidebar shell */
[data-testid="stSidebar"],
section[data-testid="stSidebar"] {
    background: var(--bg-2) !important;
    border-right: 1px solid var(--border) !important;
    /* FIX: must be position:relative so ::before renders correctly */
    position: relative !important;
    /* FIX: ensure sidebar is never zero-height or hidden */
    min-height: 100vh !important;
    display: flex !important;
    flex-direction: column !important;
}

/* Amber top stripe */
[data-testid="stSidebar"]::before,
section[data-testid="stSidebar"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--amber), var(--teal-light), var(--sky));
    z-index: 10;
}

/* FIX: the original had `padding-top: 0 !important` on > div which
   collapsed content in newer Streamlit. Now we target the correct
   inner content wrapper and give it proper padding. */
[data-testid="stSidebar"] > div,
[data-testid="stSidebarContent"],
[data-testid="stSidebarUserContent"] {
    padding-top: 0 !important;
    overflow-x: hidden !important;
    display: flex !important;
    flex-direction: column !important;
}

/* FIX: Streamlit wraps sidebar widgets in a stVerticalBlock —
   make sure it's not squashed to zero height */
[data-testid="stSidebar"] [data-testid="stVerticalBlock"],
[data-testid="stSidebarContent"] [data-testid="stVerticalBlock"] {
    gap: 0 !important;
    flex: 1 !important;
    min-height: 0 !important;
}

/* ── Sidebar — Brand ───────────────────────────────────── */
.sb-logo {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 22px 16px 16px;
    border-bottom: 1px solid var(--border);
}
.sb-logo-icon {
    width: 40px; height: 40px;
    border-radius: 10px;
    background: linear-gradient(135deg, var(--amber), #d97706);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.3rem;
    box-shadow: 0 4px 16px rgba(245,158,11,0.35);
    flex-shrink: 0;
}
.sb-logo-title {
    font-family: 'Outfit', sans-serif;
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--txt-1);
    margin: 0;
    line-height: 1.2;
}
.sb-logo-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.60rem;
    color: var(--txt-3);
    margin: 2px 0 0;
    letter-spacing: 0.04em;
}

/* ── Sidebar — Section labels ──────────────────────────── */
.sb-section-label {
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 0.60rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--txt-3);
    margin: 16px 0 8px;
}
.sb-section-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
}

/* ── Sidebar — API status ──────────────────────────────── */
.api-status {
    font-size: 0.70rem;
    font-weight: 600;
    padding: 4px 11px;
    border-radius: 6px;
    margin-top: 7px;
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-family: 'JetBrains Mono', monospace;
}
.api-status.ok   { background: rgba(52,211,153,0.10); color: var(--emerald); border: 1px solid rgba(52,211,153,0.28); }
.api-status.warn { background: var(--amber-dim);       color: var(--amber);   border: 1px solid var(--amber-border); }

/* ── Sidebar — Count badge ─────────────────────────────── */
.count-badge {
    background: var(--amber-dim);
    color: var(--amber);
    font-size: 0.65rem;
    font-weight: 700;
    padding: 1px 7px;
    border-radius: 4px;
    border: 1px solid var(--amber-border);
    font-family: 'JetBrains Mono', monospace;
}

/* ── Sidebar — Loaded indicator ────────────────────────── */
.sb-status-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 0 10px;
}
.sb-status-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: var(--emerald);
    box-shadow: 0 0 6px var(--emerald);
    flex-shrink: 0;
}
.sb-status-text {
    font-size: 0.72rem;
    font-weight: 500;
    color: var(--txt-2);
    font-family: 'JetBrains Mono', monospace;
}

/* ── Main area — Video pills ───────────────────────────── */
.video-pills-row {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin: 10px 0 14px;
}
.video-pill {
    display: inline-flex;
    align-items: center;
    background: var(--bg-3);
    border: 1px solid var(--amber-border);
    color: var(--txt-2);
    font-size: 0.72rem;
    font-weight: 500;
    padding: 4px 10px;
    border-radius: 20px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 280px;
}
.video-pill::before {
    content: '▶';
    font-size: 0.55rem;
    color: var(--amber);
    margin-right: 5px;
}

/* ── Badges (kept for intent/stats use) ────────────────── */
.badge {
    font-size: 0.60rem;
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'JetBrains Mono', monospace;
}
.badge-amber   { background: var(--amber-dim);              color: var(--amber);       border: 1px solid var(--amber-border); }
.badge-teal    { background: var(--teal-dim);               color: var(--teal-light);  border: 1px solid rgba(13,148,136,0.28); }
.badge-sky     { background: rgba(56,189,248,0.10);         color: var(--sky);         border: 1px solid rgba(56,189,248,0.25); }
.badge-emerald { background: rgba(52,211,153,0.10);         color: var(--emerald);     border: 1px solid rgba(52,211,153,0.25); }

/* ── Sidebar — Tech stack card ─────────────────────────── */
.model-info-card {
    background: var(--bg-3);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 13px;
    display: flex;
    flex-direction: column;
    gap: 7px;
}
.model-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.72rem;
}
.model-label { color: var(--txt-3); font-weight: 600; letter-spacing: 0.04em; }
.model-value { color: var(--txt-2); font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; }

/* ── Page header (compact, professional) ───────────────── */
.page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 0 0.75rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1rem;
}
.page-title {
    font-family: 'Outfit', sans-serif;
    font-size: clamp(1.3rem, 2.5vw, 1.75rem);
    font-weight: 800;
    color: var(--txt-1);
    margin: 0 0 3px;
    letter-spacing: -0.02em;
    line-height: 1.2;
}
.page-title .hl {
    color: transparent;
    background: linear-gradient(90deg, var(--amber), var(--amber-light));
    -webkit-background-clip: text;
    background-clip: text;
}
.page-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.64rem;
    color: var(--txt-3);
    margin: 0;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

/* ── Stats strip ───────────────────────────────────────── */
.stats-strip {
    display: flex;
    align-items: center;
    gap: 0;
    background: var(--bg-3);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 18px;
}
.stat-item {
    flex: 1;
    padding: 12px 16px;
    display: flex;
    align-items: center;
    gap: 12px;
    border-right: 1px solid var(--border);
    transition: background 0.2s;
}
.stat-item:last-child { border-right: none; }
.stat-item:hover { background: rgba(255,255,255,0.02); }
.stat-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}
.stat-dot.amber   { background: var(--amber);      box-shadow: 0 0 8px var(--amber); }
.stat-dot.teal    { background: var(--teal-light);  box-shadow: 0 0 8px var(--teal-light); }
.stat-dot.sky     { background: var(--sky);         box-shadow: 0 0 8px var(--sky); }
.stat-dot.emerald { background: var(--emerald);     box-shadow: 0 0 8px var(--emerald); }
.stat-text { display: flex; flex-direction: column; gap: 1px; }
.stat-number {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.1rem;
    font-weight: 500;
    color: var(--txt-1);
    line-height: 1;
}
.stat-number-sm {
    font-family: 'Outfit', sans-serif;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--txt-1);
    line-height: 1.2;
}
.stat-desc {
    font-size: 0.64rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--txt-3);
}

/* ── Welcome screen ────────────────────────────────────── */
.welcome-wrap {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    padding: 1.2rem 0 1.8rem;
}
.welcome-title {
    font-family: 'Outfit', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--txt-1);
    margin: 0 0 5px;
}
.welcome-sub {
    color: var(--txt-3);
    font-size: 0.83rem;
    line-height: 1.6;
    margin-bottom: 22px;
    max-width: 480px;
}
.feature-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    width: 100%;
    max-width: 680px;
}
.feature-card {
    background: var(--bg-3);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 13px 14px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    transition: border-color 0.2s, background 0.2s;
    cursor: default;
}
.feature-card:hover {
    border-color: var(--amber-border);
    background: rgba(245,158,11,0.03);
}
.fc-icon  { font-size: 1.15rem; line-height: 1; }
.fc-title { font-size: 0.78rem; font-weight: 700; color: var(--txt-1); }
.fc-desc  { font-size: 0.66rem; color: var(--txt-3); line-height: 1.5; }

/* ── Chat messages ─────────────────────────────────────── */
[data-testid="stChatMessage"] {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    padding: 6px 4px !important;
    margin: 5px 0 !important;
    transition: border-color 0.2s;
}
[data-testid="stChatMessage"]:hover {
    border-color: #cbd5e1 !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: #fefce8 !important;
    border-color: #fcd34d !important;
}
/* Dark text inside all chat messages */
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] td,
[data-testid="stChatMessage"] th,
[data-testid="stChatMessage"] h1,
[data-testid="stChatMessage"] h2,
[data-testid="stChatMessage"] h3,
[data-testid="stChatMessage"] code,
[data-testid="stChatMessage"] pre {
    color: #1e293b !important;
}
[data-testid="stChatMessage"] code {
    background: #f1f5f9 !important;
}

/* ── Intent badges ─────────────────────────────────────── */
.intent-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    font-weight: 500;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 2px 8px;
    border-radius: 4px;
    margin-bottom: 8px;
}
.intent-qa         { background: var(--amber-dim);           color: var(--amber);      border: 1px solid var(--amber-border); }
.intent-summarize  { background: var(--teal-dim);            color: var(--teal-light); border: 1px solid rgba(13,148,136,0.28); }
.intent-compare    { background: rgba(56,189,248,0.10);      color: var(--sky);        border: 1px solid rgba(56,189,248,0.25); }
.intent-sentiment  { background: rgba(251,113,133,0.10);     color: var(--rose);       border: 1px solid rgba(251,113,133,0.25); }
.intent-flashcards { background: rgba(52,211,153,0.10);      color: var(--emerald);    border: 1px solid rgba(52,211,153,0.25); }
.intent-quiz       { background: rgba(167,139,250,0.10);     color: #a78bfa;           border: 1px solid rgba(167,139,250,0.25); }

/* ── Processing steps ──────────────────────────────────── */
.proc-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 6px 0;
    font-size: 0.84rem;
    color: var(--txt-2);
    font-family: 'JetBrains Mono', monospace;
}
.proc-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    flex-shrink: 0;
}
.proc-dot.done   { background: var(--emerald); box-shadow: 0 0 6px var(--emerald); }
.proc-dot.active { background: var(--amber);   box-shadow: 0 0 6px var(--amber); animation: blink 1s ease-in-out infinite; }
.proc-dot.wait   { background: var(--txt-3); }
@keyframes blink {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.3; }
}

/* ── Inputs ────────────────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    background: var(--bg-3) !important;
    border: 1px solid var(--border-hi) !important;
    border-radius: 7px !important;
    color: var(--txt-1) !important;
    font-family: 'Outfit', sans-serif !important;
    transition: border-color 0.2s !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: var(--amber-border) !important;
    box-shadow: 0 0 0 2px var(--amber-dim) !important;
}
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stSelectbox"] label {
    color: var(--txt-3) !important;
    font-size: 0.75rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em !important;
}

/* ── Radio (format selector) ───────────────────────────── */
[data-testid="stRadio"] label {
    color: var(--txt-2) !important;
    font-size: 0.80rem !important;
}
[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {
    font-size: 0.80rem !important;
}

/* ── Buttons ───────────────────────────────────────────── */
[data-testid="stButton"] button[kind="primary"] {
    background: linear-gradient(135deg, #d97706, var(--amber)) !important;
    border: none !important;
    border-radius: 7px !important;
    color: #0a0a0a !important;
    font-weight: 700 !important;
    font-family: 'Outfit', sans-serif !important;
    letter-spacing: 0.02em !important;
    transition: all 0.2s !important;
    box-shadow: 0 3px 14px rgba(245,158,11,0.35) !important;
}
[data-testid="stButton"] button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 5px 22px rgba(245,158,11,0.50) !important;
}
[data-testid="stButton"] button[kind="secondary"] {
    background: var(--bg-3) !important;
    border: 1px solid var(--border-hi) !important;
    border-radius: 7px !important;
    color: var(--txt-2) !important;
    font-family: 'Outfit', sans-serif !important;
    transition: all 0.2s !important;
}
[data-testid="stButton"] button[kind="secondary"]:hover {
    border-color: var(--amber-border) !important;
    color: var(--amber) !important;
}
[data-testid="stButton"] button:disabled {
    opacity: 0.30 !important;
    cursor: not-allowed !important;
}

/* ── Expander ──────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: var(--bg-3) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}
[data-testid="stExpander"] summary {
    color: var(--txt-2) !important;
    font-size: 0.82rem !important;
}

/* ── Alerts ────────────────────────────────────────────── */
[data-testid="stAlert"] { border-radius: 7px !important; font-size: 0.85rem !important; }

/* ── Status widget ─────────────────────────────────────── */
[data-testid="stStatus"] {
    background: var(--bg-3) !important;
    border: 1px solid var(--amber-border) !important;
    border-radius: 10px !important;
}

/* ── Chat input ────────────────────────────────────────── */
[data-testid="stChatInput"] {
    background: var(--bg-3) !important;
    border: 1px solid var(--amber-border) !important;
    border-radius: 10px !important;
    box-shadow: 0 0 18px rgba(245,158,11,0.07) !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: var(--amber) !important;
    box-shadow: 0 0 0 2px var(--amber-dim), 0 0 28px rgba(245,158,11,0.10) !important;
}
[data-testid="stChatInput"] textarea {
    color: var(--txt-1) !important;
    background: var(--bg-3) !important;
    font-family: 'Outfit', sans-serif !important;
    caret-color: var(--amber) !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: var(--txt-3) !important;
}

/* ── Divider ───────────────────────────────────────────── */
hr { border-color: var(--border) !important; margin: 10px 0 !important; }

/* ── Spinner ───────────────────────────────────────────── */
[data-testid="stSpinner"] { color: var(--amber) !important; }

/* ── Hide Streamlit chrome ─────────────────────────────── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }

/* ── Footer ────────────────────────────────────────────── */
.app-footer {
    text-align: center;
    padding: 20px 0 6px;
    font-size: 0.68rem;
    color: var(--txt-3);
    letter-spacing: 0.05em;
    font-family: 'JetBrains Mono', monospace;
    border-top: 1px solid var(--border);
    margin-top: 8px;
}
.app-footer .hl-a { color: var(--amber); }
.app-footer .hl-t { color: var(--teal-light); }
.app-footer .hl-s { color: var(--sky); }
.app-footer .hl-e { color: var(--emerald); }
</style>
"""