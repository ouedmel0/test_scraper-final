#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robust-Scraper Dashboard — Page principale
ANSSI Burkina Faso
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import sys, os
sys.path.append(os.path.dirname(__file__))

# ─── CONFIG ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Robust-Scraper | ANSSI",
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

# Connexion MongoDB ou mock
try:
    from utils.mongo_client import DashboardMongoClient
    mongo = DashboardMongoClient()
    USE_MOCK = False
except Exception:
    from utils.mock_data import (
        get_stats, get_leaks_timeline, get_leaks_by_category,
        get_leaks_by_severity, get_recent_alerts
    )
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
    st.markdown('<div style="font-size:10px;text-transform:uppercase;letter-spacing:1.2px;color:#556677;margin-bottom:8px;font-weight:600">Filtres</div>', unsafe_allow_html=True)

    time_range = st.selectbox("Période", ["24 heures", "7 jours", "30 jours"], index=1)
    min_score = st.slider("Score minimum", 0, 100, 30)

    st.markdown("---")
    if st.button("↻  Actualiser", use_container_width=True):
        st.rerun()

    if USE_MOCK:
        st.markdown('<div style="font-size:10px;color:#556677;margin-top:8px">⚠ Mode démonstration</div>', unsafe_allow_html=True)

    st.markdown(f'<div style="font-size:10px;color:#556677;margin-top:1.5rem;font-family:JetBrains Mono,monospace">v2.1.0 · {datetime.now().strftime("%Y")}</div>', unsafe_allow_html=True)

# ─── DONNÉES ───────────────────────────────────────────────────────────────────
if USE_MOCK:
    stats = get_stats()
    timeline_df = get_leaks_timeline(days=7)
    category_df = get_leaks_by_category()
    severity_df = get_leaks_by_severity()
    alerts_df = get_recent_alerts()
else:
    stats = mongo.get_stats()
    timeline_df = mongo.get_leaks_timeline(days=7)
    category_df = mongo.get_leaks_by_category()
    severity_df = mongo.get_leaks_by_severity()
    alerts_df = mongo.get_leaks_dataframe(limit=5)

# ─── HEADER ────────────────────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("""
    <div class="page-header">
        <div>
            <div class="page-title">Vue d'ensemble</div>
            <div class="page-subtitle">Surveillance Dark Web — Burkina Faso</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
