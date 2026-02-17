#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Robust-Scraper Dashboard
Système de surveillance Dark Web
ANSSI Burkina Faso
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import sys
sys.path.append('/app')

from utils.mongo_client import DashboardMongoClient

# ============================================================================
# CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Robust-Scraper | ANSSI",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CSS PROFESSIONNEL - DESIGN SOBRE
# ============================================================================

st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'IBM Plex Sans', sans-serif;
    }
    
    /* Main Container */
    .main {
        background-color: #ffffff;
        color: #1a1a1a;
    }
    
    /* Headers */
    h1 {
        color: #1a1a1a;
        font-weight: 600;
        font-size: 28px;
        margin-bottom: 8px;
    }
    
    h2 {
        color: #2d2d2d;
        font-weight: 500;
        font-size: 20px;
        margin-top: 24px;
        margin-bottom: 12px;
        border-bottom: 2px solid #e5e5e5;
        padding-bottom: 8px;
    }
    
    h3 {
        color: #4a4a4a;
        font-weight: 500;
        font-size: 16px;
    }
    
    /* Metrics */
    .stMetric {
        background-color: #f8f9fa;
        padding: 16px;
        border-radius: 4px;
        border-left: 3px solid #0066cc;
    }
    
    .stMetric label {
        color: #6c757d;
        font-size: 12px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stMetric [data-testid="stMetricValue"] {
        color: #1a1a1a;
        font-size: 28px;
        font-weight: 600;
    }
    
    .stMetric [data-testid="stMetricDelta"] {
        font-size: 13px;
        font-weight: 500;
    }
    
    /* Sidebar */
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
        border-right: 1px solid #dee2e6;
    }
    
    /* Buttons */
    .stButton button {
        background-color: #0066cc;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: 500;
        font-size: 14px;
        transition: background-color 0.2s;
    }
    
    .stButton button:hover {
        background-color: #0052a3;
    }
    
    /* Tables */
    .dataframe {
        font-size: 13px;
    }
    
    .dataframe th {
        background-color: #f8f9fa;
        color: #495057;
        font-weight: 600;
        text-align: left;
        padding: 10px;
    }
    
    .dataframe td {
        padding: 8px;
        border-bottom: 1px solid #e9ecef;
    }
    
    /* Status Badge */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    .status-operational {
        background-color: #d1f4e0;
        color: #0d6832;
    }
    
    .status-warning {
        background-color: #fff3cd;
        color: #856404;
    }
    
    .status-critical {
        background-color: #f8d7da;
        color: #721c24;
    }
    
    /* Info Box */
    .info-box {
        background-color: #e7f3ff;
        border-left: 4px solid #0066cc;
        padding: 12px;
        margin: 12px 0;
        border-radius: 2px;
    }
    
    /* Subtitle */
    .subtitle {
        color: #6c757d;
        font-size: 14px;
        margin-top: -8px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# MONGODB CONNECTION
# ============================================================================

try:
    mongo = DashboardMongoClient()
except Exception as e:
    st.error(f"Erreur de connexion à la base de données: {e}")
    st.stop()

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.markdown("### Robust-Scraper")
    st.markdown("ANSSI Burkina Faso")
    
    st.markdown("---")
    
    st.markdown("##### Filtres")
    
    time_range = st.selectbox(
        "Période",
        ["24 heures", "7 jours", "30 jours"],
        index=0
    )
    
    min_score = st.slider(
        "Score minimum",
        0, 100, 30
    )
    
    st.markdown("---")
    
    # Stats rapides
    stats = mongo.get_stats()
    
    st.markdown("##### Statistiques")
    st.markdown(f"**Total:** {stats['total_leaks']:,}")
    st.markdown(f"**Burkina Faso:** {stats['bf_leaks']:,}")
    st.markdown(f"**Critiques:** {stats['critical_leaks']:,}")
    
    st.markdown("---")
    
    if st.button("Actualiser les données", use_container_width=True):
        st.rerun()
    
    st.markdown("---")
    st.markdown(f"<small>Version 2.0.1 | {datetime.now().strftime('%Y')}</small>", unsafe_allow_html=True)

# ============================================================================
# HEADER
# ============================================================================

col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("# Tableau de bord")
    st.markdown('<p class="subtitle">Surveillance et analyse des fuites de données</p>', unsafe_allow_html=True)

with col2:
    st.markdown(
        '<div style="text-align: right; padding-top: 20px;">'
        '<span class="status-badge status-operational">Système opérationnel</span><br>'
        f'<small style="color: #6c757d;">{datetime.now().strftime("%d/%m/%Y %H:%M")}</small>'
        '</div>',
        unsafe_allow_html=True
    )

# ============================================================================
# INDICATEURS PRINCIPAUX
# ============================================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total des détections",
        f"{stats['total_leaks']:,}",
        delta=f"+{stats['recent_leaks']} (24h)" if stats['recent_leaks'] > 0 else None
    )

