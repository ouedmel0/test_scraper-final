#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Robust-Scraper — Script de peuplement MongoDB (Démo)
Insère des données réalistes dans MongoDB pour la démonstration
du dashboard. Simule le résultat d'un pipeline complet de détection.

Usage: python seed_mongodb.py
"""

import os
import hashlib
import random
from datetime import datetime, timedelta
from pymongo import MongoClient

# ============================================================================
# CONFIGURATION
# ============================================================================

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://admin:ChangeMe789@mongodb:27017/")
MONGO_DATABASE = os.environ.get("MONGO_DATABASE", "robust_scraper")

# ============================================================================
# DONNÉES RÉALISTES
# ============================================================================

# Exemples de fuites simulées (contenu crédible pour le Dark Web)
LEAK_TEMPLATES = [
    {
        "title": "Database Dump - Ministère de l'Économie BF",
        "content_preview": "SQL Dump - ministere-economie.gov.bf\nTable: users\n"
            "Records: 45,230\nColumns: id, nom, prenom, email, telephone, poste\n"
            "Sample: 1|Ouédraogo|Ibrahim|i.ouedraogo@economie.gov.bf|+226 70123456|Directeur\n"
            "2|Sawadogo|Aminata|a.sawadogo@economie.gov.bf|+226 78654321|Analyste\n"
            "Leaked: 2025-06-15 | Size: 234 MB | Format: SQL + CSV",
        "final_status": "confirmed_leak",
        "is_bf": True,
        "bf_type": "administrative",
        "sensitivity": "critical",
        "leak_score": 92,
        "bf_score": 85,
        "iocs": {"email": ["i.ouedraogo@economie.gov.bf", "a.sawadogo@economie.gov.bf"],
                 "ipv4": ["196.28.245.12"]},
        "keywords": ["dump", "database", "leak", "burkina"],
        "markers_geo": ["burkina", "ouagadougou"],
        "markers_admin": ["ministère"],
        "phones": ["+226 70123456", "+226 78654321"],
    },
    {
        "title": "CNIB Database Leaked - 200K+ records",
        "content_preview": "CNIB Records - Burkina Faso National ID\n"
            "Total records: 234,891\nFormat: CSV\n"
            "Fields: cnib_number, nom, prenom, date_naissance, lieu, adresse\n"
            "Sample: BF20180034521|Compaoré|Jean|1985-03-12|Ouagadougou|Secteur 15\n"
            "BF20190087432|Zongo|Fatimata|1990-07-23|Bobo-Dioulasso|Secteur 8\n"
            "Price: 0.5 BTC | Contact: [REDACTED]",
        "final_status": "confirmed_leak",
        "is_bf": True,
        "bf_type": "cnib",
        "sensitivity": "critical",
        "leak_score": 98,
        "bf_score": 95,
        "iocs": {"bitcoin": ["1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"]},
        "keywords": ["cnib", "leak", "database", "burkina faso"],
        "markers_geo": ["burkina faso", "ouagadougou", "bobo-dioulasso"],
        "markers_admin": ["cnib", "carte nationale"],
        "phones": [],
        "cnib_numbers": ["BF20180034521", "BF20190087432"],
    },
    {
        "title": "Orange Burkina Client Data - 50K accounts",
        "content_preview": "Orange Burkina Faso - Customer Database\n"
            "Accounts: 52,341\nData includes: phone, name, balance, location\n"
            "Fresh dump from 2025-05 | Verified working numbers\n"
            "Sample: +22670112233|Traoré Moussa|15000 FCFA|Ouaga\n"
            "+22678445566|Kaboré Aïcha|8500 FCFA|Koudougou\n"
            "Selling in bulk - DM for prices",
        "final_status": "confirmed_leak",
        "is_bf": True,
        "bf_type": "telecom",
        "sensitivity": "high",
        "leak_score": 88,
        "bf_score": 78,
        "iocs": {"email": []},
        "keywords": ["dump", "selling", "data", "burkina"],
        "markers_geo": ["burkina faso", "ouagadougou", "koudougou"],
        "markers_telecom": ["orange burkina"],
        "phones": ["+22670112233", "+22678445566"],
    },
    {
        "title": "Coris Bank BF - Internal credentials",
        "content_preview": "Coris Bank International - Staff Access\n"
            "Obtained via phishing campaign targeting IT dept\n"
            "admin@corisbank.bf / C0r1s2025!Admin\n"
            "vpn.corisbank.bf credentials included\n"
            "Last verified: 2025-06-01",
        "final_status": "confirmed_leak",
        "is_bf": True,
        "bf_type": "banking",
        "sensitivity": "critical",
        "leak_score": 95,
        "bf_score": 82,
        "iocs": {"email": ["admin@corisbank.bf"]},
        "keywords": ["credentials", "phishing", "bank"],
        "markers_geo": ["burkina"],
        "markers_banking": ["coris bank"],
        "phones": [],
    },
    {
        "title": "Université Joseph Ki-Zerbo - Student Records",
        "content_preview": "Université Joseph Ki-Zerbo Ouagadougou\n"
            "Student database export - 2024/2025\n"
            "Records: 12,450 students\n"
            "Fields: matricule, nom, prenom, filiere, email_univ, telephone\n"
            "Format: Excel (.xlsx)",
        "final_status": "suspected_leak",
        "is_bf": True,
        "bf_type": "education",
        "sensitivity": "high",
        "leak_score": 72,
        "bf_score": 68,
        "iocs": {},
        "keywords": ["database", "student", "export"],
        "markers_geo": ["ouagadougou"],
        "markers_edu": ["université joseph ki-zerbo"],
        "phones": [],
    },
]

# Faux positifs et non-fuites
NON_LEAK_TEMPLATES = [
    {
        "title": "Cybersecurity News - Africa Digest",
        "content_preview": "Weekly roundup of cybersecurity events in Africa. "
            "No new breaches reported for West African banks this week. "
            "ANSSI Burkina Faso announced new security guidelines.",
        "final_status": "not_leak",
        "is_bf": False,
        "leak_score": 25,
    },
    {
        "title": "Forum - General discussion about VPNs",
        "content_preview": "Best VPN for accessing blocked sites. "
            "Recommendations for NordVPN, ExpressVPN. Tutorial on Tor setup.",
        "final_status": "not_leak",
        "is_bf": False,
        "leak_score": 15,
    },
    {
        "title": "Marketplace - Digital services for sale",
        "content_preview": "Web hosting, domain registration, VPS services. "
            "Accepting Bitcoin and Monero. Reliable uptime guaranteed.",
        "final_status": "not_leak",
        "is_bf": False,
        "leak_score": 20,
    },
    {
        "title": "Discussion on database security best practices",
        "content_preview": "How to protect your MongoDB from breaches. "
            "Always enable authentication. Use strong passwords. "
            "Regular backups are essential for data protection.",
        "final_status": "not_leak",
        "is_bf": False,
        "leak_score": 30,
    },
]

# Suspicions
SUSPECTED_TEMPLATES = [
    {
        "title": "West Africa Government Data - Unverified",
        "content_preview": "Claiming to have data from multiple West African "
            "government agencies. No samples provided yet. "
            "Mentions Burkina, Mali, Niger. Asking for offers.",
        "final_status": "suspected_leak",
        "is_bf": True,
        "bf_type": "administrative",
        "sensitivity": "medium",
        "leak_score": 55,
        "bf_score": 45,
        "keywords": ["data", "government"],
        "markers_geo": ["burkina"],
    },
    {
        "title": "Telecom data Africa - partial dump",
        "content_preview": "Mixed telecom records from several African countries. "
            "Includes some numbers with +226 prefix. Quality varies. "
            "Could be outdated data from 2023.",
        "final_status": "suspected_leak",
        "is_bf": True,
        "bf_type": "telecom",
        "sensitivity": "medium",
        "leak_score": 48,
        "bf_score": 35,
        "keywords": ["dump", "telecom"],
        "markers_geo": ["burkina"],
    },
]

ONION_DOMAINS = [
    "http://darkleaks4xqmr7j.onion",
    "http://breachforum2kpzwx.onion",
    "http://pastebintor5gxa3.onion",
    "http://dumpmarket7hg4ks.onion",
    "http://africandata9zt2p.onion",
    "http://hackforumxyz123a.onion",
    "http://sahelwatch8km4nq.onion",
    "http://databazaar3p7lmx.onion",
    "http://leakzone5nw9krt.onion",
    "http://westafricaleaks7z.onion",
]


def generate_url():
    domain = random.choice(ONION_DOMAINS)
    path = random.choice([
        "/post/", "/thread/", "/paste/", "/dump/", "/listing/",
        "/topic/", "/data/", "/view/", "/forum/",
    ])
    uid = hashlib.md5(str(random.random()).encode()).hexdigest()[:8]
    return f"{domain}{path}{uid}"


def seed_database():
    """Peuple MongoDB avec des données de démonstration réalistes."""
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DATABASE]

    # Nettoyer les collections existantes
    db.leaks.drop()
    db.alerts.drop()
    db.urls_to_scrape.drop()

    print("=" * 60)
    print("🌱 Seeding MongoDB for demo...")
    print("=" * 60)

    now = datetime.utcnow()
    leaks_inserted = 0
    alerts_inserted = 0
    urls_inserted = 0

    all_templates = []

    # Multiplier les templates pour avoir du volume
    for t in LEAK_TEMPLATES:
        for i in range(random.randint(3, 6)):
            all_templates.append(("leak", t))

    for t in SUSPECTED_TEMPLATES:
        for i in range(random.randint(5, 10)):
            all_templates.append(("suspected", t))

    for t in NON_LEAK_TEMPLATES:
        for i in range(random.randint(8, 15)):
            all_templates.append(("non_leak", t))

    random.shuffle(all_templates)

    for idx, (category, template) in enumerate(all_templates):
        url = generate_url()
        url_hash = hashlib.sha256(url.encode()).hexdigest()
        days_ago = random.randint(0, 30)
        created = now - timedelta(days=days_ago, hours=random.randint(0, 23))

        # --- URL document ---
        url_doc = {
            "url": url,
            "url_hash": url_hash,
            "status": "completed",
            "final_status": template["final_status"],
            "started_at": created - timedelta(minutes=5),
            "completed_at": created,
            "spider": "onion_spider",
        }
        db.urls_to_scrape.insert_one(url_doc)
        urls_inserted += 1

        # --- Leak document ---
        is_bf = template.get("is_bf", False)
        bf_analysis = None
        if is_bf:
            bf_analysis = {
                "geographic_matches": template.get("markers_geo", []),
                "administrative_matches": template.get("markers_admin", []),
                "telecom_matches": template.get("markers_telecom", []),
                "banking_matches": template.get("markers_banking", []),
                "education_matches": template.get("markers_edu", []),
                "phone_numbers": template.get("phones", []),
                "cnib_numbers": template.get("cnib_numbers", []),
                "total_score": template.get("bf_score", 0),
                "data_type": template.get("bf_type", "general"),
                "sensitivity_level": template.get("sensitivity", "medium"),
            }

        # Simuler une prédiction BERT
        if template["final_status"] == "confirmed_leak":
            bert_pred = {
                "predicted_label": "confirmed_leak",
                "confidence": round(random.uniform(0.82, 0.97), 4),
                "model_type": "mBERT-3classes",
            }
        elif template["final_status"] == "suspected_leak":
            bert_pred = {
                "predicted_label": "suspected_leak",
                "confidence": round(random.uniform(0.55, 0.78), 4),
                "model_type": "mBERT-3classes",
            }
        else:
            bert_pred = {
                "predicted_label": "not_leak",
                "confidence": round(random.uniform(0.75, 0.95), 4),
                "model_type": "mBERT-3classes",
            }

        leak_doc = {
            "url": url,
            "url_hash": url_hash,
            "title": template["title"],
            "content": template["content_preview"],
            "leak_score": template.get("leak_score", random.randint(10, 40)),
            "bf_score": template.get("bf_score", 0),
            "final_status": template["final_status"],
            "bert_prediction": bert_pred,
            "heuristic_status": "suspected_leak" if category != "non_leak" else "not_relevant",
            "is_bf_related": is_bf,
            "bf_analysis": bf_analysis,
            "iocs": template.get("iocs", {}),
            "ioc_count": sum(len(v) for v in template.get("iocs", {}).values()),
            "keywords_found": template.get("keywords", []),
            "keyword_count": len(template.get("keywords", [])),
            "source_type": "onion",
            "depth": random.randint(0, 2),
            "scraped_at": created.isoformat() + "Z",
            "preprocessed_at": (created + timedelta(seconds=30)).isoformat() + "Z",
            "classified_at": (created + timedelta(seconds=45)).isoformat() + "Z",
            "created_at": created,
            "updated_at": created,
        }
        db.leaks.insert_one(leak_doc)
        leaks_inserted += 1

        # --- Alertes pour les critiques BF ---
        if is_bf and template.get("sensitivity") in ("critical", "high"):
            alert = {
                "leak_url_hash": url_hash,
                "url": url,
                "severity": template.get("sensitivity", "high"),
                "type": template.get("bf_type", "unknown"),
                "message": f"BF LEAK: {template['title']}",
                "final_status": template["final_status"],
                "bert_label": bert_pred["predicted_label"],
                "bert_confidence": bert_pred["confidence"],
                "bf_score": template.get("bf_score", 0),
                "leak_score": template.get("leak_score", 0),
                "created_at": created,
                "status": random.choice(["open", "open", "open", "investigating", "resolved"]),
            }
            db.alerts.insert_one(alert)
            alerts_inserted += 1

    # Créer les index
    db.leaks.create_index("url_hash", unique=True)
    db.leaks.create_index("is_bf_related")
    db.leaks.create_index("final_status")
    db.leaks.create_index("leak_score")
    db.leaks.create_index("created_at")
    db.alerts.create_index("created_at")
    db.alerts.create_index("status")

    print(f"\n✅ Seed complete!")
    print(f"   URLs:   {urls_inserted}")
    print(f"   Leaks:  {leaks_inserted}")
    print(f"   Alerts: {alerts_inserted}")
    print(f"\n📊 Breakdown:")
    print(f"   Confirmed leaks:  {db.leaks.count_documents({'final_status': 'confirmed_leak'})}")
    print(f"   Suspected leaks:  {db.leaks.count_documents({'final_status': 'suspected_leak'})}")
    print(f"   Not leaks:        {db.leaks.count_documents({'final_status': 'not_leak'})}")
    print(f"   BF related:       {db.leaks.count_documents({'is_bf_related': True})}")
    print(f"   Critical alerts:  {db.alerts.count_documents({'severity': 'critical'})}")

    client.close()


if __name__ == "__main__":
    seed_database()
