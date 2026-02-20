#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Thème Dark — Robust-Scraper Dashboard
ANSSI Burkina Faso

Polices :IBM Plex Mono(UI) + IBM Plex Mono (données)
Palette : Dark navy profond, accents cyan/red/amber/green
"""

DARK_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@300;400;500;600;700;800&display=swap');

:root {
    --bg-base: #060a10;
    --bg-raised: #0b1018;
    --bg-card: #0f151e;
    --bg-card-hover: #141c28;
    --bg-sidebar: #080c14;
    --bg-input: #0d1219;
    --bg-table-header: #0a0f16;

    --border: #1a2332;
    --border-subtle: #141c28;
    --border-active: rgba(34,211,238,0.3);

    --text-primary: #e4e9f0;
    --text-secondary: #8494a7;
    --text-muted: #4d5f73;

    --cyan: #22d3ee;
    --blue: #3b82f6;
    --red: #ef4444;
    --amber: #f59e0b;
    --green: #10b981;
    --yellow: #eab308;
    --rose: #f43f5e;
    --gray: #64748b;
}

/* ══════════ RESET ══════════ */
*, *::before, *::after {
    font-family: 'IBM Plex Mono', sans-serif !important;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}
code, pre, .mono, .kpi-value, .data-value {
    font-family: 'IBM Plex Mono', monospace !important;
}

/* ══════════ NUKE ALL EXTRA SPACE ══════════ */
.stApp {
    background: var(--bg-base) !important;
    color: var(--text-primary) !important;
}
.stApp > header { display: none !important; }
div[data-testid="stToolbar"] { display: none !important; }
div[data-testid="stDecoration"] { display: none !important; }
div[data-testid="stStatusWidget"] { display: none !important; }
.stDeployButton { display: none !important; }
#MainMenu { display: none !important; }
footer { display: none !important; }

.main .block-container {
    padding: 0.5rem 1.8rem 1rem !important;
    max-width: 1440px;
}
section.main > div:first-child { padding-top: 0 !important; }
.block-container > div:first-child { padding-top: 0 !important; }

/* ══════════ SIDEBAR ══════════ */
[data-testid="stSidebar"] {
    background: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 0.5rem !important; }
section[data-testid="stSidebar"] > div { padding-top: 0 !important; }
[data-testid="stSidebar"] * { color: var(--text-secondary) !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stSlider label,
[data-testid="stSidebar"] .stMultiSelect label {
    color: var(--text-muted) !important;
    font-size: 10px !important;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
}
[data-testid="stSidebar"] hr {
    border-color: var(--border) !important;
    margin: 0.5rem 0 !important;
}
[data-testid="stSidebarNav"] { display: none !important; }

/* ══════════ MASQUER keyboard_double et toutes icônes page_link ══════════ */
a[data-testid="stPageLink-NavLink"] span[data-testid="stIconMaterial"] { display: none !important; }
a[data-testid="stPageLink-NavLink"] svg { display: none !important; }
a[data-testid="stPageLink-NavLink"] span.material-symbols-outlined { display: none !important; }
a[data-testid="stPageLink-NavLink"] > div > span:first-child { display: none !important; }
/* Fallback : masquer tout élément icon par classe material */
[data-testid="stSidebar"] .material-symbols-outlined { display: none !important; }
[data-testid="stSidebar"] .e1nzilvr5 { display: none !important; }

/* Style nav links */
a[data-testid="stPageLink-NavLink"] {
    border-radius: 6px !important;
    padding: 8px 12px !important;
    margin: 2px 0 !important;
    transition: background 0.15s ease !important;
    text-decoration: none !important;
}
a[data-testid="stPageLink-NavLink"]:hover {
    background: rgba(34,211,238,0.06) !important;
}
a[data-testid="stPageLink-NavLink"][aria-current="page"] {
    background: rgba(34,211,238,0.08) !important;
    border-left: 2px solid var(--cyan) !important;
}
a[data-testid="stPageLink-NavLink"][aria-current="page"] p {
    color: var(--cyan) !important;
    font-weight: 700 !important;
}

/* ══════════ SIDEBAR BRAND ══════════ */
.sidebar-brand {
    padding: 0.75rem 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 0.5rem;
}
.sidebar-brand-name {
    font-family: 'IBM Plex Mono', sans-serif !important;
    font-size: 15px;
    font-weight: 800;
    color: #fff !important;
    letter-spacing: -0.3px;
}
.sidebar-brand-name span { color: var(--cyan) !important; }
.sidebar-brand-sub {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 9px;
    color: var(--text-muted) !important;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-top: 3px;
}

/* ══════════ PAGE HEADER ══════════ */
.page-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 1.25rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid var(--border);
}
.page-title {
    font-family: 'IBM Plex Mono', sans-serif !important;
    font-size: 22px;
    font-weight: 800;
    color: var(--text-primary);
    letter-spacing: -0.5px;
    margin: 0;
}
.page-subtitle {
    font-size: 12px;
    color: var(--text-muted);
    margin-top: 3px;
    font-weight: 500;
}

/* ══════════ KPI CARDS ══════════ */
.kpi-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.1rem 1.2rem 1rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s ease, background 0.2s ease;
}
.kpi-card:hover {
    background: var(--bg-card-hover);
    border-color: #243040;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
}
.kpi-card.blue::before   { background: var(--blue); }
.kpi-card.cyan::before   { background: var(--cyan); }
.kpi-card.red::before    { background: var(--red); }
.kpi-card.green::before  { background: var(--green); }
.kpi-card.orange::before { background: var(--amber); }

.kpi-label {
    font-family: 'IBM Plex Mono', sans-serif !important;
    font-size: 10px;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-bottom: 8px;
}
.kpi-value {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 28px;
    font-weight: 600;
    color: var(--text-primary);
    line-height: 1;
    margin-bottom: 6px;
    letter-spacing: -0.5px;
}
.kpi-delta {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 11px;
    color: var(--text-muted);
    font-weight: 400;
}
.kpi-delta.up { color: var(--green); }
.kpi-delta.down { color: var(--red); }

/* ══════════ SECTION TITLES ══════════ */
.section-title {
    font-family: 'IBM Plex Mono', sans-serif !important;
    font-size: 10px;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin: 1.5rem 0 0.6rem;
    display: flex;
    align-items: center;
    gap: 10px;
}
.section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
}

/* ══════════ BADGES ══════════ */
.badge {
    display: inline-flex;
    align-items: center;
    padding: 2px 7px;
    border-radius: 3px;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 9px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border: 1px solid transparent;
}
.badge-critical { background: rgba(239,68,68,0.1); color: var(--red); border-color: rgba(239,68,68,0.2); }
.badge-high { background: rgba(245,158,11,0.1); color: var(--amber); border-color: rgba(245,158,11,0.2); }
.badge-medium { background: rgba(234,179,8,0.08); color: var(--yellow); border-color: rgba(234,179,8,0.15); }
.badge-low { background: rgba(16,185,129,0.1); color: var(--green); border-color: rgba(16,185,129,0.2); }
.badge-confirmée { background: rgba(239,68,68,0.1); color: var(--red); border-color: rgba(239,68,68,0.2); }
.badge-suspicion { background: rgba(245,158,11,0.1); color: var(--amber); border-color: rgba(245,158,11,0.2); }
.badge-actif, .badge-active { background: rgba(16,185,129,0.1); color: var(--green); border-color: rgba(16,185,129,0.2); }
.badge-error, .badge-erreur { background: rgba(239,68,68,0.1); color: var(--red); border-color: rgba(239,68,68,0.2); }
.badge-inactive, .badge-inactif { background: rgba(100,116,139,0.08); color: var(--gray); border-color: rgba(100,116,139,0.12); }

/* ══════════ STATUS DOTS ══════════ */
.status-dot {
    display: inline-block;
    width: 7px; height: 7px;
    border-radius: 50%;
    margin-right: 5px;
}
.dot-green { background: var(--green); box-shadow: 0 0 0 2px rgba(16,185,129,0.15), 0 0 6px rgba(16,185,129,0.25); }
.dot-red { background: var(--red); box-shadow: 0 0 0 2px rgba(239,68,68,0.15), 0 0 6px rgba(239,68,68,0.25); }
.dot-gray { background: #475569; }

/* ══════════ ALERT ROWS ══════════ */
.alert-row {
    display: flex;
    align-items: flex-start;
    gap: 14px;
    padding: 10px 12px;
    border-radius: 6px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    margin-bottom: 4px;
    transition: background 0.15s ease;
}
.alert-row:hover { background: var(--bg-card-hover); }
.alert-title { font-family: 'IBM Plex Mono', sans-serif !important; font-weight: 600; font-size: 13px; color: var(--text-primary); }
.alert-meta { font-size: 11px; color: var(--text-muted); margin-top: 3px; }

/* ══════════ METRIC INLINE ══════════ */
.metric-inline {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 9px 12px;
    border-radius: 6px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    margin-bottom: 3px;
    font-size: 13px;
    transition: background 0.15s ease;
}
.metric-inline:hover { background: var(--bg-card-hover); }

/* ══════════ STREAMLIT OVERRIDES ══════════ */
.stMetric { display: none !important; }
.stMarkdown p, .stMarkdown li { color: var(--text-secondary); }
.stMarkdown a { color: var(--cyan); }
.stMarkdown hr { border-color: var(--border) !important; }

div[data-testid="stSelectbox"] > div > div,
div[data-testid="stMultiSelect"] > div > div {
    background: var(--bg-input) !important;
    border-color: var(--border) !important;
    color: var(--text-primary) !important;
    border-radius: 6px !important;
}

.stButton button {
    background: var(--bg-card) !important;
    color: var(--text-secondary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    transition: all 0.15s ease !important;
}
.stButton button:hover {
    background: rgba(34,211,238,0.06) !important;
    border-color: rgba(34,211,238,0.25) !important;
    color: var(--cyan) !important;
}

.stDownloadButton button {
    background: var(--bg-card) !important;
    color: var(--text-secondary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    font-size: 11px !important;
    font-weight: 600 !important;
}
.stDownloadButton button:hover {
    border-color: rgba(34,211,238,0.25) !important;
    color: var(--cyan) !important;
}

div[data-testid="stAlert"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-secondary) !important;
    border-radius: 6px !important;
}

.footer-text {
    text-align: center;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 9px;
    color: var(--text-muted);
    letter-spacing: 1px;
    text-transform: uppercase;
    padding: 0.75rem 0;
}
</style>
"""

