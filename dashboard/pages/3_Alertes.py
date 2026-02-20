#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Page 3 — Alertes & Fuites
Robust-Scraper Dashboard · ANSSI Burkina Faso
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

st.set_page_config(
    page_title="Alertes | Robust-Scraper",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

from utils.theme import LIGHT_CSS, PLOTLY_LAYOUT, COLORS, sidebar_brand

try:
    from utils.mongo_client import DashboardMongoClient
    mongo = DashboardMongoClient()
    USE_MOCK = False
except Exception:
    from utils.mock_data import get_recent_alerts, get_stats
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

    st.markdown('<div style="font-size:10px;text-transform:uppercase;letter-spacing:0.8px;color:#4a6a8a;margin-bottom:8px">Filtres</div>', unsafe_allow_html=True)
    filtre_statut = st.selectbox("Statut", ["Tous", "Fuites confirmées", "Suspicions"])
    filtre_sev = st.multiselect("Sévérité", ["critical", "high", "medium", "low"],
                                 default=["critical", "high", "medium", "low"])
    filtre_score = st.slider("Score minimum", 0.0, 1.0, 0.3, step=0.05,
                              format="%.2f")
    st.markdown("---")
    if st.button("↻  Actualiser", use_container_width=True):
        st.rerun()
    if USE_MOCK:
        st.markdown('<div style="font-size:11px;color:#4a6a8a;margin-top:8px">⚠ Mode démonstration</div>', unsafe_allow_html=True)

# ─── DONNÉES ───────────────────────────────────────────────────────────────────
if USE_MOCK:
    alerts_df = get_recent_alerts()
    stats = get_stats()
else:
    alerts_df = mongo.get_leaks_dataframe(limit=100)
    stats = mongo.get_stats()

# Appliquer filtres
df = alerts_df.copy()
if filtre_statut == "Fuites confirmées":
    df = df[df['statut'] == 'confirmée']
elif filtre_statut == "Suspicions":
    df = df[df['statut'] == 'suspicion']
if filtre_sev:
    df = df[df['sévérité'].isin(filtre_sev)]
df = df[df['score'] >= filtre_score]

confirmed = alerts_df[alerts_df['statut'] == 'confirmée']
suspicions = alerts_df[alerts_df['statut'] == 'suspicion']
critical_all = alerts_df[alerts_df['sévérité'] == 'critical']

# ─── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <div>
        <div class="page-title">Alertes & Fuites de données</div>
        <div class="page-subtitle">Fuites confirmées et suspicions — Burkina Faso</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── KPIs ──────────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)

for col, color, label, value, delta in [
    (k1, "red",    "FUITES CONFIRMÉES",  f"{len(confirmed):,}", f"{len(confirmed[confirmed['sévérité']=='critical'])} critiques"),
    (k2, "orange", "SUSPICIONS",         f"{len(suspicions):,}", "à investiguer"),
    (k3, "blue",   "RÉSULTATS FILTRÉS",  f"{len(df):,}", f"sur {len(alerts_df)} au total"),
    (k4, "green",  "SCORE MOY.",         f"{df['score'].mean():.0%}" if len(df) > 0 else "—", "confiance IA"),
]:
    with col:
        st.markdown(f"""
        <div class="kpi-card {color}">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-delta">{delta}</div>
        </div>
        """, unsafe_allow_html=True)

# ─── GRAPHIQUES ────────────────────────────────────────────────────────────────
c1, c2 = st.columns([1, 1])

with c1:
    st.markdown('<div class="section-title">Fuites confirmées vs suspicions</div>', unsafe_allow_html=True)
    fig1 = go.Figure()
    statut_counts = alerts_df['statut'].value_counts()
    fig1.add_trace(go.Pie(
        labels=['Confirmées', 'Suspicions'],
        values=[len(confirmed), len(suspicions)],
        marker=dict(colors=[COLORS['red'], COLORS['orange']],
                    line=dict(color='white', width=3)),
        hole=0.5,
        textfont=dict(size=12, family='Outfit'),
        textinfo='percent+label',
    ))
    layout1 = PLOTLY_LAYOUT.copy()
    layout1.update(height=240, showlegend=False, margin=dict(l=0, r=0, t=10, b=10))
    fig1.update_layout(**layout1)
    st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})

