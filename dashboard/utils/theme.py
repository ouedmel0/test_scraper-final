#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module partagé : connexion MongoDB, palette, layout Plotly, CSS additionnel.
Importé par toutes les pages pour garantir la cohérence visuelle.
"""

import streamlit as st
import pymongo
import os

# ── Connexion MongoDB (singleton via cache) ────────────────────
@st.cache_resource
def get_db():
    uri = os.getenv("MONGO_URI", "mongodb://admin:ChangeMe789@mongodb:27017/")
    name = os.getenv("MONGO_DATABASE", "robust_scraper")
    client = pymongo.MongoClient(uri)
    return client[name]


# ── Palette ────────────────────────────────────────────────────
COLORS = {
    # Sévérité
    "critical":  "#F85149",
    "high":      "#D29922",
    "medium":    "#E3B341",
    "low":       "#3FB950",
    # Statuts
    "success":   "#3FB950",
    "warning":   "#D29922",
    "danger":    "#F85149",
    "info":      "#4A90D9",
    "muted":     "#8B949E",
    # Surfaces
    "bg":        "#0D1117",
    "card":      "#161B22",
    "border":    "#2D3348",
    "text":      "#E6EDF3",
    "text_sec":  "#8B949E",
}

# ── Layout Plotly partagé ──────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", size=12, color=COLORS["text_sec"]),
    margin=dict(l=16, r=16, t=36, b=16),
    legend=dict(
        orientation="h",
        yanchor="bottom", y=1.02,
        xanchor="right", x=1,
        font=dict(size=11),
    ),
)

AXIS_STYLE = dict(gridcolor="#1E2130", gridwidth=0.5, showgrid=True)
AXIS_CLEAN = dict(gridcolor="#1E2130", showgrid=False)


# ── CSS additionnel (au-delà du thème config.toml) ─────────────
def inject_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

        /* Metric cards */
        [data-testid="stMetric"] {
            background: linear-gradient(135deg, #161B22 0%, #1C2333 100%);
            border: 1px solid #2D3348;
            border-radius: 10px;
            padding: 16px 20px;
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.75rem !important;
            font-weight: 600;
            color: #8B949E !important;
            text-transform: uppercase;
            letter-spacing: 0.6px;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.7rem !important;
            font-weight: 700;
            color: #E6EDF3 !important;
        }

        /* Typography */
        h1 { font-weight: 700 !important; letter-spacing: -0.5px; }
        h2, h3 { font-weight: 600 !important; color: #C9D1D9 !important; }
        hr { border-color: #1E2130 !important; margin: 1.2rem 0 !important; }

        /* Sidebar */
        [data-testid="stSidebar"] { border-right: 1px solid #1E2130; }

        /* Buttons */
        .stButton > button {
            background: #1C2333; color: #C9D1D9;
            border: 1px solid #2D3348; border-radius: 8px;
            font-weight: 500; font-size: 0.85rem;
            transition: all 0.15s ease;
        }
        .stButton > button:hover {
            background: #2D3348; border-color: #4A90D9; color: #E6EDF3;
        }

        /* DataFrames */
        [data-testid="stDataFrame"] {
            border: 1px solid #2D3348; border-radius: 8px; overflow: hidden;
        }

        /* Reduce top padding */
        .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }

        /* Status badges */
        .badge {
            display: inline-block; padding: 3px 10px; border-radius: 20px;
            font-size: 0.72rem; font-weight: 600; letter-spacing: 0.3px;
        }
        .badge-ok    { background: rgba(63,185,80,0.12); color: #3FB950; border: 1px solid rgba(63,185,80,0.25); }
        .badge-warn  { background: rgba(210,153,34,0.12); color: #D29922; border: 1px solid rgba(210,153,34,0.25); }
        .badge-err   { background: rgba(248,81,73,0.12); color: #F85149; border: 1px solid rgba(248,81,73,0.25); }

        /* Alert cards */
        .leak-card {
            border-radius: 8px; padding: 14px 18px; margin-bottom: 10px;
        }
        .leak-card h4 { margin: 0 0 6px 0; font-size: 0.9rem; font-weight: 600; color: #E6EDF3; }
        .leak-card p  { margin: 0; font-size: 0.78rem; color: #8B949E; }
        .leak-card .score { font-weight: 700; font-size: 1rem; }

        .card-critical { background: rgba(248,81,73,0.06); border: 1px solid rgba(248,81,73,0.2); border-left: 4px solid #F85149; }
        .card-high     { background: rgba(210,153,34,0.06); border: 1px solid rgba(210,153,34,0.2); border-left: 4px solid #D29922; }
        .card-medium   { background: rgba(227,179,65,0.06); border: 1px solid rgba(227,179,65,0.2); border-left: 4px solid #E3B341; }
        .card-low      { background: rgba(63,185,80,0.06); border: 1px solid rgba(63,185,80,0.2); border-left: 4px solid #3FB950; }
    </style>
    """, unsafe_allow_html=True)