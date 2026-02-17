"""
Robust-Scraper — Onion Spider
Spider Scrapy pour le crawling et scraping de sites .onion via Tor
Author: ANSSI Burkina Faso
Version: 2.0
"""

import re
import os
import time
import hashlib
import logging
from datetime import datetime
from pathlib import Path

import scrapy
from darkweb_scraper.items import DarkWebDocument

logger = logging.getLogger(__name__)


# =============================================================================
# IOC PATTERNS (Indicators of Compromise)
# =============================================================================

IOC_PATTERNS = {
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "ipv4": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "md5": re.compile(r"\b[a-fA-F0-9]{32}\b"),
    "sha1": re.compile(r"\b[a-fA-F0-9]{40}\b"),
    "sha256": re.compile(r"\b[a-fA-F0-9]{64}\b"),
    "bitcoin": re.compile(r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b"),
    "onion_url": re.compile(r"[a-z2-7]{16,56}\.onion"),
}


class OnionSpider(scrapy.Spider):
    """
    Spider principal pour la collecte sur le Dark Web.

    Fonctionnement :
    1. Charge les URLs .onion depuis un fichier de configuration
    2. Scrape chaque page via le réseau Tor (proxy Privoxy)
    3. Extrait le contenu textuel, les liens et les IOCs
    4. Publie les résultats dans Kafka via le KafkaPipeline

    Le spider suit les liens internes de chaque site jusqu'à
    une profondeur maximale configurable (DEPTH_LIMIT).
    """

    name = "onion_spider"
    
    # Paramètres du spider
    custom_settings = {
        "DEPTH_LIMIT": int(os.getenv("DEPTH_LIMIT", 2)),
        "CLOSESPIDER_PAGECOUNT": int(os.getenv("MAX_PAGES", 500)),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keywords = self._load_keywords()
        self.pages_scraped = 0
        self.start_time = time.time()
        logger.info("Spider '%s' initialized with %d keywords", self.name, len(self.keywords))

    # =========================================================================
    # URLS DE DEPART
    # =========================================================================

    def start_requests(self):
        """
        Charge les URLs .onion depuis le fichier de configuration
        et génère les requêtes initiales.
        """
        urls_file = self.settings.get(
            "ONION_URLS_FILE",
            os.getenv("ONION_URLS_FILE", "/app/onion_urls.txt")
        )

        urls = self._load_urls(urls_file)

        if not urls:
            logger.error("Aucune URL à scraper dans %s", urls_file)
            return

        logger.info("Démarrage du crawl avec %d URLs", len(urls))

        for url in urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                errback=self.errback,
                meta={"depth": 0, "source_url": url},
                dont_filter=False,
            )

    # =========================================================================
    # PARSING PRINCIPAL
    # =========================================================================

    def parse(self, response):
        """
        Parse une page du Dark Web :
        1. Extraction du contenu textuel
        2. Détection des IOCs
        3. Recherche de mots-clés
        4. Calcul du score heuristique
        5. Découverte de liens pour le crawling en profondeur
        """
        self.pages_scraped += 1
        start = time.time()
        url = response.url
        depth = response.meta.get("depth", 0)

        logger.info(
            "Scraping [depth=%d] [#%d]: %s",
            depth, self.pages_scraped, url[:80]
        )

        # --- Extraction du contenu ---
        title = response.css("title::text").get(default="")[:200]
        # Extraire le texte visible en supprimant scripts et styles
        body = response.css("body")
        if body:
            # Supprimer les scripts et styles
            text_parts = body.css("*:not(script):not(style)::text").getall()
            text = " ".join(t.strip() for t in text_parts if t.strip())
        else:
            text = response.text[:50000]

        if not text or len(text) < 50:
            logger.debug("Contenu trop court, page ignorée: %s", url[:60])
            return

        # --- Détection des IOCs ---
        iocs = {}
        for ioc_name, pattern in IOC_PATTERNS.items():
            matches = list(set(pattern.findall(text)))[:100]
            if matches:
                iocs[ioc_name] = matches

        ioc_count = sum(len(v) for v in iocs.values())

        # --- Recherche de mots-clés ---
        text_lower = text.lower()
        keywords_found = [k for k in self.keywords if k in text_lower]

        # --- Calcul du score heuristique ---
        leak_score = self._compute_leak_score(iocs, keywords_found)

        # --- Extraction des liens pour crawl en profondeur ---
        links = self._extract_onion_links(response)

        # --- Construction de l'item ---
        url_hash = hashlib.sha256(url.encode()).hexdigest()
        elapsed = time.time() - start

        item = DarkWebDocument()
        item["url"] = url
        item["url_hash"] = url_hash
        item["title"] = title
        item["content"] = text[:50000]
        item["raw_html_length"] = len(response.text)
        item["links_found"] = links[:50]  # Max 50 liens
        item["source_type"] = "onion"
        item["scraped_at"] = datetime.utcnow().isoformat() + "Z"
        item["spider_name"] = self.name
        item["depth"] = depth
        item["iocs"] = iocs
        item["ioc_count"] = ioc_count
        item["keywords_found"] = keywords_found
        item["keyword_count"] = len(keywords_found)
        item["leak_score"] = leak_score
        item["http_status"] = response.status
        item["response_time"] = round(elapsed, 2)

        yield item

        # --- Suivre les liens .onion découverts ---
        depth_limit = self.custom_settings.get("DEPTH_LIMIT", 2)
        if depth < depth_limit:
            for link in links[:10]:  # Max 10 liens suivis par page
                yield scrapy.Request(
                    url=link,
                    callback=self.parse,
                    errback=self.errback,
                    meta={"depth": depth + 1, "source_url": url},
                    dont_filter=True,
                )

    # =========================================================================
    # MÉTHODES UTILITAIRES
    # =========================================================================

    def _compute_leak_score(self, iocs: dict, keywords_found: list) -> int:
        """
        Calcule un score heuristique de probabilité de fuite.
        Score entre 0 et 100.
        """
        score = 0

        # Points pour les IOCs trouvés
        if iocs.get("email"):
            score += min(len(iocs["email"]) * 2, 15)
        if iocs.get("ipv4"):
            score += min(len(iocs["ipv4"]) * 2, 10)
        if iocs.get("md5") or iocs.get("sha1") or iocs.get("sha256"):
            score += 15
        if iocs.get("bitcoin"):
            score += 10

        # Points pour les mots-clés
        score += min(len(keywords_found) * 5, 30)

        # Bonus si combinaison d'indicateurs
        if len(iocs) >= 3:
            score += 10
        if len(keywords_found) >= 3 and len(iocs) >= 2:
            score += 10

        return min(score, 100)

    def _extract_onion_links(self, response) -> list:
        """
        Extrait les liens .onion de la page pour le crawl en profondeur.
        """
        links = []
        for href in response.css("a::attr(href)").getall():
            # Liens absolus .onion
            if ".onion" in href and href.startswith("http"):
                links.append(href)
            # Liens relatifs
            elif href.startswith("/"):
                links.append(response.urljoin(href))

        return list(set(links))

    def _load_keywords(self) -> list:
        """Charge les mots-clés de détection depuis le fichier."""
        keywords_file = os.getenv("KEYWORDS_FILE", "/app/keywords/leak_keywords.txt")
        try:
            with open(keywords_file, "r", encoding="utf-8") as f:
                keywords = [
                    k.strip().lower()
                    for k in f
                    if k.strip() and not k.startswith("#")
                ]
            logger.info("✔ %d keywords loaded from %s", len(keywords), keywords_file)
            return keywords
        except FileNotFoundError:
            logger.warning("Keywords file not found, using fallback list")
            return [
                "leak", "password", "dump", "database", "breach", "hack",
                "credentials", "exploit", "ransomware", "data breach",
                "burkina", "ouagadougou", "cnib", "orange burkina",
            ]

    def _load_urls(self, filepath: str) -> list:
        """Charge les URLs depuis le fichier."""
        urls = []
        path = Path(filepath)
        if not path.exists():
            logger.error("URLs file not found: %s", filepath)
            return urls

        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    urls.append(line)

        logger.info("✔ %d URLs loaded from %s", len(urls), filepath)
        return urls

    # =========================================================================
    # ERROR HANDLING
    # =========================================================================

    def errback(self, failure):
        """Gestion des erreurs de requête."""
        url = failure.request.url
        logger.warning("Request failed: %s — %s", url[:60], failure.getErrorMessage()[:100])

    def closed(self, reason):
        """Appelé quand le spider se termine."""
        elapsed = time.time() - self.start_time
        logger.info(
            "Spider '%s' closed: %d pages scraped in %.1fs (reason: %s)",
            self.name, self.pages_scraped, elapsed, reason,
        )