#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Page — Performances de l'IA (BERT)
Robust-Scraper Dashboard · ANSSI Burkina Faso
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

st.set_page_config(
    page_title="IA | Robust-Scraper",
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
    from utils.mock_data import get_stats, get_ai_performance, get_classification_distribution
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
    ai_df = get_ai_performance()
    distrib_df = get_classification_distribution()
else:
    stats = mongo.get_stats()
    ai_df = mongo.get_ai_performance()
    distrib_df = mongo.get_classification_distribution()

latest = ai_df.iloc[-1]

# ─── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <div>
        <div class="page-title">Performances de l'IA</div>
        <div class="page-subtitle">Modèle BERT · Classification des fuites · 14 derniers jours</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── KPIs IA ───────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)

total_classified = int(ai_df['docs_classifiés'].sum())
avg_precision = ai_df['précision'].mean()
avg_recall = ai_df['rappel'].mean()
avg_f1 = ai_df['f1_score'].mean()

for col, color, label, value, delta in [
    (k1, "cyan",   "PRÉCISION MOY.",   f"{avg_precision:.1%}", f"dernière: {latest['précision']:.1%}"),
    (k2, "green",  "RAPPEL MOY.",       f"{avg_recall:.1%}",   f"dernière: {latest['rappel']:.1%}"),
    (k3, "orange", "F1-SCORE MOY.",     f"{avg_f1:.1%}",       f"dernière: {latest['f1_score']:.1%}"),
    (k4, "red",    "DOCS CLASSIFIÉS",   f"{total_classified:,}", f"{stats.get('bert_classified', 0):,} au total"),
]:
    with col:
        st.markdown(f"""
        <div class="kpi-card {color}">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-delta">{delta}</div>
        </div>
        """, unsafe_allow_html=True)

# ─── MÉTRIQUES BERT ────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Évolution des métriques BERT (14 jours)</div>', unsafe_allow_html=True)

fig = go.Figure()
for col_name, color, name, dash in [
    ('précision', COLORS['cyan'], 'Précision', 'solid'),
    ('rappel', COLORS['green'], 'Rappel', 'solid'),
    ('f1_score', COLORS['orange'], 'F1-Score', 'dot'),
]:
    fig.add_trace(go.Scatter(
        x=ai_df['date'], y=ai_df[col_name],
        name=name, mode='lines+markers',
        line=dict(color=color, width=2, dash=dash),
        marker=dict(size=5, color=color),
    ))

# Zone cible
fig.add_hrect(y0=0.85, y1=1.0, fillcolor='rgba(16,185,129,0.04)',
              line_width=0, annotation_text="Zone cible (>85%)",
              annotation_position="bottom right",
              annotation_font=dict(size=10, color='#10b981'))

layout = PLOTLY_LAYOUT.copy()
layout.update(
    height=300,
    yaxis=dict(**PLOTLY_LAYOUT['yaxis'], tickformat='.0%', range=[0.75, 1.0]),
    legend=dict(orientation="h", yanchor="top", y=1.12, xanchor="right", x=1,
                bgcolor='rgba(0,0,0,0)', font=dict(size=11, color='#8899aa')),
    hovermode='x unified'
)
fig.update_layout(**layout)
st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# ─── DISTRIBUTION CLASSIFICATION ───────────────────────────────────────────────
c1, c2 = st.columns([1, 1])

label_colors = {
    'Fuite confirmée': COLORS['red'],
    'Suspicion fuite': COLORS['orange'],
    'Non pertinent': COLORS['gray'],
    'Ambigu': COLORS['yellow'],
}

with c1:
    st.markdown('<div class="section-title">Distribution des labels</div>', unsafe_allow_html=True)
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=distrib_df['label'],
        y=distrib_df['count'],
        marker=dict(
            color=[label_colors.get(l, COLORS['blue']) for l in distrib_df['label']],
            opacity=0.85, line=dict(width=0)
        ),
        text=distrib_df['count'],
        textposition='outside',
        textfont=dict(size=11, family='JetBrains Mono', color='#8899aa')
    ))
    layout2 = PLOTLY_LAYOUT.copy()
    layout2.update(height=260, showlegend=False,
                   margin=dict(l=0, r=10, t=30, b=0))
    fig2.update_layout(**layout2)
    st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

with c2:
    st.markdown('<div class="section-title">Confiance moyenne par label</div>', unsafe_allow_html=True)
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        y=distrib_df['label'],
        x=distrib_df['confiance_moy'],
        orientation='h',
        marker=dict(
            color=[label_colors.get(l, COLORS['blue']) for l in distrib_df['label']],
            opacity=0.85, line=dict(width=0)
        ),
        text=[f"{v:.0%}" for v in distrib_df['confiance_moy']],
        textposition='outside',
        textfont=dict(size=11, family='JetBrains Mono', color='#8899aa')
    ))
    layout3 = PLOTLY_LAYOUT.copy()
    layout3.update(
        height=260, showlegend=False,
        xaxis=dict(**PLOTLY_LAYOUT['xaxis'], tickformat='.0%', range=[0, 1.1]),
        yaxis=dict(showgrid=False, tickfont=dict(size=11, color='#8899aa')),
        margin=dict(l=0, r=60, t=30, b=0)
    )
    fig3.update_layout(**layout3)
    st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})

# ─── VOLUME ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Volume journalier classifié</div>', unsafe_allow_html=True)

fig4 = go.Figure()
fig4.add_trace(go.Bar(
    x=ai_df['date'],
    y=ai_df['docs_classifiés'],
    marker=dict(color=COLORS['blue'], opacity=0.6, line=dict(width=0)),
    name='Docs classifiés'
))
layout4 = PLOTLY_LAYOUT.copy()
layout4.update(height=200, showlegend=False, margin=dict(l=0, r=0, t=10, b=0))
fig4.update_layout(**layout4)
st.plotly_chart(fig4, use_container_width=True, config={'displayModeBar': False})

st.markdown("---")
st.markdown('<div class="footer-text">Robust-Scraper · ANSSI Burkina Faso · Surveillance Dark Web</div>', unsafe_allow_html=True)