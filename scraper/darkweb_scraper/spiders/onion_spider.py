"""
Robust-Scraper — Onion Spider v3.0
Spider Scrapy pour le crawling et scraping de sites .onion via Tor
Avec injection de requêtes HTTP sur les moteurs de recherche Dark Web

Author: ANSSI Burkina Faso
Version: 3.0 — Aligned with seed_urls.json
"""

import re
import os
import json
import time
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus, urljoin

import scrapy
from darkweb_scraper.items import DarkWebDocument

logger = logging.getLogger(__name__)


# =============================================================================
# IOC PATTERNS — Enrichis pour le contexte Burkina Faso
# =============================================================================

IOC_PATTERNS = {
    # --- IOCs génériques ---
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "ipv4": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "md5": re.compile(r"\b[a-fA-F0-9]{32}\b"),
    "sha1": re.compile(r"\b[a-fA-F0-9]{40}\b"),
    "sha256": re.compile(r"\b[a-fA-F0-9]{64}\b"),
    "bitcoin": re.compile(r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b"),
    "onion_url": re.compile(r"https?://[a-z2-7]{16,56}\.onion[^\s\"'<>]*"),
    "credit_card": re.compile(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14})\b"),

    # --- IOCs spécifiques Burkina Faso ---
    "phone_bf": re.compile(r"\+226\s?[0-9]{2}\s?[0-9]{2}\s?[0-9]{2}\s?[0-9]{2}"),
    "cnib": re.compile(r"\bB[0-9]{6}[A-E]\b"),
    "email_bf": re.compile(r"[A-Za-z0-9._%+-]+@(?:gov\.bf|fasonet\.bf|onatel\.bf|orange\.bf)"),
    "gov_bf": re.compile(r"\b[a-z]+\.gov\.bf\b"),
}

# Mots-clés de contexte Burkina Faso pour le scoring
BF_CONTEXT_KEYWORDS = [
    "burkina", "burkina faso", "ouagadougou", "bobo-dioulasso", "bobo dioulasso",
    "koudougou", "banfora", "ouahigouya", "fada ngourma", "dédougou",
    "cnib", "cnss", "carfo", "onatel", "sonabel", "anssi",
    "coris bank", "ecobank burkina", "uba burkina", "boa burkina",
    "orange burkina", "moov burkina", "telecel faso", "fasonet",
    "gov.bf", "finances.gov.bf", "sante.gov.bf", "defense.gov.bf",
    "ministère", "fcfa", "xof",
]

# Mots-clés de leak génériques
LEAK_KEYWORDS = [
    "leak", "leaked", "dump", "dumped", "breach", "breached",
    "hack", "hacked", "credentials", "password", "passwd", "combo list",
    "database dump", "sql injection", "sqli", "fullz", "cc dump",
    "stealer log", "credential stuffing", "ransomware", "data breach",
    "exposed", "for sale", "free leak", "fresh dump",
    "mot de passe", "fuite", "piratage", "données", "base de données",
]


