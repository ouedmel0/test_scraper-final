#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Données mockées pour développement local Windows
Robust-Scraper Dashboard - ANSSI Burkina Faso
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

random.seed(42)
np.random.seed(42)

def get_stats():
    return {
        'total_leaks': 1_247,
        'bf_leaks': 312,
        'critical_leaks': 47,
        'bert_classified': 1_189,
        'recent_leaks': 23,
        'bf_percentage': 25.0,
        'scraping_uptime': 98.7,
        'pages_scraped_today': 4_821,
        'sources_monitored': 34,
        'last_scrape': datetime.now() - timedelta(minutes=12),
    }

def get_leaks_timeline(days=7):
    dates = [datetime.now() - timedelta(days=i) for i in range(days, -1, -1)]
    return pd.DataFrame({
        'date': dates,
        'total': np.random.randint(80, 200, len(dates)),
        'bf_related': np.random.randint(15, 60, len(dates)),
        'critical': np.random.randint(2, 15, len(dates)),
    })

def get_leaks_by_category():
    categories = ['Identifiants', 'Données financières', 'Documents gov.', 
                  'Données personnelles', 'Accès réseau', 'Emails', 'Mots de passe']
    counts = [234, 189, 156, 143, 98, 87, 67]
    return pd.DataFrame({'category': categories, 'count': counts})

def get_leaks_by_severity():
    return pd.DataFrame({
        'severity': ['critical', 'high', 'medium', 'low'],
        'count': [47, 183, 412, 605]
    })

def get_scraping_performance():
    hours = list(range(24))
    return pd.DataFrame({
        'heure': [f"{h:02d}h" for h in hours],
        'pages_scrapées': np.random.randint(150, 350, 24),
        'erreurs': np.random.randint(0, 15, 24),
        'temps_moyen_ms': np.random.randint(200, 800, 24),
    })

def get_sources_status():
    return pd.DataFrame({
        'source': ['Forum Alpha', 'Market X', 'Paste Site 1', 'Forum Beta', 
                   'Dark Market 2', 'Leak DB', 'Channel TG', 'IRC Anon'],
        'statut': ['actif', 'actif', 'actif', 'erreur', 'actif', 'actif', 'inactif', 'actif'],
        'dernière_collecte': [
            datetime.now() - timedelta(minutes=random.randint(1, 120))
            for _ in range(8)
        ],
        'docs_collectés': np.random.randint(50, 800, 8),
        'taux_succès': [f"{random.uniform(85, 100):.1f}%" for _ in range(8)],
    })

def get_ai_performance():
    dates = [datetime.now() - timedelta(days=i) for i in range(14, -1, -1)]
    return pd.DataFrame({
        'date': dates,
        'précision': np.random.uniform(0.88, 0.97, len(dates)),
        'rappel': np.random.uniform(0.84, 0.95, len(dates)),
        'f1_score': np.random.uniform(0.86, 0.96, len(dates)),
        'docs_classifiés': np.random.randint(60, 180, len(dates)),
    })

def get_classification_distribution():
    return pd.DataFrame({
        'label': ['Fuite confirmée', 'Suspicion fuite', 'Non pertinent', 'Ambigu'],
        'count': [312, 456, 389, 90],
        'confiance_moy': [0.94, 0.78, 0.91, 0.52],
    })

def get_recent_alerts():
    titles = [
        "Base de données clients Banque BF exposée",
        "Identifiants SONABEL en vente",
        "Documents MINEFID — accès non autorisé",
        "Liste d'emails fonctionnaires Ouagadougou",
        "Credentials VPN ministère de la défense",
        "Dump BF Telecom — 45k entrées",
        "Passeports scannés Burkina — forum russe",
        "Données CNSS employés secteur public",
        "Accès RDP serveur entreprise BF",
        "Cartes bancaires — préfixe BF détecté",
        "Rapport interne ARCEP leaked",
        "Base municipale Bobo-Dioulasso",
    ]
    sources = ['Forum Alpha', 'Market X', 'Paste Site 1', 'Dark Market 2', 
               'Forum Beta', 'Leak DB']
    severities = ['critical', 'high', 'high', 'medium', 'critical', 
                  'high', 'medium', 'high', 'critical', 'medium', 'high', 'medium']
    statuts = ['confirmée', 'confirmée', 'confirmée', 'suspicion', 'confirmée',
               'confirmée', 'suspicion', 'suspicion', 'confirmée', 'suspicion', 
               'confirmée', 'suspicion']
    
    return pd.DataFrame({
        'titre': titles,
        'source': [random.choice(sources) for _ in titles],
        'sévérité': severities,
        'statut': statuts,
        'score': [round(random.uniform(0.6, 0.99), 2) for _ in titles],
        'catégorie': ['Données financières', 'Identifiants', 'Documents gov.',
                      'Données personnelles', 'Accès réseau', 'Identifiants',
                      'Données personnelles', 'Données personnelles', 'Accès réseau',
                      'Données financières', 'Documents gov.', 'Données personnelles'],
        'détecté_le': [datetime.now() - timedelta(hours=random.randint(1, 72)) 
                       for _ in titles],
    })