with col2:
    st.metric(
        "Burkina Faso",
        f"{stats['bf_leaks']:,}",
        delta=f"{stats['bf_percentage']:.1f}% du total"
    )

with col3:
    st.metric(
        "Classifiés (IA)",
        f"{stats['bert_classified']:,}"
    )

with col4:
    st.metric(
        "Niveau critique",
        f"{stats['critical_leaks']:,}"
    )

# ============================================================================
# TIMELINE
# ============================================================================

st.markdown("## Évolution des détections")

timeline_df = mongo.get_leaks_timeline(days=7)

if not timeline_df.empty:
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=timeline_df['date'],
        y=timeline_df['total'],
        name="Total",
        mode='lines+markers',
        line=dict(color='#0066cc', width=2),
        marker=dict(size=6)
    ))
    
    fig.add_trace(go.Scatter(
        x=timeline_df['date'],
        y=timeline_df['bf_related'],
        name="Burkina Faso",
        mode='lines+markers',
        line=dict(color='#28a745', width=2),
        marker=dict(size=6)
    ))
    
    fig.add_trace(go.Scatter(
        x=timeline_df['date'],
        y=timeline_df['critical'],
        name="Critiques",
        mode='lines+markers',
        line=dict(color='#dc3545', width=2, dash='dot'),
        marker=dict(size=6)
    ))
    
    fig.update_layout(
        height=350,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='IBM Plex Sans', color='#495057'),
        margin=dict(l=0, r=0, t=30, b=0),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode='x unified'
    )
    
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='#e9ecef',
        showline=True,
        linewidth=1,
        linecolor='#dee2e6'
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='#e9ecef',
        showline=True,
        linewidth=1,
        linecolor='#dee2e6'
    )
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Aucune donnée disponible pour la période sélectionnée")

# ============================================================================
# ANALYSES
# ============================================================================

col1, col2 = st.columns(2)

with col1:
    st.markdown("## Classification par type")
    
    category_df = mongo.get_leaks_by_category()
    
    if not category_df.empty:
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=category_df['category'],
            x=category_df['count'],
            orientation='h',
            marker=dict(
                color='#0066cc',
                line=dict(color='#0052a3', width=1)
            ),
            text=category_df['count'],
            textposition='outside'
        ))
        
        fig.update_layout(
            height=350,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family='IBM Plex Sans', color='#495057'),
            margin=dict(l=0, r=0, t=10, b=0),
            showlegend=False,
            xaxis_title="Nombre de détections",
            yaxis_title=None
        )
        
        fig.update_xaxes(showgrid=True, gridcolor='#e9ecef')
        fig.update_yaxes(showgrid=False)
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune classification disponible")

with col2:
    st.markdown("## Répartition par sévérité")
    
    severity_df = mongo.get_leaks_by_severity()
    
    if not severity_df.empty:
        colors = {
            'critical': '#dc3545',
            'high': '#fd7e14',
            'medium': '#ffc107',
            'low': '#28a745'
        }
        
        severity_colors = [colors.get(s, '#6c757d') for s in severity_df['severity']]
        
        fig = go.Figure()
        
        fig.add_trace(go.Pie(
            labels=severity_df['severity'],
            values=severity_df['count'],
            marker=dict(colors=severity_colors, line=dict(color='white', width=2)),
            textfont=dict(size=13, family='IBM Plex Sans'),
            hole=0.4
        ))
        
        fig.update_layout(
            height=350,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family='IBM Plex Sans', color='#495057'),
            margin=dict(l=0, r=0, t=10, b=0),
            showlegend=True,
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=0.85)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune donnée de sévérité")

# ============================================================================
# DÉTECTIONS RÉCENTES
# ============================================================================

st.markdown("## Détections récentes")

recent_df = mongo.get_leaks_dataframe(limit=20)

if not recent_df.empty:
    display_df = recent_df[[
        'title', 'leak_score', 'is_bf_related',
        'bert_category', 'bert_confidence', 'bert_severity'
    ]].copy()
    
    display_df.columns = [
        'Titre', 'Score', 'BF', 'Catégorie',
        'Confiance', 'Sévérité'
    ]
    
    # Formater confiance
    display_df['Confiance'] = display_df['Confiance'].apply(lambda x: f"{x:.2f}" if isinstance(x, float) else x)
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=400
    )
else:
    st.info("Aucune détection récente")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: #6c757d; font-size: 12px;">'
    'Robust-Scraper - ANSSI Burkina Faso - Système de surveillance Dark Web'
    '</div>',
    unsafe_allow_html=True
)