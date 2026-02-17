#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Robust-Scraper — Preprocessor
Consomme les documents bruts (raw_documents), effectue :
  - Nettoyage et normalisation du texte
  - Extraction et enrichissement des IOCs
  - Analyse heuristique BF (marqueurs géographiques, téléphones, CNIB)
  - Scoring de pertinence
Publie les résultats dans 'preprocessed_documents'

Author: ANSSI Burkina Faso
Version: 2.0
"""

import os
import re
import json
import logging
from datetime import datetime
from typing import Dict, Tuple, List

from kafka import KafkaConsumer, KafkaProducer
from pymongo import MongoClient

# ============================================================================
# CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s [preprocessor] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092").split(",")
KAFKA_TOPIC_INPUT = os.getenv("KAFKA_TOPIC_INPUT", "raw_documents")
KAFKA_TOPIC_OUTPUT = os.getenv("KAFKA_TOPIC_OUTPUT", "preprocessed_documents")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "preprocessor-group")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:ChangeMe789@mongodb:27017/")
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "robust_scraper")

MIN_SCORE_FOR_CLASSIFICATION = int(os.getenv("MIN_SCORE_FOR_CLASSIFICATION", 20))

# ============================================================================
# MARQUEURS BURKINA FASO
# ============================================================================

BF_MARKERS = {
    "geographic": [
        "burkina", "burkinabè", "burkinabe", "burkina faso",
        "ouagadougou", "ouaga", "bobo", "bobo-dioulasso",
        "koudougou", "banfora", "kaya", "ouahigouya",
        "fada", "gourma", "sahel", "boucle du mouhoun",
        "tenkodogo", "ziniaré", "dédougou", "manga",
    ],
    "administrative": [
        "cnib", "carte nationale", "ministere burkina",
        "gouvernement burkinabe", "anssi", "ministère",
        "préfecture", "mairie de ouagadougou",
        "conseil constitutionnel", "assemblée nationale bf",
        "passeport burkinabe",
    ],
    "telecom": [
        "orange burkina", "moov burkina", "telecel faso",
        "onatel", "arcep burkina",
    ],
    "banking": [
        "coris bank", "bank of africa bf", "boa bf", "bicia",
        "ecobank burkina", "uba burkina", "atlantic bank bf",
        "banque agricole", "rcpb",
    ],
    "education": [
        "université ouaga", "université joseph ki-zerbo",
        "université nazi boni", "ministère éducation burkina",
        "isge", "2ie",
    ],
}

BF_PHONE_PATTERNS = [
    re.compile(r"\+226[0-9\s\-]{8,}"),
    re.compile(r"00226[0-9\s\-]{8,}"),
    re.compile(r"\b0[567][0-9\s\-]{7}\b"),
]

CNIB_PATTERNS = [
    re.compile(r"\bCNIB[:\s\-]?[A-Z0-9]{10,15}\b"),
    re.compile(r"\b[A-Z]{2}[0-9]{8,12}\b"),
]

IOC_PATTERNS = {
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "ipv4": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "md5": re.compile(r"\b[a-fA-F0-9]{32}\b"),
    "sha1": re.compile(r"\b[a-fA-F0-9]{40}\b"),
    "sha256": re.compile(r"\b[a-fA-F0-9]{64}\b"),
    "bitcoin": re.compile(r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b"),
}

CATEGORY_WEIGHTS = {
    "geographic": 30,
    "administrative": 25,
    "telecom": 20,
    "banking": 20,
    "education": 15,
    "phone_bf": 30,
}


# ============================================================================
# TEXT PREPROCESSING
# ============================================================================

def clean_text(text: str) -> str:
    """
    Nettoyage et normalisation du texte brut :
    - Suppression des caractères de contrôle
    - Normalisation des espaces
    - Remplacement des entités sensibles par des marqueurs
    """
    if not text:
        return ""

    # Supprimer caractères de contrôle
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Normaliser les espaces multiples
    text = re.sub(r"\s+", " ", text).strip()

    # Remplacer les emails par un marqueur (pour BERT)
    text = re.sub(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        "[EMAIL]",
        text,
    )

    # Remplacer les numéros de téléphone BF par un marqueur
    text = re.sub(r"\+226\s?[0-9\s\-]{8,}", "[PHONE_BF]", text)
    text = re.sub(r"00226\s?[0-9\s\-]{8,}", "[PHONE_BF]", text)

    # Remplacer les URLs .onion
    text = re.sub(r"https?://[a-z2-7]{16,56}\.onion\S*", "[ONION_URL]", text)

    return text


# ============================================================================
# BF ANALYSIS
# ============================================================================

def analyze_bf_content(content: str, title: str) -> Tuple[bool, Dict]:
    """
    Analyse heuristique pour détecter du contenu lié au Burkina Faso.
    Retourne (is_bf_related, analysis_details).
    """
    text = f"{content} {title}".lower()

    analysis = {
        "geographic_matches": [],
        "administrative_matches": [],
        "telecom_matches": [],
        "banking_matches": [],
        "education_matches": [],
        "phone_numbers": [],
        "cnib_numbers": [],
        "geographic_score": 0,
        "administrative_score": 0,
        "telecom_score": 0,
        "banking_score": 0,
        "education_score": 0,
        "phone_score": 0,
        "total_score": 0,
        "data_type": "unknown",
        "sensitivity_level": "unknown",
    }

    # --- Recherche des marqueurs par catégorie ---
    for category, markers in BF_MARKERS.items():
        key = f"{category}_matches"
        for marker in markers:
            if marker in text:
                analysis[key].append(marker)

    # --- Recherche des numéros de téléphone BF ---
    for pattern in BF_PHONE_PATTERNS:
        matches = pattern.findall(text)
        analysis["phone_numbers"].extend(matches)

    # --- Recherche des numéros CNIB ---
    for pattern in CNIB_PATTERNS:
        matches = pattern.findall(text)
        analysis["cnib_numbers"].extend(matches)

    # --- Calcul des scores par catégorie ---
    for cat in ["geographic", "administrative", "telecom", "banking", "education"]:
        matches = analysis[f"{cat}_matches"]
        if matches:
            weight = CATEGORY_WEIGHTS.get(cat, 10)
            analysis[f"{cat}_score"] = min(len(set(matches)) * 10, weight)

    if analysis["phone_numbers"]:
        analysis["phone_score"] = min(
            len(set(analysis["phone_numbers"])) * 5,
            CATEGORY_WEIGHTS["phone_bf"],
        )

    # --- Score total ---
    analysis["total_score"] = min(
        sum(analysis[f"{cat}_score"] for cat in
            ["geographic", "administrative", "telecom", "banking", "education", "phone"]),
        100,
    )

    # --- Niveau de sensibilité ---
    if analysis["cnib_numbers"]:
        analysis["data_type"] = "cnib"
        analysis["sensitivity_level"] = "critical"
    elif analysis["total_score"] >= 70:
        analysis["sensitivity_level"] = "high"
        if analysis["banking_matches"]:
            analysis["data_type"] = "banking"
        elif analysis["administrative_matches"]:
            analysis["data_type"] = "administrative"
        else:
            analysis["data_type"] = "general"
    elif analysis["total_score"] >= 40:
        analysis["sensitivity_level"] = "medium"
        analysis["data_type"] = "general"
    else:
        analysis["sensitivity_level"] = "low"

    # Déduplication des listes
    for k in analysis:
        if isinstance(analysis[k], list):
            analysis[k] = list(set(analysis[k]))[:50]

    return analysis["total_score"] >= 30, analysis


def extract_iocs(text: str) -> Tuple[Dict, int]:
    """Extraction complète des IOCs du texte."""
    iocs = {}
    for ioc_name, pattern in IOC_PATTERNS.items():
        matches = list(set(pattern.findall(text)))[:100]
        if matches:
            iocs[ioc_name] = matches

    ioc_count = sum(len(v) for v in iocs.values())
    return iocs, ioc_count


# ============================================================================
# PREPROCESSOR SERVICE
# ============================================================================

class Preprocessor:
    """
    Service de prétraitement consommant raw_documents et
    publiant dans preprocessed_documents.
    """

    def __init__(self):
        logger.info("=" * 70)
        logger.info("Robust-Scraper Preprocessor Starting")
        logger.info("Input:  %s", KAFKA_TOPIC_INPUT)
        logger.info("Output: %s", KAFKA_TOPIC_OUTPUT)
        logger.info("=" * 70)

        self.consumer = KafkaConsumer(
            KAFKA_TOPIC_INPUT,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=KAFKA_GROUP_ID,
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            max_poll_interval_ms=300_000,
        )

        self.producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            compression_type="gzip",
            acks="all",
            retries=5,
        )

        self.mongo = MongoClient(MONGO_URI)
        self.db = self.mongo[MONGO_DATABASE]
        self.urls_col = self.db["urls_to_scrape"]

        self.processed_count = 0
        self.bf_count = 0

        logger.info("✔ Preprocessor ready")

    def process_document(self, doc: Dict) -> Dict:
        """
        Pipeline de prétraitement complet d'un document brut.
        """
        url = doc.get("url", "")
        url_hash = doc.get("url_hash", "")
        content = doc.get("content", "")
        title = doc.get("title", "")

        # 1. Nettoyage du texte
        cleaned_content = clean_text(content)

        # 2. Extraction enrichie des IOCs
        iocs, ioc_count = extract_iocs(content)  # Sur le texte original

        # 3. Analyse heuristique BF
        is_bf, bf_analysis = analyze_bf_content(content, title)

        # 4. Score de pertinence combiné
        base_score = doc.get("leak_score", 0)
        bf_bonus = bf_analysis["total_score"] // 2 if is_bf else 0
        combined_score = min(base_score + bf_bonus, 100)

        # 5. Déterminer le statut heuristique
        if combined_score >= 70:
            heuristic_status = "suspected_leak"
        elif combined_score >= 40:
            heuristic_status = "low_confidence"
        else:
            heuristic_status = "not_relevant"

        # 6. Construire le document enrichi
        preprocessed = {
            # Identifiants
            "url": url,
            "url_hash": url_hash,
            "title": title,
            # Contenu nettoyé (pour BERT)
            "cleaned_content": cleaned_content[:10000],
            # Contenu original tronqué (pour archivage)
            "original_content": content[:50000],
            # IOCs enrichis
            "iocs": iocs,
            "ioc_count": ioc_count,
            # Mots-clés
            "keywords_found": doc.get("keywords_found", []),
            "keyword_count": doc.get("keyword_count", 0),
            # Scores
            "leak_score": combined_score,
            "bf_score": bf_analysis["total_score"],
            # Analyse BF
            "is_bf_related": is_bf,
            "bf_analysis": bf_analysis if is_bf else None,
            # Statut heuristique
            "heuristic_status": heuristic_status,
            # Métadonnées
            "source_type": doc.get("source_type", "onion"),
            "depth": doc.get("depth", 0),
            "spider_name": doc.get("spider_name", ""),
            "scraped_at": doc.get("scraped_at"),
            "preprocessed_at": datetime.utcnow().isoformat() + "Z",
        }

        return preprocessed

    def run(self):
        """Boucle principale du preprocessor."""
        logger.info("Listening for messages on '%s'...", KAFKA_TOPIC_INPUT)

        try:
            for message in self.consumer:
                try:
                    doc = message.value

                    # Validation minimale
                    if not doc.get("url") or not doc.get("content"):
                        logger.warning("Message invalide (url/content manquant)")
                        self.consumer.commit()
                        continue

                    # Prétraitement
                    result = self.process_document(doc)
                    self.processed_count += 1

                    if result["is_bf_related"]:
                        self.bf_count += 1

                    # Publier vers preprocessed_documents
                    # On publie TOUT, mais le BERT classifier filtrera
                    self.producer.send(KAFKA_TOPIC_OUTPUT, value=result)
                    self.producer.flush()

                    # Mettre à jour le statut dans MongoDB
                    self.urls_col.update_one(
                        {"url_hash": result["url_hash"]},
                        {"$set": {
                            "status": "preprocessed",
                            "heuristic_status": result["heuristic_status"],
                            "leak_score": result["leak_score"],
                            "is_bf_related": result["is_bf_related"],
                            "preprocessed_at": datetime.utcnow(),
                        }},
                    )

                    # Log
                    emoji = "🚨" if result.get("bf_analysis", {}).get("sensitivity_level") == "critical" else \
                            "⚠️" if result["is_bf_related"] else "✔"
                    logger.info(
                        "%s Preprocessed: %s | score=%d | bf=%s | status=%s",
                        emoji,
                        result["url"][:50],
                        result["leak_score"],
                        result["is_bf_related"],
                        result["heuristic_status"],
                    )

                    # Progression
                    if self.processed_count % 10 == 0:
                        logger.info(
                            "📊 Progress: %d processed | %d BF-related",
                            self.processed_count, self.bf_count,
                        )

                    self.consumer.commit()

                except Exception as e:
                    logger.error("Error processing message: %s", e, exc_info=True)
                    self.consumer.commit()

        except KeyboardInterrupt:
            logger.info("Preprocessor stopped by user")
        finally:
            self.consumer.close()
            self.producer.close()
            self.mongo.close()
            logger.info(
                "Preprocessor shutdown | processed=%d | bf_related=%d",
                self.processed_count, self.bf_count,
            )


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    Preprocessor().run()