"""
Robust-Scraper — Pipelines
Pipeline de nettoyage et publication vers Kafka (topic: raw_documents)
Author: ANSSI Burkina Faso
"""

import json
import logging
import hashlib
from datetime import datetime

from kafka import KafkaProducer
from pymongo import MongoClient
from scrapy.exceptions import DropItem

logger = logging.getLogger(__name__)


# =============================================================================
# PIPELINE 1 : NETTOYAGE & VALIDATION
# =============================================================================

class CleaningPipeline:
    """
    Valide et nettoie les items avant publication.
    - Vérifie les champs obligatoires
    - Déduplique via MongoDB (url_hash)
    - Limite la taille du contenu
    """

    MAX_CONTENT_LENGTH = 50_000  # 50k caractères max

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get("MONGO_URI"),
            mongo_db=crawler.settings.get("MONGO_DATABASE"),
        )

    def open_spider(self, spider):
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        self.urls_col = self.db["urls_to_scrape"]
        logger.info("✔ CleaningPipeline: MongoDB connected")

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        # --- Validation des champs obligatoires ---
        if not item.get("url") or not item.get("content"):
            raise DropItem(f"Missing url or content: {item.get('url', 'N/A')}")

        # --- Déduplication ---
        url_hash = item["url_hash"]
        existing = self.urls_col.find_one(
            {"url_hash": url_hash, "status": {"$in": ["processing", "completed"]}}
        )
        if existing:
            raise DropItem(f"URL already processed: {url_hash[:12]}...")

        # --- Marquer comme processing dans MongoDB ---
        self.urls_col.update_one(
            {"url_hash": url_hash},
            {"$set": {
                "url": item["url"],
                "status": "processing",
                "spider": item.get("spider_name", "unknown"),
                "started_at": datetime.utcnow(),
            }},
            upsert=True,
        )

        # --- Tronquer le contenu ---
        if len(item.get("content", "")) > self.MAX_CONTENT_LENGTH:
            item["content"] = item["content"][:self.MAX_CONTENT_LENGTH]

        return item


# =============================================================================
# PIPELINE 2 : PUBLICATION KAFKA → raw_documents
# =============================================================================

class KafkaPipeline:
    """
    Publie les documents nettoyés dans le topic Kafka 'raw_documents'.
    Chaque message contient le document brut + IOCs + métadonnées.
    """

    def __init__(self, kafka_servers, kafka_topic):
        self.kafka_servers = kafka_servers
        self.kafka_topic = kafka_topic

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            kafka_servers=crawler.settings.get("KAFKA_BOOTSTRAP_SERVERS"),
            kafka_topic=crawler.settings.get("KAFKA_TOPIC_RAW"),
        )

    def open_spider(self, spider):
        self.producer = KafkaProducer(
            bootstrap_servers=self.kafka_servers.split(","),
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            compression_type="gzip",
            acks="all",
            retries=5,
        )
        logger.info("✔ KafkaPipeline: Producer ready → topic '%s'", self.kafka_topic)

    def close_spider(self, spider):
        self.producer.flush()
        self.producer.close()
        logger.info("✔ KafkaPipeline: Producer closed")

    def process_item(self, item, spider):
        # Construire le message Kafka
        message = {
            "url": item["url"],
            "url_hash": item["url_hash"],
            "title": item.get("title", ""),
            "content": item["content"],
            "raw_html_length": item.get("raw_html_length", 0),
            "links_found": item.get("links_found", []),
            "source_type": item.get("source_type", "onion"),
            "scraped_at": item.get("scraped_at", datetime.utcnow().isoformat() + "Z"),
            "spider_name": item.get("spider_name", "onion_spider"),
            "depth": item.get("depth", 0),
            "iocs": item.get("iocs", {}),
            "ioc_count": item.get("ioc_count", 0),
            "keywords_found": item.get("keywords_found", []),
            "keyword_count": item.get("keyword_count", 0),
            "leak_score": item.get("leak_score", 0),
            "http_status": item.get("http_status", 200),
        }

        self.producer.send(self.kafka_topic, value=message)

        logger.info(
            "→ Published to %s: %s (score=%d, iocs=%d)",
            self.kafka_topic,
            item["url"][:60],
            message["leak_score"],
            message["ioc_count"],
        )

        return item