with col_h2:
    st.markdown(f"""
    <div style="text-align:right;padding-top:8px">
        <div style="font-size:11px;color:#8899aa">
            <span class="status-dot dot-green"></span>Système opérationnel
        </div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:#556677;margin-top:4px">
            {datetime.now().strftime("%d/%m/%Y %H:%M")}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─── KPIs ──────────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)

kpis = [
    (k1, "cyan", "TOTAL DÉTECTIONS", f"{stats['total_leaks']:,}", f"↑ +{stats['recent_leaks']} dernières 24h", "up"),
    (k2, "red", "BURKINA FASO", f"{stats['bf_leaks']:,}", f"{stats['bf_percentage']:.1f}% du total", ""),
    (k3, "orange", "NIVEAU CRITIQUE", f"{stats['critical_leaks']:,}", "nécessitent action immédiate", "down"),
    (k4, "green", "CLASSIFIÉS IA", f"{stats['bert_classified']:,}", f"{(stats['bert_classified']/stats['total_leaks']*100):.0f}% du total" if stats['total_leaks'] > 0 else "0% du total", ""),
]

for col, color, label, value, delta, delta_class in kpis:
    with col:
        st.markdown(f"""
        <div class="kpi-card {color}">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-delta {delta_class}">{delta}</div>
        </div>
        """, unsafe_allow_html=True)

# ─── TIMELINE ──────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Évolution des détections (7 jours)</div>', unsafe_allow_html=True)

with st.container():
    fig = go.Figure()
    for col_name, color, name in [
        ('total', COLORS['cyan'], 'Total'),
        ('bf_related', COLORS['green'], 'Burkina Faso'),
        ('critical', COLORS['red'], 'Critiques'),
    ]:
        fig.add_trace(go.Scatter(
            x=timeline_df['date'], y=timeline_df[col_name],
            name=name, mode='lines+markers',
            line=dict(color=color, width=2),
            marker=dict(size=5, color=color),
            fill='tozeroy' if col_name == 'total' else None,
            fillcolor=COLORS['cyan_fill'] if col_name == 'total' else None,
        ))

    layout = PLOTLY_LAYOUT.copy()
    layout.update(height=300, legend=dict(
        orientation="h", yanchor="top", y=1.15, xanchor="right", x=1,
        font=dict(size=11, color='#8899aa'), bgcolor='rgba(0,0,0,0)'
    ), hovermode='x unified')
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# ─── GRAPHIQUES ────────────────────────────────────────────────────────────────
c1, c2 = st.columns(2)

with c1:
    st.markdown('<div class="section-title">Par catégorie</div>', unsafe_allow_html=True)
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        y=category_df['category'],
        x=category_df['count'],
        orientation='h',
        marker=dict(color=COLORS['blue'], opacity=0.85, line=dict(width=0)),
        text=category_df['count'],
        textposition='outside',
        textfont=dict(size=11, family='JetBrains Mono', color='#8899aa')
    ))
    layout2 = PLOTLY_LAYOUT.copy()
    layout2.update(height=280, showlegend=False,
                   xaxis=dict(**PLOTLY_LAYOUT['xaxis'], title=None),
                   yaxis=dict(showgrid=False, tickfont=dict(size=11, color='#8899aa')))
    fig2.update_layout(**layout2)
    st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

with c2:
    st.markdown('<div class="section-title">Par sévérité</div>', unsafe_allow_html=True)
    severity_colors = {
        'critical': COLORS['red'], 'high': COLORS['orange'],
        'medium': COLORS['yellow'], 'low': COLORS['green']
    }
    fig3 = go.Figure()
    fig3.add_trace(go.Pie(
        labels=severity_df['severity'],
        values=severity_df['count'],
        marker=dict(
            colors=[severity_colors.get(s, COLORS['gray']) for s in severity_df['severity']],
            line=dict(color='#06090f', width=3)
        ),
        hole=0.55,
        textfont=dict(size=11, family='Satoshi', color='#e8edf3'),
        textinfo='percent+label',
    ))
    layout3 = PLOTLY_LAYOUT.copy()
    layout3.update(height=280, showlegend=False,
                   margin=dict(l=0, r=0, t=10, b=10))
    fig3.update_layout(**layout3)
    st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})

# ─── ALERTES RÉCENTES ──────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Alertes récentes</div>', unsafe_allow_html=True)

recent = alerts_df[alerts_df['statut'] == 'confirmée'].head(5) if 'statut' in alerts_df.columns else alerts_df.head(5)

for _, row in recent.iterrows():
    sev = row.get('sévérité', 'medium')
    statut = row.get('statut', '')
    score = row.get('score', 0)
    titre = row.get('titre', row.get('title', 'Sans titre'))
    source = row.get('source', '')
    date = row.get('détecté_le', row.get('timestamp', ''))
    categorie = row.get('catégorie', row.get('bert_category', ''))
    date_str = date.strftime("%d/%m %H:%M") if hasattr(date, 'strftime') else str(date)[:16]

    st.markdown(f"""
    <div class="alert-row">
        <div style="flex:1">
            <div class="alert-title">{titre}</div>
            <div class="alert-meta">
                <span class="badge badge-{sev}">{sev}</span>&nbsp;
                <span class="badge badge-{statut}">{statut}</span>&nbsp;&nbsp;
                {source} · {categorie} · {date_str}
            </div>
        </div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:600;color:{COLORS['cyan'] if score >= 0.8 else '#e8edf3'};white-space:nowrap">
            {score:.0%}
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div class="footer-text">Robust-Scraper · ANSSI Burkina Faso · Surveillance Dark Web</div>', unsafe_allow_html=True)