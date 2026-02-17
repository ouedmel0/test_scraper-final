#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robust-Scraper — Performance du Scraping
"""

import streamlit as st
import pymongo
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ── Configuration ──────────────────────────────────────────────
st.set_page_config(
    page_title="Scraping | Robust-Scraper",
    page_icon="RS",
    layout="wide",
)

# ── Style (réutilisation du thème global) ──────────────────────
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #161B22 0%, #1C2333 100%);
        border: 1px solid #2D3348; border-radius: 10px; padding: 18px 20px;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.8rem !important; font-weight: 500; color: #8B949E !important;
        text-transform: uppercase; letter-spacing: 0.5px;
    }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: 700; color: #E6EDF3 !important; }
    h1 { font-weight: 700 !important; color: #E6EDF3 !important; }
    h2, h3 { font-weight: 600 !important; color: #C9D1D9 !important; }
    hr { border-color: #1E2130 !important; }
    .stButton > button {
        background: #1C2333; color: #C9D1D9; border: 1px solid #2D3348;
        border-radius: 8px; font-weight: 500; transition: all 0.2s ease;
    }
    .stButton > button:hover { background: #2D3348; border-color: #4A90D9; }
    .block-container { padding-top: 2rem; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ── Palette de couleurs ────────────────────────────────────────
COLORS = {
    "success": "#3FB950",
    "warning": "#D29922",
    "danger": "#F85149",
    "info": "#4A90D9",
    "muted": "#8B949E",
    "bg_card": "#161B22",
}

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#C9D1D9"),
    margin=dict(l=20, r=20, t=40, b=20),
)


# ── MongoDB ────────────────────────────────────────────────────
@st.cache_resource
def get_mongo_client():
    return pymongo.MongoClient("mongodb://admin:ChangeMe789@mongodb:27017/")


client = get_mongo_client()
db = client.robust_scraper


# ── Header ─────────────────────────────────────────────────────
st.markdown("# Performance du Scraping")
st.caption("Suivi en temps réel de la collecte de données sur le Dark Web")
st.markdown("---")


# ── Métriques principales ─────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

total = db.urls_to_scrape.count_documents({})
completed = db.urls_to_scrape.count_documents({"status": "completed"})
processing = db.urls_to_scrape.count_documents({"status": "processing"})
failed = db.urls_to_scrape.count_documents({"status": "failed"})

taux_succes = (completed / total * 100) if total > 0 else 0
taux_echec = (failed / total * 100) if total > 0 else 0

col1.metric("Total URLs", f"{total:,}")
col2.metric("Completees", f"{completed:,}", delta=f"{taux_succes:.1f}% succes")
col3.metric("En cours", f"{processing:,}")
col4.metric("Echecs", f"{failed:,}", delta=f"-{taux_echec:.1f}%", delta_color="inverse")

st.markdown("---")


# ── Graphiques ─────────────────────────────────────────────────
col_left, col_right = st.columns(2)

# — Répartition des statuts —
with col_left:
    st.markdown("### Repartition des statuts")

    data = pd.DataFrame({
        "Statut": ["Completees", "En cours", "Echecs"],
        "Nombre": [completed, processing, failed],
    })

    fig = px.pie(
        data,
        values="Nombre",
        names="Statut",
        hole=0.45,
        color="Statut",
        color_discrete_map={
            "Completees": COLORS["success"],
            "En cours": COLORS["warning"],
            "Echecs": COLORS["danger"],
        },
    )
    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_traces(
        textinfo="percent+value",
        textfont_size=12,
        marker=dict(line=dict(color="#0D1117", width=2)),
    )
    st.plotly_chart(fig, use_container_width=True)

# — Timeline (7 derniers jours) —
with col_right:
    st.markdown("### Activite — 7 derniers jours")

    pipeline = [
        {
            "$match": {
                "status": "completed",
                "completed_at": {"$gte": datetime.utcnow() - timedelta(days=7)},
            }
        },
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$completed_at"}},
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    timeline_data = list(db.urls_to_scrape.aggregate(pipeline))

    if timeline_data:
        df = pd.DataFrame(timeline_data)
        df.columns = ["Date", "URLs"]

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=df["Date"],
                y=df["URLs"],
                marker_color=COLORS["info"],
                marker_line_color=COLORS["info"],
                marker_line_width=0,
                opacity=0.85,
            )
        )
        fig.update_layout(
            **PLOTLY_LAYOUT,
            xaxis=dict(gridcolor="#1E2130", showgrid=False),
            yaxis=dict(gridcolor="#1E2130", gridwidth=0.5),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune donnee pour les 7 derniers jours.")

st.markdown("---")


# ── Taux de complétion par source ──────────────────────────────
st.markdown("### Performance par source")

pipeline = [
    {
        "$group": {
            "_id": {"source": "$source", "status": "$status"},
            "count": {"$sum": 1},
        }
    },
    {"$sort": {"_id.source": 1}},
]
source_data = list(db.urls_to_scrape.aggregate(pipeline))

if source_data:
    rows = []
    for item in source_data:
        rows.append({
            "Source": item["_id"].get("source", "N/A"),
            "Statut": item["_id"].get("status", "N/A"),
            "Nombre": item["count"],
        })
    df = pd.DataFrame(rows)

    fig = px.bar(
        df,
        x="Source",
        y="Nombre",
        color="Statut",
        barmode="stack",
        color_discrete_map={
            "completed": COLORS["success"],
            "processing": COLORS["warning"],
            "failed": COLORS["danger"],
            "pending": COLORS["muted"],
        },
    )
    fig.update_layout(
        **PLOTLY_LAYOUT,
        xaxis=dict(gridcolor="#1E2130", showgrid=False),
        yaxis=dict(gridcolor="#1E2130", gridwidth=0.5),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")


# ── Dernières URLs scrapées ────────────────────────────────────
st.markdown("### Dernieres URLs scrapees")

recent = list(
    db.urls_to_scrape.find(
        {"status": "completed"},
        {"url": 1, "source": 1, "worker_id": 1, "completed_at": 1, "_id": 0},
    )
    .sort("completed_at", -1)
    .limit(15)
)

if recent:
    df = pd.DataFrame(recent)
    if "completed_at" in df.columns:
        df["completed_at"] = pd.to_datetime(df["completed_at"]).dt.strftime("%d/%m/%Y %H:%M")
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("Aucune URL scrapee pour le moment.")


# ── Actions ────────────────────────────────────────────────────
st.markdown("---")
col1, col2, _ = st.columns([1, 1, 4])

with col1:
    if st.button("Actualiser"):
        st.rerun()

with col2:
    st.caption(f"Maj : {datetime.now().strftime('%H:%M:%S')}")