"""
Think of this like a librarian stamping subject labels on a new book.
When a book arrives, the librarian skims it and decides:
"This goes under investing, personal finance, index funds."

Those labels let you later say "show me everything under investing"
without having to remember the exact words from every article.

This file does the same — reads the document and assigns topic tags.
"""

import json
import anthropic
from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL_FAST, MAX_TAGS


def generate_tags(title: str, text: str) -> list[str]:
    """
    Read a document and return a list of topic tags.

    Example:
      title: "Why Index Funds Beat Active Management"
      tags:  ["investing", "index funds", "personal finance", "passive investing"]
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Only send the first 2000 characters — enough to understand the topic
    # without wasting tokens on the full article
    preview = text[:2000]

    prompt = f"""You are a document tagging assistant for a personal knowledge base.

Document title: "{title}"

Document preview:
{preview}

Generate up to {MAX_TAGS} topic tags for this document.

Rules:
- Tags should be short (1-3 words)
- Use lowercase with hyphens for multi-word tags (e.g. "index-funds" not "Index Funds")
- Be specific enough to be useful but broad enough to group related articles
- Think about what category a person would search for to find this article

Respond with ONLY a JSON array of strings. No explanation, no markdown.
Example: ["investing", "index-funds", "personal-finance"]"""

    response = client.messages.create(
        model      = CLAUDE_MODEL_FAST,
        max_tokens = 100,
        messages   = [{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        tags = json.loads(raw)
        if not isinstance(tags, list):
            raise ValueError("Expected a list")
        return [str(t).lower() for t in tags[:MAX_TAGS]]
    except (json.JSONDecodeError, ValueError):
        print(f"[Tagger] JSON parse failed. Raw: {raw}")
        return []
