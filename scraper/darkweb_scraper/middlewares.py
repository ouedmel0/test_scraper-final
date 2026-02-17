"""
Robust-Scraper — Middlewares
Middleware Tor/Privoxy pour anonymisation et rotation de User-Agent
Author: ANSSI Burkina Faso
"""

import random
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# TOR PROXY MIDDLEWARE
# =============================================================================

class TorProxyMiddleware:
    """
    Middleware Scrapy qui route toutes les requêtes via Tor/Privoxy.
    
    Flux : Spider → Privoxy (port 8118) → Tor SOCKS5 (port 9050) → Dark Web
    
    Ce middleware remplace le HttpProxyMiddleware par défaut de Scrapy
    pour garantir que TOUTES les requêtes transitent par le réseau Tor.
    """

    def __init__(self, http_proxy, https_proxy):
        self.http_proxy = http_proxy
        self.https_proxy = https_proxy

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            http_proxy=crawler.settings.get("HTTP_PROXY"),
            https_proxy=crawler.settings.get("HTTPS_PROXY"),
        )

    def process_request(self, request, spider):
        """Applique le proxy Tor à chaque requête sortante."""
        request.meta["proxy"] = self.http_proxy
        logger.debug("Proxy Tor appliqué: %s → %s", request.url[:60], self.http_proxy)


# =============================================================================
# USER-AGENT ROTATION MIDDLEWARE
# =============================================================================

# Pool de User-Agents réalistes pour éviter le fingerprinting
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",

    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) "
    "Gecko/20100101 Firefox/121.0",

    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.2 Safari/605.1.15",

    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",

    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
]


class RotateUserAgentMiddleware:
    """
    Middleware qui assigne un User-Agent aléatoire à chaque requête
    pour réduire l'empreinte digitale du scraper.
    """

    def process_request(self, request, spider):
        ua = random.choice(USER_AGENTS)
        request.headers["User-Agent"] = ua