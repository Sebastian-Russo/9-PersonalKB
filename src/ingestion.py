"""
Think of this like a postal sorting office.
A new package (URL) arrives, gets opened (scraped), inspected (tagged),
labeled (metadata), and filed in the correct shelf (vector store).

This file coordinates scraper → tagger → vector store in sequence.
It's the ingest pipeline — separate from the query pipeline deliberately,
so each side stays clean and focused on one job.
"""

from src.scraper      import scrape_url
from src.tagger       import generate_tags
from src.vector_store import VectorStore


class IngestionPipeline:
    def __init__(self, store: VectorStore):
        self.store = store

    def ingest_url(self, url: str) -> dict:
        """
        Full ingestion pipeline for a single URL.

        Returns a result dict with what happened — success or failure,
        how many chunks were stored, and what tags were assigned.
        """
        print(f"[Ingestion] Scraping: {url}")

        # Step 1: scrape
        scraped = scrape_url(url)
        if not scraped["success"]:
            return {
                "success": False,
                "url":     url,
                "error":   "Could not extract text from this URL. It may be paywalled, JavaScript-rendered, or blocking scrapers."
            }

        title = scraped["title"]
        text  = scraped["text"]
        print(f"[Ingestion] Scraped: '{title}' ({len(text)} characters)")

        # Step 2: tag
        print(f"[Ingestion] Generating tags...")
        tags = generate_tags(title, text)
        print(f"[Ingestion] Tags: {tags}")

        # Step 3: store
        chunks_stored = self.store.ingest(url, title, text, tags)
        print(f"[Ingestion] Stored {chunks_stored} chunks.")

        return {
            "success":       True,
            "url":           url,
            "title":         title,
            "tags":          tags,
            "chunks_stored": chunks_stored,
            "characters":    len(text)
        }
