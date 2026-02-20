#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Page 1 — Performances du Scraping
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
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    st.page_link("app.py", label="Vue d'ensemble", icon="📊")
    st.page_link("pages/1_Scraping.py", label="Performances Scraping", icon="🌐")
    st.page_link("pages/2_IA.py", label="Performances IA", icon="🤖")
    st.page_link("pages/3_Alertes.py", label="Alertes & Fuites", icon="🚨")
    st.markdown("---")

    if st.button("↻  Actualiser", use_container_width=True):
        st.rerun()

    if USE_MOCK:
        st.markdown('<div style="font-size:11px;color:#4a6a8a;margin-top:8px">⚠ Mode démonstration</div>', unsafe_allow_html=True)

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
    (k1, "blue", "PAGES COLLECTÉES", f"{total_pages:,}", f"sur {stats['sources_monitored']} sources", ""),
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

# Pages scrapées
fig.add_trace(go.Bar(
    x=perf_df['heure'],
    y=perf_df['pages_scrapées'],
    name="Pages collectées",
    marker=dict(color=COLORS['blue'], opacity=0.8, line=dict(width=0)),
), row=1, col=1)

# Temps moyen
fig.add_trace(go.Scatter(
    x=perf_df['heure'],
    y=perf_df['temps_moyen_ms'],
    name="Temps moyen (ms)",
    mode='lines',
    line=dict(color=COLORS['orange'], width=2),
    fill='tozeroy',
    fillcolor='rgba(255,107,53,0.08)'
), row=2, col=1)

# Erreurs en overlay
fig.add_trace(go.Scatter(
    x=perf_df['heure'],
    y=perf_df['erreurs'],
    name="Erreurs",
    mode='lines+markers',
    line=dict(color=COLORS['red'], width=1.5, dash='dot'),
    marker=dict(size=4, color=COLORS['red'])
), row=1, col=1)

fig.update_layout(
    height=380,
    plot_bgcolor='white', paper_bgcolor='white',
    font=dict(family='Outfit', color='#5a6a7a', size=12),
    margin=dict(l=10, r=10, t=20, b=10),
    legend=dict(orientation="h", yanchor="top", y=1.08, xanchor="right", x=1,
                bgcolor='rgba(0,0,0,0)', font=dict(size=12)),
    hovermode='x unified',
    hoverlabel=dict(bgcolor='#0d1b2a', font=dict(family='Outfit', color='white', size=12))
)
fig.update_xaxes(showgrid=True, gridcolor='#f1f5f9', linecolor='#e2e8f0')
fig.update_yaxes(showgrid=True, gridcolor='#f1f5f9', linecolor='#e2e8f0')
fig.update_yaxes(title_text="Pages / Erreurs", row=1, col=1, title_font=dict(size=11))
fig.update_yaxes(title_text="Temps (ms)", row=2, col=1, title_font=dict(size=11))

st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# ─── STATUT DES SOURCES ────────────────────────────────────────────────────────
st.markdown('<div class="section-title">État des sources</div>', unsafe_allow_html=True)

for _, row in sources_df.iterrows():
    statut = row.get('statut', 'inactif')
    dot = 'dot-green' if statut == 'actif' else ('dot-red' if statut == 'erreur' else 'dot-gray')
    badge = f'badge-active' if statut == 'actif' else (f'badge-error' if statut == 'erreur' else 'badge-inactive')
    derniere = row.get('dernière_collecte', '')
    derniere_str = derniere.strftime("%H:%M") if hasattr(derniere, 'strftime') else str(derniere)[:5]
    docs = row.get('docs_collectés', 0)
    taux = row.get('taux_succès', '—')
    source = row.get('source', '')

    st.markdown(f"""
    <div class="metric-inline">
        <div style="display:flex;align-items:center;gap:10px;min-width:180px">
            <span class="status-dot {dot}"></span>
            <span style="font-weight:500;font-size:13px">{source}</span>
        </div>
        <span class="badge {badge}">{statut}</span>
        <div style="font-family:'Space Mono',monospace;font-size:12px;color:#5a6a7a;text-align:right">
            {docs:,} docs
        </div>
        <div style="font-family:'Space Mono',monospace;font-size:12px;color:#8a9ab0;min-width:50px;text-align:right">
            {taux}
        </div>
        <div style="font-size:11px;color:#8a9ab0;min-width:60px;text-align:right">
            {derniere_str}
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div style="text-align:center;font-size:11px;color:#8a9ab0">Robust-Scraper · ANSSI Burkina Faso · Surveillance Dark Web</div>', unsafe_allow_html=True)