with c2:
    st.markdown('<div class="section-title">Sévérité des alertes</div>', unsafe_allow_html=True)
    sev_counts = alerts_df['sévérité'].value_counts()
    sev_colors_map = {'critical': COLORS['red'], 'high': COLORS['orange'],
                       'medium': COLORS['yellow'], 'low': COLORS['green']}
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=sev_counts.index,
        y=sev_counts.values,
        marker=dict(color=[sev_colors_map.get(s, COLORS['gray']) for s in sev_counts.index],
                    opacity=0.85, line=dict(width=0)),
        text=sev_counts.values,
        textposition='outside',
        textfont=dict(size=11, family='Space Mono')
    ))
    layout2 = PLOTLY_LAYOUT.copy()
    layout2.update(height=240, showlegend=False, margin=dict(l=0, r=0, t=30, b=0))
    fig2.update_layout(**layout2)
    st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

# ─── LISTE DES ALERTES ─────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">Liste des alertes ({len(df)} résultats)</div>', unsafe_allow_html=True)

# Export
col_exp1, col_exp2 = st.columns([6, 1])
with col_exp2:
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "⬇ Export CSV",
        data=csv,
        file_name=f"alertes_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime='text/csv',
        use_container_width=True
    )

# Tableau des alertes
if len(df) == 0:
    st.info("Aucune alerte ne correspond aux filtres sélectionnés.")
else:
    # Header
    st.markdown("""
    <div style="display:grid;grid-template-columns:1fr 80px 80px 90px 80px 100px;
                gap:8px;padding:8px 12px;background:#f8fafc;border-radius:6px 6px 0 0;
                border:1px solid #e2e8f0;font-size:10px;font-weight:700;
                text-transform:uppercase;letter-spacing:0.7px;color:#8a9ab0;margin-bottom:0">
        <div>Titre</div>
        <div style="text-align:center">Statut</div>
        <div style="text-align:center">Sévérité</div>
        <div>Catégorie</div>
        <div style="text-align:right">Score</div>
        <div style="text-align:right">Détecté</div>
    </div>
    """, unsafe_allow_html=True)

    for i, row in df.iterrows():
        sev = row.get('sévérité', 'medium')
        statut = row.get('statut', '')
        score = row.get('score', 0)
        titre = row.get('titre', row.get('title', 'Sans titre'))
        source = row.get('source', '')
        date = row.get('détecté_le', '')
        categorie = row.get('catégorie', row.get('bert_category', ''))
        date_str = date.strftime("%d/%m %H:%M") if hasattr(date, 'strftime') else str(date)[:16]

        # Couleur ligne selon sévérité
        bg = '#fff5f5' if sev == 'critical' else ('#fff8f0' if sev == 'high' else 'white')

        st.markdown(f"""
        <div style="display:grid;grid-template-columns:1fr 80px 80px 90px 80px 100px;
                    gap:8px;padding:10px 12px;background:{bg};
                    border:1px solid #e2e8f0;border-top:none;
                    font-size:13px;align-items:center">
            <div>
                <div style="font-weight:500;color:#0d1b2a">{titre}</div>
                <div style="font-size:11px;color:#8a9ab0;margin-top:2px">{source}</div>
            </div>
            <div style="text-align:center"><span class="badge badge-{statut}">{statut}</span></div>
            <div style="text-align:center"><span class="badge badge-{sev}">{sev}</span></div>
            <div style="font-size:12px;color:#5a6a7a">{categorie}</div>
            <div style="font-family:'Space Mono',monospace;font-weight:700;
                        text-align:right;color:{'#e02424' if score >= 0.9 else '#0d1b2a'}">{score:.0%}</div>
            <div style="font-family:'Space Mono',monospace;font-size:11px;
                        color:#8a9ab0;text-align:right">{date_str}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div style="text-align:center;font-size:11px;color:#8a9ab0">Robust-Scraper · ANSSI Burkina Faso · Surveillance Dark Web</div>', unsafe_allow_html=True)