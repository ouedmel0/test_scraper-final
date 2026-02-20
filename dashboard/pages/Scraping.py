#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Page — Performances du Scraping
Robust-Scraper Dashboard · ANSSI Burkina Faso
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

st.set_page_config(
    page_title="Scraping | Robust-Scraper",
    page_icon="🛡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
[data-testid="stSidebarNav"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

from utils.theme import LIGHT_CSS, PLOTLY_LAYOUT, COLORS, sidebar_brand

try:
    from utils.mongo_client import DashboardMongoClient
    mongo = DashboardMongoClient()
    USE_MOCK = False
except Exception:
    from utils.mock_data import get_stats, get_scraping_performance, get_sources_status
    USE_MOCK = True

st.markdown(LIGHT_CSS, unsafe_allow_html=True)

# ─── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(sidebar_brand(), unsafe_allow_html=True)
    st.markdown("---")

    st.page_link("app.py", label="◈  Vue d'ensemble")
    st.page_link("pages/Alertes.py", label="◈  Alertes & Fuites")
    st.page_link("pages/Scraping.py", label="◈  Performances Scraping")
    st.page_link("pages/Ia.py", label="◈  Performances IA")

    st.markdown("---")
    if st.button("↻  Actualiser", use_container_width=True):
        st.rerun()
    if USE_MOCK:
        st.markdown('<div style="font-size:10px;color:#556677;margin-top:8px">⚠ Mode démonstration</div>', unsafe_allow_html=True)

# ─── DONNÉES ───────────────────────────────────────────────────────────────────
if USE_MOCK:
    stats = get_stats()
    perf_df = get_scraping_performance()
    sources_df = get_sources_status()
else:
    stats = mongo.get_stats()
    perf_df = mongo.get_scraping_performance()
    sources_df = mongo.get_sources_status()

# ─── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <div>
        <div class="page-title">Performances du Scraping</div>
        <div class="page-subtitle">Activité des collecteurs Dark Web · dernières 24h</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── KPIs SCRAPING ─────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)

total_pages = int(perf_df['pages_scrapées'].sum())
total_errors = int(perf_df['erreurs'].sum())
avg_time = int(perf_df['temps_moyen_ms'].mean())
error_rate = (total_errors / total_pages * 100) if total_pages > 0 else 0
sources_actives = len(sources_df[sources_df['statut'] == 'actif']) if 'statut' in sources_df.columns else 0

for col, color, label, value, delta, delta_class in [
    (k1, "cyan", "PAGES COLLECTÉES", f"{total_pages:,}", f"sur {stats['sources_monitored']} sources", ""),
    (k2, "green", "SOURCES ACTIVES", f"{sources_actives}/{len(sources_df)}", "opérationnelles", "up"),
    (k3, "red", "TAUX D'ERREUR", f"{error_rate:.1f}%", f"{total_errors} erreurs totales", "down" if error_rate > 5 else ""),
    (k4, "orange", "TEMPS MOYEN", f"{avg_time}ms", "par requête", ""),
]:
    with col:
        st.markdown(f"""
        <div class="kpi-card {color}">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-delta {delta_class}">{delta}</div>
        </div>
        """, unsafe_allow_html=True)

# ─── GRAPHIQUES ACTIVITÉ ───────────────────────────────────────────────────────
st.markdown('<div class="section-title">Activité horaire</div>', unsafe_allow_html=True)

fig = make_subplots(
    rows=2, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.08,
    row_heights=[0.65, 0.35]
)

fig.add_trace(go.Bar(
    x=perf_df['heure'],
    y=perf_df['pages_scrapées'],
    name="Pages collectées",
    marker=dict(color=COLORS['blue'], opacity=0.7, line=dict(width=0)),
), row=1, col=1)

fig.add_trace(go.Scatter(
    x=perf_df['heure'],
    y=perf_df['temps_moyen_ms'],
    name="Temps moyen (ms)",
    mode='lines',
    line=dict(color=COLORS['orange'], width=2),
    fill='tozeroy',
    fillcolor=COLORS['amber_fill']
), row=2, col=1)

fig.add_trace(go.Scatter(
    x=perf_df['heure'],
    y=perf_df['erreurs'],
    name="Erreurs",
    mode='lines+markers',
    line=dict(color=COLORS['red'], width=1.5, dash='dot'),
    marker=dict(size=4, color=COLORS['red'])
), row=1, col=1)

fig.update_layout(
    height=400,
    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Satoshi, sans-serif', color='#8899aa', size=12),
    margin=dict(l=10, r=10, t=20, b=10),
    legend=dict(orientation="h", yanchor="top", y=1.08, xanchor="right", x=1,
                bgcolor='rgba(0,0,0,0)', font=dict(size=11, color='#8899aa')),
    hovermode='x unified',
    hoverlabel=dict(bgcolor='#111920', font=dict(family='Satoshi', color='#e8edf3', size=12), bordercolor='#1c2633')
)
fig.update_xaxes(showgrid=True, gridcolor='rgba(28,38,51,0.6)', linecolor='#1c2633',
                 tickfont=dict(size=10, family='JetBrains Mono', color='#556677'))
fig.update_yaxes(showgrid=True, gridcolor='rgba(28,38,51,0.6)', linecolor='#1c2633',
                 tickfont=dict(size=10, family='JetBrains Mono', color='#556677'))
fig.update_yaxes(title_text="Pages / Erreurs", row=1, col=1, title_font=dict(size=10, color='#556677'))
fig.update_yaxes(title_text="Temps (ms)", row=2, col=1, title_font=dict(size=10, color='#556677'))

st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# ─── STATUT DES SOURCES ────────────────────────────────────────────────────────
st.markdown('<div class="section-title">État des sources</div>', unsafe_allow_html=True)

for _, row in sources_df.iterrows():
    statut = row.get('statut', 'inactif')
    dot = 'dot-green' if statut == 'actif' else ('dot-red' if statut == 'erreur' else 'dot-gray')
    badge = 'badge-active' if statut == 'actif' else ('badge-error' if statut == 'erreur' else 'badge-inactive')
    derniere = row.get('dernière_collecte', '')
    derniere_str = derniere.strftime("%H:%M") if hasattr(derniere, 'strftime') else str(derniere)[:5]
    docs = row.get('docs_collectés', 0)
    taux = row.get('taux_succès', '—')
    source = row.get('source', '')

    st.markdown(f"""
    <div class="metric-inline">
        <div style="display:flex;align-items:center;gap:10px;min-width:180px">
            <span class="status-dot {dot}"></span>
            <span style="font-weight:600;font-size:13px;color:#e8edf3">{source}</span>
        </div>
        <span class="badge {badge}">{statut}</span>
        <div style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#8899aa;text-align:right">
            {docs:,} docs
        </div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#556677;min-width:50px;text-align:right">
            {taux}
        </div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:#556677;min-width:60px;text-align:right">
            {derniere_str}
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div class="footer-text">Robust-Scraper · ANSSI Burkina Faso · Surveillance Dark Web</div>', unsafe_allow_html=True)