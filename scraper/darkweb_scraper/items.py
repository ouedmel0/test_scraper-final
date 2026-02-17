"""
Robust-Scraper — Items
Structure des données extraites par les spiders
"""

import scrapy


class DarkWebDocument(scrapy.Item):
    """
    Document brut extrait du Dark Web.
    Correspond au schéma publié dans le topic Kafka 'raw_documents'.
    """
    # Identifiants
    url = scrapy.Field()
    url_hash = scrapy.Field()

    # Contenu extrait
    title = scrapy.Field()
    content = scrapy.Field()
    raw_html_length = scrapy.Field()

    # Liens découverts sur la page
    links_found = scrapy.Field()

    # Métadonnées de collecte
    source_type = scrapy.Field()       # "onion", "i2p", etc.
    scraped_at = scrapy.Field()
    spider_name = scrapy.Field()
    depth = scrapy.Field()

    # Indicateurs de premier niveau (IOC)
    iocs = scrapy.Field()
    ioc_count = scrapy.Field()

    # Mots-clés détectés
    keywords_found = scrapy.Field()
    keyword_count = scrapy.Field()

    # Score heuristique initial
    leak_score = scrapy.Field()

    # Statut HTTP
    http_status = scrapy.Field()
    response_time = scrapy.Field()