LIGHT_CSS = DARK_CSS

PLOTLY_LAYOUT = dict(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(family='IBM Plex Mono, sans-serif', color='#8494a7', size=12),
    margin=dict(l=10, r=10, t=30, b=10),
    hoverlabel=dict(
        bgcolor='#0f151e',
        font=dict(family='IBM Plex Mono, sans-serif', color='#e4e9f0', size=12),
        bordercolor='#1a2332'
    ),
    xaxis=dict(
        showgrid=True, gridwidth=1, gridcolor='rgba(26,35,50,0.5)',
        showline=True, linewidth=1, linecolor='#1a2332',
        tickfont=dict(size=10, family='IBM Plex Mono, monospace', color='#4d5f73'),
        zeroline=False,
    ),
    yaxis=dict(
        showgrid=True, gridwidth=1, gridcolor='rgba(26,35,50,0.5)',
        showline=False,
        tickfont=dict(size=10, family='IBM Plex Mono, monospace', color='#4d5f73'),
        zeroline=False,
    ),
)

COLORS = {
    'cyan':    '#22d3ee',
    'blue':    '#3b82f6',
    'red':     '#ef4444',
    'green':   '#10b981',
    'orange':  '#f59e0b',
    'yellow':  '#eab308',
    'rose':    '#f43f5e',
    'gray':    '#64748b',
    'white':   '#e4e9f0',
    'cyan_fill':   'rgba(34,211,238,0.06)',
    'blue_fill':   'rgba(59,130,246,0.06)',
    'red_fill':    'rgba(239,68,68,0.06)',
    'green_fill':  'rgba(16,185,129,0.06)',
    'amber_fill':  'rgba(245,158,11,0.06)',
}

def sidebar_brand():
    return """
    <div class="sidebar-brand">
        <div class="sidebar-brand-name">🛡 Robust<span>-Scraper</span></div>
        <div class="sidebar-brand-sub">ANSSI Burkina Faso</div>
    </div>
    """