#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robust-Scraper Scheduler (KAFKA ONLY - NO REDIS)
Publishes URLs to Kafka for scrapers to consume
"""

import os
import json
import time
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import List

from kafka import KafkaProducer

# ============================================================================
# CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
KAFKA_TOPIC = "urls-to-scrape"
ONION_URLS_FILE = os.getenv("ONION_URLS_FILE", "/app/onion_urls.txt")

# ============================================================================
# KAFKA PRODUCER
# ============================================================================

class URLScheduler:
    """Simple scheduler that publishes URLs to Kafka"""
    
    def __init__(self, kafka_servers: str, urls_file: str):
        self.kafka_servers = kafka_servers
        self.urls_file = urls_file
        
        # Create Kafka producer
        self.producer = KafkaProducer(
            bootstrap_servers=kafka_servers.split(','),
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            compression_type='gzip',
            retries=5
        )
        
        logger.info(f"✓ Connected to Kafka: {kafka_servers}")
        logger.info(f"✓ URLs file: {urls_file}")
    
    def load_urls(self) -> List[str]:
        """Load URLs from file"""
        urls = []
        
        if not Path(self.urls_file).exists():
            logger.error(f"URLs file not found: {self.urls_file}")
            return urls
        
        with open(self.urls_file, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    urls.append(line)
        
        logger.info(f"✓ Loaded {len(urls)} URLs from file")
        return urls
    
    def schedule_crawl(self):
        """Load URLs and publish them to Kafka"""
        logger.info("=" * 60)
        logger.info("Starting crawl job...")
        logger.info("=" * 60)
        
        # Load URLs
        urls = self.load_urls()
        
        if not urls:
            logger.warning("No URLs to schedule!")
            return
        
        # Publish each URL to Kafka
        added = 0
        for url in urls:
            url_hash = hashlib.sha256(url.encode()).hexdigest()
            
            message = {
                'url': url,
                'url_hash': url_hash,
                'scheduled_at': datetime.utcnow().isoformat() + 'Z',
                'priority': 5
            }
            
            try:
                self.producer.send(KAFKA_TOPIC, value=message)
                added += 1
                logger.info(f"✓ Scheduled: {url}")
            except Exception as e:
                logger.error(f"✗ Failed to schedule {url}: {e}")
        
        # Flush to ensure all messages are sent
        self.producer.flush()
        
        logger.info("=" * 60)
        logger.info(f"✓ Crawl job completed: {added}/{len(urls)} URLs scheduled")
        logger.info("=" * 60)
    
    def close(self):
        """Close Kafka producer"""
        self.producer.close()

# ============================================================================
# MAIN
# ============================================================================

def main():
    logger.info("=" * 60)
    logger.info("Robust-Scraper Scheduler (Kafka)")
    logger.info("=" * 60)
    
    # Create scheduler
    scheduler = URLScheduler(
        kafka_servers=KAFKA_BOOTSTRAP_SERVERS,
        urls_file=ONION_URLS_FILE
    )
    
    # Run initial crawl
    logger.info("Running initial crawl job...")
    scheduler.schedule_crawl()
    
    # Keep container alive
    logger.info("Scheduler started. Waiting for cron schedule...")
    
    while True:
        time.sleep(3600)  # Sleep 1 hour

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {e}")
        raise