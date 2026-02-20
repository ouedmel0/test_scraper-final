"""
Robust-Scraper — Scrapy Settings v3
Configuration avec seed_urls.json et proxy Tor/Privoxy

Author: ANSSI Burkina Faso
"""

import os

# =============================================================================
# SCRAPY CORE
# =============================================================================
BOT_NAME = "darkweb_scraper"
SPIDER_MODULES = ["darkweb_scraper.spiders"]
NEWSPIDER_MODULE = "darkweb_scraper.spiders"

ROBOTSTXT_OBEY = False

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "[%(levelname)s] %(asctime)s [%(name)s] %(message)s"
LOG_DATEFORMAT = "%Y-%m-%d %H:%M:%S"

# =============================================================================
# CONCURRENCE & THROTTLING (adapté au Dark Web via Tor)
# =============================================================================
CONCURRENT_REQUESTS = int(os.getenv("CONCURRENT_REQUESTS", 2))
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = int(os.getenv("DOWNLOAD_DELAY", 8))
RANDOMIZE_DOWNLOAD_DELAY = True
DOWNLOAD_TIMEOUT = int(os.getenv("DOWNLOAD_TIMEOUT", 60))

RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# =============================================================================
# PROXY TOR / PRIVOXY
# =============================================================================
HTTP_PROXY = os.getenv("HTTP_PROXY", "http://tor-privoxy:8118")
HTTPS_PROXY = os.getenv("HTTPS_PROXY", "http://tor-privoxy:8118")

# =============================================================================
# SEED URLS (nouveau v3 — remplace ONION_URLS_FILE)
# =============================================================================
SEED_URLS_FILE = os.getenv("SEED_URLS_FILE", "/app/config/seed_urls.json")

# =============================================================================
# MIDDLEWARES
# =============================================================================
DOWNLOADER_MIDDLEWARES = {
    "scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware": None,
    "darkweb_scraper.middlewares.TorProxyMiddleware": 350,
    "darkweb_scraper.middlewares.RotateUserAgentMiddleware": 400,
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": 500,
}

# =============================================================================
# PIPELINES
# =============================================================================
ITEM_PIPELINES = {
    "darkweb_scraper.pipelines.CleaningPipeline": 100,
    "darkweb_scraper.pipelines.KafkaPipeline": 300,
}

# =============================================================================
# KAFKA
# =============================================================================
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
KAFKA_TOPIC_RAW = os.getenv("KAFKA_TOPIC_RAW", "raw_documents")

# =============================================================================
# MONGODB (déduplication)
# =============================================================================
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:ChangeMe789@mongodb:27017/")
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "robust_scraper")

# =============================================================================
# AUTRES
# =============================================================================
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8" 