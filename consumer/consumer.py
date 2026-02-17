#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Robust-Scraper — Consumer Final
Consomme 'classified_documents' depuis Kafka et :
  - Stocke les résultats dans MongoDB (collection 'leaks')
  - Crée des alertes pour les fuites critiques BF
  - Met à jour le statut final des URLs

Author: ANSSI Burkina Faso
Version: 2.0
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Optional

from kafka import KafkaConsumer
from pymongo import MongoClient

# ============================================================================
# CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s [consumer] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092").split(",")
KAFKA_TOPIC_INPUT = os.getenv("KAFKA_TOPIC_INPUT", "classified_documents")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "consumer-final-group")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:ChangeMe789@mongodb:27017/")
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "robust_scraper")


# ============================================================================
# MONGODB CLIENT
# ============================================================================

class MongoDBStore:
    """Gestion du stockage MongoDB pour les leaks et alertes."""

    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[MONGO_DATABASE]
        self.leaks = self.db["leaks"]
        self.alerts = self.db["alerts"]
        self.urls = self.db["urls_to_scrape"]

        # Index pour optimiser les requêtes du dashboard
        self.leaks.create_index("url_hash", unique=True)
        self.leaks.create_index("is_bf_related")
        self.leaks.create_index("final_status")
        self.leaks.create_index("leak_score")
        self.leaks.create_index("created_at")
        self.alerts.create_index("created_at")
        self.alerts.create_index("status")

        logger.info("✔ MongoDB connected")

    def store_leak(self, doc: Dict) -> Optional[str]:
        """Stocke un document classifié dans la collection leaks."""
        url_hash = doc.get("url_hash")
        if not url_hash:
            logger.warning("Document sans url_hash, ignoré")
            return None

        # Document MongoDB
        leak_doc = {
            "url": doc.get("url"),
            "url_hash": url_hash,
            "title": doc.get("title", ""),
            "content": doc.get("content", ""),
            "cleaned_content": doc.get("cleaned_content", ""),
            # Scores
            "leak_score": doc.get("leak_score", 0),
            "bf_score": doc.get("bf_score", 0),
            # Classification
            "final_status": doc.get("final_status", "unknown"),
            "bert_prediction": doc.get("bert_prediction", {}),
            "heuristic_status": doc.get("heuristic_status", "unknown"),
            # BF
            "is_bf_related": doc.get("is_bf_related", False),
            "bf_analysis": doc.get("bf_analysis"),
            # IOCs
            "iocs": doc.get("iocs", {}),
            "ioc_count": doc.get("ioc_count", 0),
            "keywords_found": doc.get("keywords_found", []),
            "keyword_count": doc.get("keyword_count", 0),
            # Métadonnées
            "source_type": doc.get("source_type", "onion"),
            "depth": doc.get("depth", 0),
            "scraped_at": doc.get("scraped_at"),
            "preprocessed_at": doc.get("preprocessed_at"),
            "classified_at": doc.get("classified_at"),
            # Timestamps MongoDB
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        # Upsert
        result = self.leaks.update_one(
            {"url_hash": url_hash},
            {"$set": leak_doc},
            upsert=True,
        )

        # Mettre à jour le statut de l'URL
        self.urls.update_one(
            {"url_hash": url_hash},
            {"$set": {
                "status": "completed",
                "final_status": doc.get("final_status"),
                "completed_at": datetime.utcnow(),
            }},
        )

        return str(result.upserted_id or url_hash)

    def create_alert(self, doc: Dict):
        """Crée une alerte pour les fuites critiques BF."""
        bf_analysis = doc.get("bf_analysis", {}) or {}

        alert = {
            "leak_url_hash": doc.get("url_hash"),
            "url": doc.get("url"),
            "severity": bf_analysis.get("sensitivity_level", "high"),
            "type": bf_analysis.get("data_type", "unknown"),
            "message": f"BF LEAK DETECTED: {doc.get('url', 'N/A')}",
            "final_status": doc.get("final_status"),
            "bert_label": doc.get("bert_prediction", {}).get("predicted_label"),
            "bert_confidence": doc.get("bert_prediction", {}).get("confidence"),
            "bf_score": doc.get("bf_score", 0),
            "leak_score": doc.get("leak_score", 0),
            "ioc_count": doc.get("ioc_count", 0),
            "cnib_count": len(bf_analysis.get("cnib_numbers", [])),
            "phone_count": len(bf_analysis.get("phone_numbers", [])),
            "created_at": datetime.utcnow(),
            "status": "open",
        }

        self.alerts.insert_one(alert)
        logger.warning(
            "🚨 ALERT created | type=%s | severity=%s | url=%s",
            alert["type"],
            alert["severity"],
            doc.get("url", "N/A")[:60],
        )


# ============================================================================
# CONSUMER SERVICE
# ============================================================================

class FinalConsumer:
    """Consumer final : stockage MongoDB + alertes."""

    def __init__(self):
        logger.info("=" * 70)
        logger.info("Robust-Scraper Consumer Final Starting")
        logger.info("Input: %s", KAFKA_TOPIC_INPUT)
        logger.info("=" * 70)

        self.consumer = KafkaConsumer(
            KAFKA_TOPIC_INPUT,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=KAFKA_GROUP_ID,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            max_poll_interval_ms=300_000,
        )

        self.store = MongoDBStore()

        # Stats
        self.total = 0
        self.leaks = 0
        self.suspected = 0
        self.alerts_created = 0

        logger.info("✔ Consumer ready")

    def run(self):
        """Boucle principale."""
        logger.info("Listening on '%s'...", KAFKA_TOPIC_INPUT)

        try:
            for message in self.consumer:
                try:
                    doc = message.value
                    final_status = doc.get("final_status", "unknown")

                    # Stocker dans MongoDB
                    leak_id = self.store.store_leak(doc)

                    if leak_id:
                        self.total += 1

                        if final_status == "confirmed_leak":
                            self.leaks += 1
                        elif final_status == "suspected_leak":
                            self.suspected += 1

                        # Créer une alerte si BF-related et critique
                        is_bf = doc.get("is_bf_related", False)
                        bf_analysis = doc.get("bf_analysis", {}) or {}
                        sensitivity = bf_analysis.get("sensitivity_level", "low")

                        if is_bf and sensitivity in ("critical", "high"):
                            self.store.create_alert(doc)
                            self.alerts_created += 1

                        # Log
                        emoji = "🔴" if final_status == "confirmed_leak" else \
                                "🟡" if final_status == "suspected_leak" else "🟢"
                        logger.info(
                            "%s Stored: %s | status=%s | bf=%s | score=%d",
                            emoji,
                            doc.get("url", "N/A")[:50],
                            final_status,
                            is_bf,
                            doc.get("leak_score", 0),
                        )

                    # Progression
                    if self.total % 10 == 0 and self.total > 0:
                        logger.info(
                            "📊 Total: %d | Leaks: %d | Suspected: %d | Alerts: %d",
                            self.total, self.leaks, self.suspected, self.alerts_created,
                        )

                except Exception as e:
                    logger.error("Error: %s", e, exc_info=True)

        except KeyboardInterrupt:
            logger.info("Consumer stopped")
        finally:
            self.consumer.close()
            self.store.client.close()
            logger.info(
                "Shutdown | total=%d | leaks=%d | suspected=%d | alerts=%d",
                self.total, self.leaks, self.suspected, self.alerts_created,
            )


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    FinalConsumer().run()