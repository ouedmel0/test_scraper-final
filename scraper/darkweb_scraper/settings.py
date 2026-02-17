"""
Robust-Scraper — Scrapy Settings
Configuration du framework de collecte avec proxy Tor et pipeline Kafka
Author: ANSSI Burkina Faso
"""

import os

# =============================================================================
# SCRAPY CORE
# =============================================================================

BOT_NAME = "darkweb_scraper"
SPIDER_MODULES = ["darkweb_scraper.spiders"]
NEWSPIDER_MODULE = "darkweb_scraper.spiders"

# Respect robots.txt désactivé (Dark Web n'a pas de robots.txt)
ROBOTSTXT_OBEY = False

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "[%(levelname)s] %(asctime)s [%(name)s] %(message)s"
LOG_DATEFORMAT = "%Y-%m-%d %H:%M:%S"

# =============================================================================
# CONCURRENCE & THROTTLING
# =============================================================================

# Requêtes parallèles limitées (Tor est lent, pas la peine de flood)
CONCURRENT_REQUESTS = int(os.getenv("CONCURRENT_REQUESTS", 4))
CONCURRENT_REQUESTS_PER_DOMAIN = 2

# Délai entre requêtes (respecter le réseau Tor)
DOWNLOAD_DELAY = int(os.getenv("DOWNLOAD_DELAY", 5))
RANDOMIZE_DOWNLOAD_DELAY = True

# Timeout adapté au Dark Web (latence Tor : 3-8s par requête)
DOWNLOAD_TIMEOUT = int(os.getenv("DOWNLOAD_TIMEOUT", 60))

# Retries
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# =============================================================================
# PROXY TOR / PRIVOXY
# =============================================================================

HTTP_PROXY = os.getenv("HTTP_PROXY", "http://tor-privoxy:8118")
HTTPS_PROXY = os.getenv("HTTPS_PROXY", "http://tor-privoxy:8118")

# =============================================================================
# MIDDLEWARES
# =============================================================================

DOWNLOADER_MIDDLEWARES = {
    # Désactiver le middleware proxy par défaut
    "scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware": None,
    # Notre middleware Tor custom
    "darkweb_scraper.middlewares.TorProxyMiddleware": 350,
    # Rotation de User-Agent
    "darkweb_scraper.middlewares.RotateUserAgentMiddleware": 400,
    # Retry amélioré
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": 500,
}

# =============================================================================
# PIPELINES
# =============================================================================

ITEM_PIPELINES = {
    # Nettoyage et validation des données extraites
    "darkweb_scraper.pipelines.CleaningPipeline": 100,
    # Publication vers Kafka (topic: raw_documents)
    "darkweb_scraper.pipelines.KafkaPipeline": 300,
}

# =============================================================================
# KAFKA SETTINGS
# =============================================================================

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
KAFKA_TOPIC_RAW = os.getenv("KAFKA_TOPIC_RAW", "raw_documents")

# =============================================================================
# MONGODB (pour déduplication)
# =============================================================================

MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:ChangeMe789@mongodb:27017/")
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "robust_scraper")

# =============================================================================
# KEYWORDS FILE
# =============================================================================

KEYWORDS_FILE = os.getenv("KEYWORDS_FILE", "/app/keywords/leak_keywords.txt")

# =============================================================================
# FEED SETTINGS (désactivé, on utilise Kafka)
# =============================================================================

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"