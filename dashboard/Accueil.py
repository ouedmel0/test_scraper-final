#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robust-Scraper — Accueil
"""

import streamlit as st
from datetime import datetime
from utils.theme import get_db, inject_css, COLORS

st.set_page_config(
    page_title="Robust-Scraper",
    page_icon="RS",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()
db = get_db()

# ── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("#### ROBUST-SCRAPER")
    st.caption("Surveillance Dark Web — ANSSI-BF")
    st.markdown("---")
    st.caption(f"Mise a jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# ── Header ─────────────────────────────────────────────────────
st.markdown("# Robust-Scraper")
st.caption("Systeme de detection de fuites de donnees sur le Dark Web — ANSSI Burkina Faso")
st.markdown("---")

# ── Metriques globales ─────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

total_urls     = db.urls_to_scrape.count_documents({})
completed_urls = db.urls_to_scrape.count_documents({"status": "completed"})
total_leaks    = db.leaks.count_documents({})
critical       = db.leaks.count_documents({"is_bf_related": True, "bf_analysis.sensitivity_level": "critical"})

c1.metric("URLs collectees",   f"{total_urls:,}")
c2.metric("URLs traitees",     f"{completed_urls:,}")
c3.metric("Fuites detectees",  f"{total_leaks:,}")
c4.metric("Alertes critiques", f"{critical:,}")

st.markdown("---")

# ── Statut systeme ─────────────────────────────────────────────
st.markdown("### Statut systeme")

processing = db.urls_to_scrape.count_documents({"status": "processing"})
failed     = db.urls_to_scrape.count_documents({"status": "failed"})

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown('<span class="badge badge-ok">CONNECTE</span>', unsafe_allow_html=True)
    st.caption("MongoDB")
with c2:
    if total_leaks > 0:
        st.markdown('<span class="badge badge-ok">ACTIF</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge badge-warn">EN ATTENTE</span>', unsafe_allow_html=True)
    st.caption("Kafka")
with c3:
    st.metric("En traitement", f"{processing:,}")
with c4:
    st.metric("Echecs", f"{failed:,}")

st.markdown("---")

# ── Resume ─────────────────────────────────────────────────────
st.markdown("### Indicateurs cles")

taux_scraping   = (completed_urls / total_urls * 100) if total_urls > 0 else 0
bf_related      = db.leaks.count_documents({"is_bf_related": True})
taux_pertinence = (bf_related / total_leaks * 100) if total_leaks > 0 else 0

c1, c2, c3 = st.columns(3)
c1.metric("Taux de scraping",    f"{taux_scraping:.1f}%")
c2.metric("Fuites liees au BF",  f"{bf_related:,}")
c3.metric("Pertinence IA",       f"{taux_pertinence:.1f}%")

# ── Footer ─────────────────────────────────────────────────────
st.markdown("---")
st.caption("Robust-Scraper v1.0 — ANSSI Burkina Faso")