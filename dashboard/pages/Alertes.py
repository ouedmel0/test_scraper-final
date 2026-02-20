#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Page — Alertes & Fuites
Robust-Scraper Dashboard · ANSSI Burkina Faso
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

st.set_page_config(
    page_title="Alertes | Robust-Scraper",
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
    from utils.mock_data import get_recent_alerts, get_stats
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

    filtre_statut = st.selectbox("Statut", ["Tous", "Fuites confirmées", "Suspicions"])
    filtre_sev = st.multiselect("Sévérité", ["critical", "high", "medium", "low"],
                                 default=["critical", "high", "medium", "low"])
    filtre_score = st.slider("Score minimum", 0.0, 1.0, 0.3, step=0.05, format="%.2f")

    st.markdown("---")
    if st.button("↻  Actualiser", use_container_width=True):
        st.rerun()
    if USE_MOCK:
        st.markdown('<div style="font-size:10px;color:#556677;margin-top:8px">⚠ Mode démonstration</div>', unsafe_allow_html=True)

# ─── DONNÉES ───────────────────────────────────────────────────────────────────
if USE_MOCK:
    alerts_df = get_recent_alerts()
    stats = get_stats()
else:
    alerts_df = mongo.get_leaks_dataframe(limit=100)
    stats = mongo.get_stats()

# Filtres
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
    (k3, "cyan",   "RÉSULTATS FILTRÉS",  f"{len(df):,}", f"sur {len(alerts_df)} au total"),
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
    fig1.add_trace(go.Pie(
        labels=['Confirmées', 'Suspicions'],
        values=[len(confirmed), len(suspicions)],
        marker=dict(colors=[COLORS['red'], COLORS['orange']],
                    line=dict(color='#06090f', width=3)),
        hole=0.55,
        textfont=dict(size=11, family='Satoshi', color='#e8edf3'),
        textinfo='percent+label',
    ))
    layout1 = PLOTLY_LAYOUT.copy()
    layout1.update(height=260, showlegend=False, margin=dict(l=0, r=0, t=10, b=10))
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
        textfont=dict(size=11, family='JetBrains Mono', color='#8899aa')
    ))
    layout2 = PLOTLY_LAYOUT.copy()
    layout2.update(height=260, showlegend=False, margin=dict(l=0, r=0, t=30, b=0))
    fig2.update_layout(**layout2)
    st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

# ─── LISTE DES ALERTES ─────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">Liste des alertes ({len(df)} résultats)</div>', unsafe_allow_html=True)

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

if len(df) == 0:
    st.info("Aucune alerte ne correspond aux filtres sélectionnés.")
else:
    # Table header
    st.markdown("""
    <div style="display:grid;grid-template-columns:1fr 80px 80px 90px 80px 100px;
                gap:8px;padding:10px 14px;background:#0c1219;border-radius:8px 8px 0 0;
                border:1px solid #1c2633;font-size:10px;font-weight:700;
                text-transform:uppercase;letter-spacing:1px;color:#556677;margin-bottom:0">
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

        # Row highlight for critical
        bg = 'rgba(239,68,68,0.04)' if sev == 'critical' else ('rgba(245,158,11,0.03)' if sev == 'high' else '#111920')
        border_left = f'border-left:2px solid {COLORS["red"]};' if sev == 'critical' else ''

        st.markdown(f"""
        <div style="display:grid;grid-template-columns:1fr 80px 80px 90px 80px 100px;
                    gap:8px;padding:10px 14px;background:{bg};
                    border:1px solid #1c2633;border-top:none;{border_left}
                    font-size:13px;align-items:center">
            <div>
                <div style="font-weight:600;color:#e8edf3;font-size:12px">{titre}</div>
                <div style="font-size:10px;color:#556677;margin-top:2px">{source}</div>
            </div>
            <div style="text-align:center"><span class="badge badge-{statut}">{statut}</span></div>
            <div style="text-align:center"><span class="badge badge-{sev}">{sev}</span></div>
            <div style="font-size:11px;color:#8899aa">{categorie}</div>
            <div style="font-family:'JetBrains Mono',monospace;font-weight:600;
                        text-align:right;color:{COLORS['red'] if score >= 0.9 else '#e8edf3'};font-size:12px">{score:.0%}</div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:10px;
                        color:#556677;text-align:right">{date_str}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div class="footer-text">Robust-Scraper · ANSSI Burkina Faso · Surveillance Dark Web</div>', unsafe_allow_html=True)