"""
Think of this like a filing cabinet with labeled folders.
Previous projects just stored text and embeddings.
This one also stores metadata — tags, URL, title, date —
so you can later filter by folder (tag) instead of searching everything.

"Show me everything tagged investing" becomes a real query.
"""

import os
from datetime import datetime
from sentence_transformers import SentenceTransformer
import chromadb

from src.config import (
    EMBEDDING_MODEL, VECTORSTORE_PATH,
    COLLECTION_NAME, CHUNK_SIZE, CHUNK_OVERLAP, TOP_K
)


def _chunk_text(text: str) -> list[str]:
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start:start + CHUNK_SIZE])
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


class VectorStore:
    def __init__(self):
        self.embedder   = SentenceTransformer(EMBEDDING_MODEL)
        self.client     = chromadb.PersistentClient(path=VECTORSTORE_PATH)
        self.collection = self.client.get_or_create_collection(COLLECTION_NAME)

    def ingest(self, url: str, title: str, text: str, tags: list[str]) -> int:
        """
        Chunk a document and store each chunk with metadata.

        Metadata stored per chunk:
          - url:   source URL
          - title: document title
          - tags:  comma-separated topic tags
          - date:  when it was ingested

        Returns number of chunks stored.
        """
        chunks = _chunk_text(text)
        if not chunks:
            return 0

        # Build parallel lists — ChromaDB requires them in sync
        ids        = []
        embeddings = []
        metadatas  = []

        # Embed all chunks at once — more efficient than one by one
        vectors = self.embedder.encode(chunks).tolist()

        date_str = datetime.now().strftime("%Y-%m-%d")
        url_slug = url[:40].replace("/", "_").replace(":", "")

        for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
            ids.append(f"{url_slug}_{i}")
            embeddings.append(vector)
            metadatas.append({
                "url":   url,
                "title": title,
                "tags":  ",".join(tags),   # ChromaDB stores metadata as strings
                "date":  date_str
            })

        self.collection.add(
            documents  = chunks,
            embeddings = embeddings,
            ids        = ids,
            metadatas  = metadatas
        )

        return len(chunks)

    def query(self, query_text: str, top_k: int = TOP_K, tag_filter: str = None) -> list[dict]:
        """
        Search for relevant chunks, optionally filtered by tag.

        tag_filter: if provided, only return chunks where tags contain this string
        """
        query_embedding = self.embedder.encode(query_text).tolist()

        # ChromaDB where clause for tag filtering
        # Tags are stored as "investing,index-funds,personal-finance"
        # $contains checks if the string appears anywhere in the field
        where = {"tags": {"$contains": tag_filter}} if tag_filter else None

        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results":        top_k,
            "include":          ["documents", "metadatas", "distances"]
        }
        if where:
            kwargs["where"] = where

        result = self.collection.query(**kwargs)

        # Zip results into clean dicts
        chunks = []
        for text, meta, dist in zip(
            result["documents"][0],
            result["metadatas"][0],
            result["distances"][0]
        ):
            chunks.append({
                "text":  text,
                "title": meta.get("title", ""),
                "url":   meta.get("url", ""),
                "tags":  meta.get("tags", "").split(","),
                "date":  meta.get("date", ""),
                "score": round(1 - dist, 3)   # convert distance to similarity
            })

        return chunks

    def list_documents(self) -> list[dict]:
        """Return one entry per unique URL — useful for showing what's in the KB."""
        if self.collection.count() == 0:
            return []

        result = self.collection.get(include=["metadatas"])
        seen, docs = set(), []

        for meta in result["metadatas"]:
            url = meta.get("url", "")
            if url not in seen:
                seen.add(url)
                docs.append({
                    "url":   url,
                    "title": meta.get("title", ""),
                    "tags":  meta.get("tags", "").split(","),
                    "date":  meta.get("date", "")
                })

        return sorted(docs, key=lambda d: d["date"], reverse=True)
