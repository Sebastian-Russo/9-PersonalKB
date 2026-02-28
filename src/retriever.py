"""
Think of this like a research assistant who has read everything
you've ever saved. You ask them a question, they pull the most
relevant passages from your notes, and a senior analyst
synthesizes them into a clear answer.

This file handles the query side — completely separate from ingestion.
"""

import anthropic
from src.config       import ANTHROPIC_API_KEY, CLAUDE_MODEL_SMART, TOP_K
from src.vector_store import VectorStore


class Retriever:
    def __init__(self, store: VectorStore):
        self.store  = store
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def query(self, question: str, tag_filter: str = None) -> dict:
        """
        Search the knowledge base and synthesize an answer.

        question:   what the user is asking
        tag_filter: optional tag to restrict search (e.g. "investing")
        """
        # Step 1: retrieve relevant chunks
        chunks = self.store.query(question, top_k=TOP_K, tag_filter=tag_filter)

        if not chunks:
            return {
                "answer":  "I couldn't find anything relevant in your knowledge base. Try adding some documents first.",
                "sources": [],
                "chunks":  0
            }

        # Step 2: build evidence block for Claude
        evidence = "\n\n".join(
            f"[Source: {c['title']} — {c['url']}]\n{c['text']}"
            for c in chunks
        )

        # Step 3: synthesize answer
        prompt = f"""You are a personal knowledge assistant. The user has saved articles
and documents to their knowledge base, and you answer questions using only that content.

QUESTION:
{question}

RETRIEVED CONTENT FROM KNOWLEDGE BASE:
{evidence}

Instructions:
- Answer using ONLY the retrieved content above
- If the content doesn't fully answer the question, say so honestly
- Mention which sources you're drawing from naturally in your answer
- Be concise and direct — this is a personal assistant, not an essay"""

        response = self.client.messages.create(
            model      = CLAUDE_MODEL_SMART,
            max_tokens = 800,
            messages   = [{"role": "user", "content": prompt}]
        )

        # Step 4: build source list — deduplicated by URL
        seen, sources = set(), []
        for c in chunks:
            if c["url"] not in seen:
                seen.add(c["url"])
                sources.append({
                    "title": c["title"],
                    "url":   c["url"],
                    "tags":  c["tags"],
                    "score": c["score"]
                })

        return {
            "answer":  response.content[0].text.strip(),
            "sources": sources,
            "chunks":  len(chunks)
        }
