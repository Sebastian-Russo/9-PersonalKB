"""
Think of this like a highlighter and a pair of scissors.
A web page is a messy newspaper — ads, menus, cookie banners,
related articles, footers. Trafilatura reads the whole page,
identifies the actual article, and hands you just that text.

You give it a URL. It gives you clean readable content.

Trafilatura does the heavy lifting —
we just call it and check if it worked.
The failure cases matter here because not every URL is scrapeable.
Some sites block bots, some are paywalled,
some are just JavaScript-rendered with no readable HTML.

"""

import trafilatura # does the heavy lifting


def scrape_url(url: str) -> dict:
    """
    Fetch a URL and extract clean article text.

    Returns a dict with:
      - url:     the original URL
      - title:   page title if found
      - text:    clean extracted text
      - success: whether extraction worked
    """
    # Step 1: download the raw HTML
    downloaded = trafilatura.fetch_url(url)

    if not downloaded:
        return {
            "url":     url,
            "title":   None,
            "text":    None,
            "success": False
        }

    # Step 2: extract clean text
    # include_comments=False strips user comments on articles
    # include_tables=True keeps structured data like comparison tables
    text = trafilatura.extract(
        downloaded,
        include_comments = False,
        include_tables   = True
    )

    # Step 3: extract metadata separately for the title
    metadata = trafilatura.extract_metadata(downloaded)
    title    = metadata.title if metadata else None

    if not text:
        return {
            "url":     url,
            "title":   title,
            "text":    None,
            "success": False
        }

    return {
        "url":     url,
        "title":   title or url,   # fall back to URL if no title found
        "text":    text,
        "success": True
    }
