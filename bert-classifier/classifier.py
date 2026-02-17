#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Robust-Scraper — BERT Classifier Service
Consomme 'preprocessed_documents' depuis Kafka, classifie avec mBERT,
publie les résultats dans 'classified_documents'.

Supporte :
  - Modèle 3 classes : fuite_confirmee / suspicion / non_fuite
  - Modèle 2 classes : leak / no_leak (fallback)

Author: ANSSI Burkina Faso
Version: 2.0
"""

import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional

import torch
import numpy as np
from transformers import BertTokenizer, BertForSequenceClassification

from kafka import KafkaConsumer, KafkaProducer
from pymongo import MongoClient

# ============================================================================
# CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s [bert-classifier] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092").split(",")
KAFKA_TOPIC_INPUT = os.getenv("KAFKA_TOPIC_INPUT", "preprocessed_documents")
KAFKA_TOPIC_OUTPUT = os.getenv("KAFKA_TOPIC_OUTPUT", "classified_documents")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "bert-classifier-group")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:ChangeMe789@mongodb:27017/")
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "robust_scraper")

MODEL_PATH = os.getenv("MODEL_PATH", "/app/model")
MAX_LENGTH = int(os.getenv("MAX_LENGTH", 512))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 8))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 0.6))

# Labels selon le nombre de classes du modèle
LABELS_3_CLASSES = {0: "confirmed_leak", 1: "suspected_leak", 2: "not_leak"}
LABELS_2_CLASSES = {0: "not_leak", 1: "leak"}


# ============================================================================
# BERT INFERENCE ENGINE
# ============================================================================

class BERTInferenceEngine:
    """
    Moteur d'inférence BERT pour la classification de documents.
    Charge le modèle fine-tuné et effectue les prédictions.
    """

    def __init__(self, model_path: str, max_length: int = 512):
        self.max_length = max_length
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.tokenizer = None
        self.num_labels = None
        self.labels_map = None

        self._load_model(model_path)

    def _load_model(self, model_path: str):
        """Charge le modèle et le tokenizer."""
        try:
            logger.info("Loading BERT model from %s...", model_path)
            logger.info("Device: %s", self.device)

            # Charger le tokenizer
            self.tokenizer = BertTokenizer.from_pretrained(model_path)

            # Charger le modèle
            self.model = BertForSequenceClassification.from_pretrained(model_path)
            self.model.to(self.device)
            self.model.eval()

            # Déterminer le nombre de classes
            self.num_labels = self.model.config.num_labels
            self.labels_map = LABELS_3_CLASSES if self.num_labels == 3 else LABELS_2_CLASSES

            logger.info(
                "✔ Model loaded: %d labels, %s",
                self.num_labels,
                list(self.labels_map.values()),
            )

        except Exception as e:
            logger.error("Failed to load model from %s: %s", model_path, e)
            logger.warning("⚠️ Falling back to base mBERT (untrained)")
            self._load_fallback()

    def _load_fallback(self):
        """Charge le modèle mBERT de base si pas de modèle fine-tuné."""
        model_name = "bert-base-multilingual-cased"
        logger.info("Loading fallback model: %s", model_name)

        self.tokenizer = BertTokenizer.from_pretrained(model_name)
        self.model = BertForSequenceClassification.from_pretrained(
            model_name, num_labels=3
        )
        self.model.to(self.device)
        self.model.eval()
        self.num_labels = 3
        self.labels_map = LABELS_3_CLASSES

        logger.warning("⚠️ Using untrained fallback model — predictions won't be accurate")

    def predict(self, text: str) -> Dict:
        """
        Classifie un texte et retourne la prédiction avec les scores de confiance.
        """
        start = time.time()

        # Tokenization avec stratégie head+tail pour les longs documents
        if len(text) > 1000:
            # Garder les 255 premiers et 255 derniers tokens
            tokens = self.tokenizer.encode(text, add_special_tokens=False)
            if len(tokens) > self.max_length - 2:  # -2 pour [CLS] et [SEP]
                half = (self.max_length - 2) // 2
                tokens = tokens[:half] + tokens[-half:]
                text_truncated = self.tokenizer.decode(tokens)
            else:
                text_truncated = text
        else:
            text_truncated = text

        inputs = self.tokenizer(
            text_truncated,
            return_tensors="pt",
            max_length=self.max_length,
            truncation=True,
            padding="max_length",
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Inférence
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1).cpu().numpy()[0]

        # Résultat
        predicted_class = int(np.argmax(probs))
        confidence = float(probs[predicted_class])
        elapsed_ms = (time.time() - start) * 1000

        result = {
            "predicted_label": self.labels_map[predicted_class],
            "predicted_class": predicted_class,
            "confidence": round(confidence, 4),
            "probabilities": {
                self.labels_map[i]: round(float(p), 4)
                for i, p in enumerate(probs)
            },
            "inference_time_ms": round(elapsed_ms, 1),
            "model_type": f"mBERT-{self.num_labels}classes",
        }

        return result

    def predict_batch(self, texts: List[str]) -> List[Dict]:
        """Classifie un batch de textes."""
        return [self.predict(text) for text in texts]


# ============================================================================
# CLASSIFIER SERVICE
# ============================================================================

class BERTClassifierService:
    """
    Service Kafka qui consomme les documents prétraités,
    les classifie avec BERT et publie les résultats.
    """

    def __init__(self):
        logger.info("=" * 70)
        logger.info("🧠 Robust-Scraper BERT Classifier Starting")
        logger.info("Input:  %s", KAFKA_TOPIC_INPUT)
        logger.info("Output: %s", KAFKA_TOPIC_OUTPUT)
        logger.info("Model:  %s", MODEL_PATH)
        logger.info("=" * 70)

        # Charger le modèle BERT
        self.engine = BERTInferenceEngine(MODEL_PATH, MAX_LENGTH)

        # Kafka consumer
        self.consumer = KafkaConsumer(
            KAFKA_TOPIC_INPUT,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=KAFKA_GROUP_ID,
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            max_poll_interval_ms=600_000,  # 10 min (BERT peut être lent)
        )

        # Kafka producer
        self.producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            acks="all",
            retries=5,
        )

        # MongoDB
        self.mongo = MongoClient(MONGO_URI)
        self.db = self.mongo[MONGO_DATABASE]

        # Stats
        self.classified_count = 0
        self.leak_count = 0
        self.suspected_count = 0

        logger.info("✔ BERT Classifier ready")

    def classify_document(self, doc: Dict) -> Dict:
        """
        Classifie un document et retourne le message enrichi
        prêt pour publication dans classified_documents.
        """
        # Texte à classifier (nettoyé par le preprocessor)
        text = doc.get("cleaned_content", doc.get("original_content", ""))

        if not text or len(text) < 20:
            return self._build_output(doc, {
                "predicted_label": "not_leak",
                "confidence": 0.0,
                "probabilities": {},
                "inference_time_ms": 0,
                "model_type": "skipped_too_short",
            })

        # Inférence BERT
        prediction = self.engine.predict(text)

        return self._build_output(doc, prediction)

    def _build_output(self, doc: Dict, prediction: Dict) -> Dict:
        """Construit le message de sortie pour classified_documents."""

        # Déterminer le statut final en combinant heuristique + BERT
        heuristic_status = doc.get("heuristic_status", "unknown")
        bert_label = prediction["predicted_label"]
        confidence = prediction.get("confidence", 0)

        # Logique de décision combinée
        if bert_label == "confirmed_leak" and confidence >= CONFIDENCE_THRESHOLD:
            final_status = "confirmed_leak"
        elif bert_label == "suspected_leak" or (
            bert_label == "leak" and confidence < 0.8
        ):
            final_status = "suspected_leak"
        elif bert_label in ("not_leak",) and confidence >= CONFIDENCE_THRESHOLD:
            final_status = "not_leak"
        else:
            # En cas de doute, utiliser le statut heuristique
            final_status = heuristic_status if heuristic_status != "unknown" else "suspected_leak"

        return {
            # Identifiants
            "url": doc.get("url"),
            "url_hash": doc.get("url_hash"),
            "title": doc.get("title", ""),
            # Contenu
            "content": doc.get("original_content", "")[:50000],
            "cleaned_content": doc.get("cleaned_content", "")[:10000],
            # Scores
            "leak_score": doc.get("leak_score", 0),
            "bf_score": doc.get("bf_score", 0),
            # Analyse BF
            "is_bf_related": doc.get("is_bf_related", False),
            "bf_analysis": doc.get("bf_analysis"),
            # IOCs
            "iocs": doc.get("iocs", {}),
            "ioc_count": doc.get("ioc_count", 0),
            "keywords_found": doc.get("keywords_found", []),
            "keyword_count": doc.get("keyword_count", 0),
            # Classification BERT
            "bert_prediction": prediction,
            "final_status": final_status,
            # Métadonnées
            "heuristic_status": heuristic_status,
            "source_type": doc.get("source_type", "onion"),
            "depth": doc.get("depth", 0),
            "scraped_at": doc.get("scraped_at"),
            "preprocessed_at": doc.get("preprocessed_at"),
            "classified_at": datetime.utcnow().isoformat() + "Z",
        }

    def run(self):
        """Boucle principale du classifier."""
        logger.info("Listening for messages on '%s'...", KAFKA_TOPIC_INPUT)

        try:
            for message in self.consumer:
                try:
                    doc = message.value
                    url = doc.get("url", "N/A")

                    # Classifier le document
                    result = self.classify_document(doc)
                    self.classified_count += 1

                    # Compter par catégorie
                    if result["final_status"] == "confirmed_leak":
                        self.leak_count += 1
                    elif result["final_status"] == "suspected_leak":
                        self.suspected_count += 1

                    # Publier vers classified_documents
                    self.producer.send(KAFKA_TOPIC_OUTPUT, value=result)
                    self.producer.flush()

                    # Log
                    pred = result["bert_prediction"]
                    emoji = "🔴" if result["final_status"] == "confirmed_leak" else \
                            "🟡" if result["final_status"] == "suspected_leak" else "🟢"
                    logger.info(
                        "%s Classified: %s | BERT=%s (%.1f%%) | final=%s | time=%.0fms",
                        emoji,
                        url[:50],
                        pred.get("predicted_label", "?"),
                        pred.get("confidence", 0) * 100,
                        result["final_status"],
                        pred.get("inference_time_ms", 0),
                    )

                    # Progression
                    if self.classified_count % 10 == 0:
                        logger.info(
                            "📊 Stats: %d classified | %d leaks | %d suspected",
                            self.classified_count,
                            self.leak_count,
                            self.suspected_count,
                        )

                    self.consumer.commit()

                except Exception as e:
                    logger.error("Error classifying document: %s", e, exc_info=True)
                    self.consumer.commit()

        except KeyboardInterrupt:
            logger.info("Classifier stopped by user")
        finally:
            self.consumer.close()
            self.producer.close()
            self.mongo.close()
            logger.info(
                "Classifier shutdown | total=%d | leaks=%d | suspected=%d",
                self.classified_count, self.leak_count, self.suspected_count,
            )


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    BERTClassifierService().run()