#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robust-Scraper — Collecte
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.theme import get_db, inject_css, COLORS, PLOTLY_LAYOUT, AXIS_STYLE, AXIS_CLEAN

st.set_page_config(page_title="Collecte | Robust-Scraper", page_icon="RS", layout="wide")
inject_css()
db = get_db()

# ── Header ─────────────────────────────────────────────────────
st.markdown("# Collecte de donnees")
st.caption("Performance du scraping via Tor — URLs collectees et traitees")
st.markdown("---")

# ── Metriques ──────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

total      = db.urls_to_scrape.count_documents({})
completed  = db.urls_to_scrape.count_documents({"status": "completed"})
processing = db.urls_to_scrape.count_documents({"status": "processing"})
failed     = db.urls_to_scrape.count_documents({"status": "failed"})

taux = (completed / total * 100) if total > 0 else 0

c1.metric("Total",     f"{total:,}")
c2.metric("Traitees",  f"{completed:,}", delta=f"{taux:.1f}%")
c3.metric("En cours",  f"{processing:,}")
c4.metric("Echecs",    f"{failed:,}")

st.markdown("---")

# ── Graphiques ─────────────────────────────────────────────────
left, right = st.columns(2)

with left:
    st.markdown("### Repartition")
    df = pd.DataFrame({
        "Statut": ["Traitees", "En cours", "Echecs"],
        "Nombre": [completed, processing, failed],
    })
    fig = px.pie(df, values="Nombre", names="Statut", hole=0.45,
                 color="Statut",
                 color_discrete_map={
                     "Traitees": COLORS["success"],
                     "En cours": COLORS["warning"],
                     "Echecs":   COLORS["danger"],
                 })
    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_traces(textinfo="percent+value", textfont_size=12,
                      marker=dict(line=dict(color=COLORS["bg"], width=2)))
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.markdown("### Activite — 7 derniers jours")
    pipeline = [
        {"$match": {"status": "completed",
                     "completed_at": {"$gte": datetime.utcnow() - timedelta(days=7)}}},
        {"$group": {"_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$completed_at"}},
                     "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]
    data = list(db.urls_to_scrape.aggregate(pipeline))
    if data:
        df = pd.DataFrame(data, columns=["Date", "URLs"])
        fig = go.Figure(go.Bar(x=df["Date"], y=df["URLs"],
                               marker_color=COLORS["info"], opacity=0.85))
        fig.update_layout(**PLOTLY_LAYOUT,
                          xaxis=AXIS_CLEAN, yaxis=AXIS_STYLE)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune donnee sur les 7 derniers jours.")

st.markdown("---")

# ── Par source ─────────────────────────────────────────────────
st.markdown("### Performance par source")

pipeline = [
    {"$group": {"_id": {"source": "$source", "status": "$status"}, "count": {"$sum": 1}}},
    {"$sort": {"_id.source": 1}},
]
src = list(db.urls_to_scrape.aggregate(pipeline))

if src:
    rows = [{"Source": i["_id"].get("source", "N/A"),
             "Statut": i["_id"].get("status", "N/A"),
             "Nombre": i["count"]} for i in src]
    df = pd.DataFrame(rows)
    fig = px.bar(df, x="Source", y="Nombre", color="Statut", barmode="stack",
                 color_discrete_map={
                     "completed":  COLORS["success"],
                     "processing": COLORS["warning"],
                     "failed":     COLORS["danger"],
                     "pending":    COLORS["muted"],
                 })
    fig.update_layout(**PLOTLY_LAYOUT, xaxis=AXIS_CLEAN, yaxis=AXIS_STYLE)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── Dernieres URLs ─────────────────────────────────────────────
st.markdown("### Dernieres URLs traitees")

recent = list(
    db.urls_to_scrape.find(
        {"status": "completed"},
        {"url": 1, "source": 1, "worker_id": 1, "completed_at": 1, "_id": 0},
    ).sort("completed_at", -1).limit(15)
)

if recent:
    df = pd.DataFrame(recent)
    if "completed_at" in df.columns:
        df["completed_at"] = pd.to_datetime(df["completed_at"]).dt.strftime("%d/%m/%Y %H:%M")
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("Aucune URL traitee.")

# ── Footer ─────────────────────────────────────────────────────
st.markdown("---")
c1, _, _ = st.columns([1, 1, 4])
with c1:
    if st.button("Actualiser"):
        st.rerun()