#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robust-Scraper — Classification IA
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from utils.theme import get_db, inject_css, COLORS, PLOTLY_LAYOUT, AXIS_STYLE, AXIS_CLEAN

st.set_page_config(page_title="Classification | Robust-Scraper", page_icon="RS", layout="wide")
inject_css()
db = get_db()

# ── Header ─────────────────────────────────────────────────────
st.markdown("# Classification IA")
st.caption("Analyse BERT et scoring de pertinence — Fuites liees au Burkina Faso")
st.markdown("---")

# ── Metriques ──────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

total     = db.leaks.count_documents({})
bf        = db.leaks.count_documents({"is_bf_related": True})
confirmed = db.leaks.count_documents({"bf_analysis.classification": "confirmed_leak"})
suspected = db.leaks.count_documents({"bf_analysis.classification": "suspected_leak"})

pct_bf   = (bf / total * 100) if total > 0 else 0
pct_conf = (confirmed / bf * 100) if bf > 0 else 0

c1.metric("Total analyse",  f"{total:,}")
c2.metric("Pertinence BF",  f"{bf:,}", delta=f"{pct_bf:.1f}%")
c3.metric("Confirmees",     f"{confirmed:,}", delta=f"{pct_conf:.1f}%")
c4.metric("Suspectees",     f"{suspected:,}")

st.markdown("---")

# ── Classification + Criticite ─────────────────────────────────
left, right = st.columns(2)

LABEL_CLASS = {"confirmed_leak": "Confirmee", "suspected_leak": "Suspectee", "low_confidence": "Faible confiance"}
LABEL_LEVEL = {"critical": "Critique", "high": "Eleve", "medium": "Moyen", "low": "Faible"}

with left:
    st.markdown("### Classification")
    pipe = [
        {"$match": {"is_bf_related": True}},
        {"$group": {"_id": "$bf_analysis.classification", "n": {"$sum": 1}}},
    ]
    data = list(db.leaks.aggregate(pipe))
    if data:
        df = pd.DataFrame(data)
        df.columns = ["Classification", "Nombre"]
        df["Classification"] = df["Classification"].map(LABEL_CLASS).fillna(df["Classification"])

        color_seq = [COLORS["critical"], COLORS["warning"], COLORS["success"]]
        fig = go.Figure(go.Bar(
            x=df["Classification"], y=df["Nombre"],
            marker_color=color_seq[:len(df)],
            text=df["Nombre"], textposition="auto",
            textfont=dict(color=COLORS["text"], size=13),
        ))
        fig.update_layout(**PLOTLY_LAYOUT, showlegend=False,
                          xaxis=AXIS_CLEAN, yaxis=AXIS_STYLE)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune donnee.")

with right:
    st.markdown("### Niveaux de criticite")
    pipe = [
        {"$match": {"is_bf_related": True}},
        {"$group": {"_id": "$bf_analysis.sensitivity_level", "n": {"$sum": 1}}},
    ]
    data = list(db.leaks.aggregate(pipe))
    if data:
        df = pd.DataFrame(data)
        df.columns = ["Niveau", "Nombre"]
        df["Niveau"] = df["Niveau"].map(LABEL_LEVEL).fillna(df["Niveau"])

        fig = px.pie(df, values="Nombre", names="Niveau", hole=0.45,
                     color="Niveau",
                     color_discrete_map={
                         "Critique": COLORS["critical"], "Eleve": COLORS["high"],
                         "Moyen": COLORS["medium"],      "Faible": COLORS["low"],
                     })
        fig.update_layout(**PLOTLY_LAYOUT)
        fig.update_traces(textinfo="percent+value", textfont_size=12,
                          marker=dict(line=dict(color=COLORS["bg"], width=2)))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune donnee.")

st.markdown("---")

# ── Distribution des scores ────────────────────────────────────
st.markdown("### Distribution des scores")

pipe = [
    {"$match": {"is_bf_related": True, "bf_analysis.total_score": {"$exists": True}}},
    {"$project": {"score": "$bf_analysis.total_score"}},
]
scores = list(db.leaks.aggregate(pipe))

if scores:
    df = pd.DataFrame(scores)
    fig = go.Figure(go.Histogram(
        x=df["score"], nbinsx=25,
        marker_color=COLORS["info"],
        marker_line_color=COLORS["bg"], marker_line_width=1,
        opacity=0.85,
    ))
    fig.add_vline(x=40, line_dash="dash", line_color=COLORS["warning"],
                  annotation_text="Suspicion (40)", annotation_position="top left",
                  annotation_font=dict(color=COLORS["warning"], size=11))
    fig.add_vline(x=70, line_dash="dash", line_color=COLORS["critical"],
                  annotation_text="Confirmation (70)", annotation_position="top right",
                  annotation_font=dict(color=COLORS["critical"], size=11))
    fig.update_layout(**PLOTLY_LAYOUT,
                      xaxis_title="Score", yaxis_title="Nombre",
                      xaxis=AXIS_CLEAN, yaxis=AXIS_STYLE)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Aucun score disponible.")

st.markdown("---")

# ── Top indicateurs ────────────────────────────────────────────
st.markdown("### Indicateurs detectes")

left, right = st.columns(2)

def horizontal_bar(collection_field, title, color, container):
    with container:
        st.markdown(f"**{title}**")
        pipe = [
            {"$match": {f"bf_analysis.{collection_field}": {"$exists": True, "$ne": []}}},
            {"$unwind": f"$bf_analysis.{collection_field}"},
            {"$group": {"_id": f"$bf_analysis.{collection_field}", "n": {"$sum": 1}}},
            {"$sort": {"n": -1}}, {"$limit": 10},
        ]
        data = list(db.leaks.aggregate(pipe))
        if data:
            df = pd.DataFrame(data)
            df.columns = ["Marqueur", "Occurrences"]
            fig = go.Figure(go.Bar(
                y=df["Marqueur"], x=df["Occurrences"], orientation="h",
                marker_color=color,
                text=df["Occurrences"], textposition="auto",
                textfont=dict(color=COLORS["text"], size=11),
            ))
            fig.update_layout(**PLOTLY_LAYOUT, height=320,
                              xaxis=AXIS_STYLE, yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucun marqueur.")

horizontal_bar("geographic_matches",      "Marqueurs geographiques",  COLORS["info"],    left)
horizontal_bar("administrative_matches",  "Marqueurs administratifs", COLORS["warning"], right)

# ── Footer ─────────────────────────────────────────────────────
st.markdown("---")
c1, _, _ = st.columns([1, 1, 4])
with c1:
    if st.button("Actualiser"):
        st.rerun()