class OnionSpider(scrapy.Spider):
    """
    Spider v3 — Avec injection de requêtes HTTP sur les moteurs de recherche.

    Architecture de crawl en 3 phases :
      Phase 1 : Requêtes de recherche sur Ahmia/Torch/Haystak/TorDex
                 → Extraction des URLs .onion dans les résultats
      Phase 2 : Crawl des directories (Hidden Wiki, TorLinks)
                 → Découverte de nouveaux sites .onion
      Phase 3 : Crawl en profondeur des sites découverts
                 → Extraction du contenu + IOCs + scoring
    """

    name = "onion_spider"

    custom_settings = {
        "DEPTH_LIMIT": int(os.getenv("DEPTH_LIMIT", 3)),
        "CLOSESPIDER_PAGECOUNT": int(os.getenv("MAX_PAGES", 1000)),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages_scraped = 0
        self.urls_discovered = set()
        self.start_time = time.time()
        self.seed_config = self._load_seed_urls()
        logger.info(
            "Spider '%s' v3 initialized — %d BF keywords, %d leak keywords",
            self.name, len(BF_CONTEXT_KEYWORDS), len(LEAK_KEYWORDS),
        )

    # =========================================================================
    # PHASE 0 : CHARGEMENT DES SEED URLs ET GÉNÉRATION DES REQUÊTES
    # =========================================================================

    def start_requests(self):
        """
        Charge le fichier seed_urls.json et génère les requêtes HTTP
        avec les keywords injectés dans les query params.
        """
        if not self.seed_config:
            logger.error("Aucune seed URL chargée — arrêt du spider")
            return

        start_urls = self.seed_config.get("start_urls", {})

        # --- Phase 1 : Requêtes de recherche sur les moteurs ---
        for engine_key in ["ahmia_searches", "torch_searches", "haystak_searches", "tordex_searches"]:
            engine = start_urls.get(engine_key, {})
            urls = engine.get("urls", [])
            priority_val = self._priority_to_int(engine.get("priority", "MEDIUM"))

            logger.info(
                "📡 [%s] %d requêtes de recherche à lancer (priority=%s)",
                engine_key, len(urls), engine.get("priority"),
            )

            for url in urls:
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_search_results,
                    errback=self.errback,
                    priority=priority_val,
                    meta={
                        "source_type": "search_engine",
                        "engine": engine_key,
                        "depth": 0,
                    },
                    dont_filter=False,
                )

        # --- Phase 2 : Directories à crawler ---
        directories = start_urls.get("directories_to_crawl", {})
        for url in directories.get("urls", []):
            yield scrapy.Request(
                url=url,
                callback=self.parse_directory,
                errback=self.errback,
                priority=5,
                meta={"source_type": "directory", "depth": 0},
                dont_filter=False,
            )

        # --- Phase 2b : Paste sites à monitorer ---
        paste_sites = start_urls.get("paste_sites_to_monitor", {})
        for url in paste_sites.get("urls", []):
            yield scrapy.Request(
                url=url,
                callback=self.parse_paste_listing,
                errback=self.errback,
                priority=10,  # Haute priorité
                meta={"source_type": "paste_site", "depth": 0},
                dont_filter=False,
            )

        # --- Phase 2c : Forums publics ---
        forums = start_urls.get("forums_to_scrape", {})
        for url in forums.get("urls", []):
            yield scrapy.Request(
                url=url,
                callback=self.parse_forum,
                errback=self.errback,
                priority=7,
                meta={"source_type": "forum", "depth": 0},
                dont_filter=False,
            )

    # =========================================================================
    # PHASE 1 : PARSING DES RÉSULTATS DE RECHERCHE
    # =========================================================================

    def parse_search_results(self, response):
        """
        Parse les pages de résultats des moteurs de recherche Dark Web.
        Extrait les URLs .onion des résultats et lance leur crawl.
        """
        engine = response.meta.get("engine", "unknown")
        logger.info("🔍 [%s] Parsing search results: %s", engine, response.url[:80])

        # --- Extraire les URLs .onion des résultats ---
        discovered_urls = set()

        # Méthode 1 : Liens dans les balises <a href>
        for href in response.css("a::attr(href)").getall():
            if ".onion" in href:
                # Nettoyer l'URL
                clean_url = self._clean_onion_url(href)
                if clean_url:
                    discovered_urls.add(clean_url)

        # Méthode 2 : Regex dans le texte brut (certains moteurs affichent les URLs en texte)
        onion_matches = IOC_PATTERNS["onion_url"].findall(response.text)
        for match in onion_matches:
            clean_url = self._clean_onion_url(match)
            if clean_url:
                discovered_urls.add(clean_url)

        # Méthode 3 : Spécifique Ahmia — les résultats sont dans des <li> avec redirect
        if "ahmia" in engine:
            for link in response.css("li.result a::attr(href)").getall():
                if ".onion" in link:
                    discovered_urls.add(self._clean_onion_url(link))
            # Ahmia utilise aussi des redirections /search/redirect?...
            for link in response.css("a[href*='redirect']::attr(href)").getall():
                # Extraire l'URL cible du paramètre de redirection
                if "search_result=" in link:
                    target = link.split("search_result=")[-1]
                    if ".onion" in target:
                        discovered_urls.add(self._clean_onion_url(target))

        # Filtrer les URLs des moteurs de recherche eux-mêmes
        search_engine_domains = [
            "juhanurmihxlp77", "xmh57jrknzkhv6y3", "haystak5njsmn2hq",
            "tordexpmg4xy32rf", "torchdeedp3i2jig", "notevil2ebbr5xjw",
            "duckduckgogg42xj",
        ]
        discovered_urls = {
            url for url in discovered_urls
            if url and not any(se in url for se in search_engine_domains)
        }

        # Ajouter aux URLs découvertes et lancer le crawl
        new_urls = discovered_urls - self.urls_discovered
        self.urls_discovered.update(new_urls)

        logger.info(
            "🔍 [%s] %d URLs .onion découvertes (%d nouvelles)",
            engine, len(discovered_urls), len(new_urls),
        )

        for url in new_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_page,
                errback=self.errback,
                priority=8,
                meta={
                    "source_type": "discovered",
                    "discovered_from": engine,
                    "depth": 1,
                },
                dont_filter=False,
            )

        # --- Pagination : suivre les pages suivantes des résultats ---
        next_pages = response.css("a.next::attr(href), a[rel='next']::attr(href)").getall()
        for next_page in next_pages[:3]:  # Max 3 pages de résultats
            next_url = response.urljoin(next_page)
            yield scrapy.Request(
                url=next_url,
                callback=self.parse_search_results,
                errback=self.errback,
                priority=6,
                meta=response.meta,
                dont_filter=False,
            )

    # =========================================================================
    # PHASE 2a : PARSING DES DIRECTORIES
    # =========================================================================

    def parse_directory(self, response):
        """
        Parse les pages de répertoire (Hidden Wiki, TorLinks, etc.)
        pour extraire les liens .onion listés.
        """
        logger.info("📂 Parsing directory: %s", response.url[:80])

        discovered_urls = set()

        # Extraire tous les liens .onion de la page
        for href in response.css("a::attr(href)").getall():
            if ".onion" in href:
                clean_url = self._clean_onion_url(href)
                if clean_url:
                    discovered_urls.add(clean_url)

        # Regex dans le texte brut aussi
        for match in IOC_PATTERNS["onion_url"].findall(response.text):
            clean_url = self._clean_onion_url(match)
            if clean_url:
                discovered_urls.add(clean_url)

        new_urls = discovered_urls - self.urls_discovered
        self.urls_discovered.update(new_urls)

        logger.info(
            "📂 Directory: %d liens .onion extraits (%d nouveaux)",
            len(discovered_urls), len(new_urls),
        )

        for url in new_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_page,
                errback=self.errback,
                priority=5,
                meta={
                    "source_type": "directory_discovered",
                    "discovered_from": response.url,
                    "depth": 1,
                },
                dont_filter=False,
            )

        # Aussi parser cette page elle-même comme contenu
        yield from self._process_page_content(response)

    # =========================================================================
    # PHASE 2b : PARSING DES PASTE SITES
    # =========================================================================

    def parse_paste_listing(self, response):
        """
        Parse la page de listing d'un paste site (StrongHold, etc.)
        pour extraire les liens vers les pastes individuels.
        """
        logger.info("📋 Parsing paste listing: %s", response.url[:80])

        # Extraire les liens vers les pastes individuels
        paste_links = set()
        for href in response.css("a::attr(href)").getall():
            full_url = response.urljoin(href)
            if ".onion" in full_url:
                paste_links.add(full_url)

        logger.info("📋 %d paste links trouvés", len(paste_links))

        for url in paste_links:
            yield scrapy.Request(
                url=url,
                callback=self.parse_page,
                errback=self.errback,
                priority=9,  # Haute priorité pour les pastes
                meta={
                    "source_type": "paste",
                    "discovered_from": response.url,
                    "depth": 1,
                },
                dont_filter=False,
            )

    # =========================================================================
    # PHASE 2c : PARSING DES FORUMS
    # =========================================================================

    def parse_forum(self, response):
        """
        Parse un forum public (Dread, DEF CON, etc.)
        Extrait les threads/topics et les crawle.
        """
        logger.info("💬 Parsing forum: %s", response.url[:80])

        # Vérifier qu'on n'a pas été redirigé vers une page de login
        if self._is_login_page(response):
            logger.warning("⚠️ Login required, skipping: %s", response.url[:80])
            return

        # Extraire les liens vers les threads
        thread_links = set()
        for href in response.css("a::attr(href)").getall():
            full_url = response.urljoin(href)
            # Filtrer les liens qui ressemblent à des threads
            if ".onion" in full_url and any(
                p in full_url for p in
                ["/thread", "/topic", "/post", "/t/", "/d/", "showthread", "viewtopic"]
            ):
                thread_links.add(full_url)

        logger.info("💬 %d thread links trouvés", len(thread_links))

        for url in thread_links:
            yield scrapy.Request(
                url=url,
                callback=self.parse_page,
                errback=self.errback,
                priority=7,
                meta={
                    "source_type": "forum_thread",
                    "discovered_from": response.url,
                    "depth": 1,
                },
                dont_filter=False,
            )

        # Parser le contenu de la page courante aussi
        yield from self._process_page_content(response)

    # =========================================================================
    # PHASE 3 : PARSING DE CONTENU (callback principal)
    # =========================================================================

    def parse_page(self, response):
        """
        Parse une page découverte — extraction du contenu, IOCs, scoring.
        C'est le callback principal pour toutes les pages crawlées.
        """
        yield from self._process_page_content(response)

        # Crawl en profondeur si autorisé
        depth = response.meta.get("depth", 0)
        depth_limit = self.custom_settings.get("DEPTH_LIMIT", 3)

        if depth < depth_limit:
            links = self._extract_onion_links(response)
            for link in links[:10]:
                yield scrapy.Request(
                    url=link,
                    callback=self.parse_page,
                    errback=self.errback,
                    priority=3,
                    meta={
                        "source_type": response.meta.get("source_type", "crawled"),
                        "discovered_from": response.url,
                        "depth": depth + 1,
                    },
                    dont_filter=False,
                )

    # =========================================================================
    # EXTRACTION DE CONTENU (utilisé par tous les callbacks)
    # =========================================================================

    def _process_page_content(self, response):
        """
        Extraction complète du contenu d'une page :
        texte, IOCs, keywords, scoring, construction de l'item.
        """
        self.pages_scraped += 1
        start = time.time()
        url = response.url
        depth = response.meta.get("depth", 0)
        source_type = response.meta.get("source_type", "unknown")

        logger.info(
            "📄 [%s] [depth=%d] [#%d]: %s",
            source_type, depth, self.pages_scraped, url[:80],
        )

        # --- Extraction du contenu textuel ---
        title = response.css("title::text").get(default="")[:200]

        body = response.css("body")
        if body:
            text_parts = body.css("*:not(script):not(style):not(noscript)::text").getall()
            text = " ".join(t.strip() for t in text_parts if t.strip())
        else:
            text = response.text[:50000]

        # Ignorer les pages vides ou trop courtes
        if not text or len(text) < 50:
            logger.debug("Contenu trop court, ignoré: %s", url[:60])
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
        bf_keywords_found = [k for k in BF_CONTEXT_KEYWORDS if k in text_lower]
        leak_keywords_found = [k for k in LEAK_KEYWORDS if k in text_lower]
        all_keywords = bf_keywords_found + leak_keywords_found

        # --- Score heuristique ---
        leak_score = self._compute_leak_score(iocs, bf_keywords_found, leak_keywords_found)

        # --- Extraction des liens ---
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
        item["links_found"] = links[:50]
        item["source_type"] = source_type
        item["scraped_at"] = datetime.utcnow().isoformat() + "Z"
        item["spider_name"] = self.name
        item["depth"] = depth
        item["iocs"] = iocs
        item["ioc_count"] = ioc_count
        item["keywords_found"] = all_keywords
        item["keyword_count"] = len(all_keywords)
        item["leak_score"] = leak_score
        item["http_status"] = response.status
        item["response_time"] = round(elapsed, 2)

        yield item

    # =========================================================================
    # SCORING HEURISTIQUE — Enrichi pour le Burkina Faso
    # =========================================================================

    def _compute_leak_score(self, iocs: dict, bf_keywords: list, leak_keywords: list) -> int:
        """
        Score heuristique 0-100 avec pondération Burkina Faso.

        Seuils (alignés avec le rapport chapitre 4) :
          ≥ 70 → confirmed_leak (pré-qualification)
          40-69 → suspected_leak
          < 40  → low_confidence
        """
        score = 0

        # --- Points IOCs génériques ---
        if iocs.get("email"):
            score += min(len(iocs["email"]) * 2, 15)
        if iocs.get("credit_card"):
            score += min(len(iocs["credit_card"]) * 5, 20)
        if iocs.get("md5") or iocs.get("sha1") or iocs.get("sha256"):
            hash_count = (
                len(iocs.get("md5", [])) +
                len(iocs.get("sha1", [])) +
                len(iocs.get("sha256", []))
            )
            score += min(hash_count * 3, 15)
        if iocs.get("bitcoin"):
            score += 5

        # --- Points IOCs spécifiques Burkina Faso (poids FORT) ---
        if iocs.get("phone_bf"):
            score += min(len(iocs["phone_bf"]) * 5, 20)
        if iocs.get("cnib"):
            score += min(len(iocs["cnib"]) * 8, 20)  # CNIB = très sensible
        if iocs.get("email_bf"):
            score += min(len(iocs["email_bf"]) * 5, 15)
        if iocs.get("gov_bf"):
            score += min(len(iocs["gov_bf"]) * 5, 10)

        # --- Points mots-clés ---
        score += min(len(leak_keywords) * 3, 15)

        # --- Bonus contexte Burkina Faso ---
        if bf_keywords:
            score += min(len(bf_keywords) * 4, 15)

        # --- Bonus combinaisons (signaux forts) ---
        has_bf_ioc = bool(
            iocs.get("phone_bf") or iocs.get("cnib") or
            iocs.get("email_bf") or iocs.get("gov_bf")
        )
        has_leak_signal = bool(
            iocs.get("email") or iocs.get("credit_card") or
            iocs.get("md5") or iocs.get("sha1")
        )

        if has_bf_ioc and has_leak_signal:
            score += 15  # Combinaison BF + leak = très suspect
        if has_bf_ioc and len(leak_keywords) >= 2:
            score += 10
        if len(iocs) >= 4:
            score += 5  # Diversité d'IOCs

        return min(score, 100)

    # =========================================================================
    # MÉTHODES UTILITAIRES
    # =========================================================================

    def _extract_onion_links(self, response) -> list:
        """Extrait les liens .onion de la page."""
        links = set()
        for href in response.css("a::attr(href)").getall():
            if ".onion" in href and href.startswith("http"):
                links.add(href.split("#")[0])  # Supprimer les fragments
            elif href.startswith("/"):
                full_url = response.urljoin(href)
                if ".onion" in full_url:
                    links.add(full_url.split("#")[0])
        return list(links)

    def _clean_onion_url(self, url: str) -> str:
        """Nettoie et valide une URL .onion."""
        if not url:
            return None
        url = url.strip().split("#")[0].split("?utm")[0]  # Supprimer fragments et tracking
        if not url.startswith("http"):
            url = "http://" + url
        if ".onion" not in url:
            return None
        return url

    def _is_login_page(self, response) -> bool:
        """Détecte si la page est un formulaire de login."""
        indicators = [
            response.css("input[type='password']"),
            response.css("form[action*='login']"),
            response.css("form[action*='signin']"),
            response.css("input[name='captcha']"),
        ]
        text_lower = response.text[:2000].lower()
        text_indicators = [
            "please login" in text_lower,
            "sign in" in text_lower and "password" in text_lower,
            "captcha" in text_lower,
            "create account" in text_lower and "password" in text_lower,
        ]
        return any(indicators) or any(text_indicators)

    def _load_seed_urls(self) -> dict:
        """Charge le fichier seed_urls.json."""
        seed_file = os.getenv("SEED_URLS_FILE", "/app/config/seed_urls.json")
        try:
            with open(seed_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            total = sum(
                len(cat.get("urls", []))
                for cat in config.get("start_urls", {}).values()
            )
            logger.info("✔ Seed URLs loaded from %s — %d URLs total", seed_file, total)
            return config
        except FileNotFoundError:
            logger.error("❌ Seed URLs file not found: %s", seed_file)
            return {}
        except json.JSONDecodeError as e:
            logger.error("❌ Invalid JSON in seed URLs: %s", e)
            return {}

    def _priority_to_int(self, priority_str: str) -> int:
        """Convertit une priorité string en int Scrapy (plus haut = traité en premier)."""
        mapping = {"CRITICAL": 10, "HIGH": 7, "MEDIUM": 5, "LOW": 2}
        return mapping.get(priority_str.upper(), 5)

    # =========================================================================
    # ERROR HANDLING
    # =========================================================================

    def errback(self, failure):
        """Gestion des erreurs."""
        url = failure.request.url
        logger.warning(
            "❌ Request failed: %s — %s",
            url[:60], str(failure.value)[:100],
        )

    def closed(self, reason):
        """Stats de fin."""
        elapsed = time.time() - self.start_time
        logger.info(
            "🏁 Spider '%s' closed: %d pages scraped, %d URLs discovered in %.1fs (reason: %s)",
            self.name, self.pages_scraped, len(self.urls_discovered), elapsed, reason,
        )