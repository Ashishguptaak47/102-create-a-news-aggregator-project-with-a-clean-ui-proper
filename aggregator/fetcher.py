import datetime
import html
import re
from typing import Any, Dict, List, Optional
import feedparser
import requests
from bs4 import BeautifulSoup
from aggregator.database import get_sources, upsert_article

SAMPLE_FALLBACK_ARTICLES = [
    {
        "title": "Advancements in Next-Gen Microprocessor Architecture",
        "link": "https://example.com/news/next-gen-processors",
        "summary": "Engineers reveal innovative sub-nanometer chip topologies designed to minimize thermal output and drastically accelerate neural network model processing.",
        "published_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "image_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=600&auto=format&fit=crop&q=80",
        "category": "Tech",
    },
    {
        "title": "James Webb Space Telescope Maps Distant Atmospheric Water Vapor",
        "link": "https://example.com/news/jwst-atmosphere",
        "summary": "Astronomers detect rich molecular signatures in the atmosphere of an exoplanet orbiting a nearby stable star system, unlocking fresh cosmic insights.",
        "published_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "image_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=600&auto=format&fit=crop&q=80",
        "category": "Science",
    },
    {
        "title": "Global Clean Energy Investment Reaches Historic Milestone",
        "link": "https://example.com/news/clean-energy-record",
        "summary": "Renewable energy financing surpassed fossil fuel investments across emerging and developed markets during the previous fiscal quarter.",
        "published_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "image_url": "https://images.unsplash.com/photo-1466611653911-95081537e5b7?w=600&auto=format&fit=crop&q=80",
        "category": "World",
    },
]


def clean_html_summary(html_content: str, max_length: int = 240) -> str:
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "html.parser")
    text = soup.get_text(separator=" ").strip()
    text = re.sub(r"\s+", " ", text)
    text = html.unescape(text)
    if len(text) > max_length:
        return text[:max_length].rsplit(" ", 1)[0] + "..."
    return text


def extract_first_image(entry: Dict[str, Any], raw_summary: str) -> Optional[str]:
    # 1. Media enclosures / media_content
    if "media_content" in entry and entry["media_content"]:
        for media in entry["media_content"]:
            if media.get("medium") == "image" or media.get("type", "").startswith("image/"):
                return media.get("url")
    if "enclosures" in entry and entry["enclosures"]:
        for enc in entry["enclosures"]:
            if enc.get("type", "").startswith("image/"):
                return enc.get("href") or enc.get("url")

    # 2. Extract from summary or content
    soup = BeautifulSoup(raw_summary or "", "html.parser")
    img = soup.find("img")
    if img and img.get("src"):
        return img["src"]
    return None


def parse_feed_entries(feed_url: str, timeout: int = 6) -> List[Dict[str, Any]]:
    try:
        resp = requests.get(
            feed_url,
            timeout=timeout,
            headers={"User-Agent": "PulseNewsAggregator/1.0 (+http://localhost:5000)"},
        )
        resp.raise_for_status()
        parsed = feedparser.parse(resp.content)
        return parsed.entries
    except Exception:
        return []


def sync_feeds() -> int:
    sources = get_sources()
    saved_count = 0

    for source in sources:
        entries = parse_feed_entries(source["url"])
        for entry in entries[:15]:
            link = entry.get("link")
            title = entry.get("title")
            if not link or not title:
                continue

            raw_desc = entry.get("summary", entry.get("description", ""))
            summary = clean_html_summary(raw_desc)
            image_url = extract_first_image(entry, raw_desc)

            # Date parsing
            published = entry.get("published", entry.get("updated"))
            if not published:
                published = datetime.datetime.utcnow().isoformat()

            payload = {
                "source_id": source["id"],
                "title": html.unescape(title.strip()),
                "link": link.strip(),
                "summary": summary,
                "published_at": str(published),
                "image_url": image_url,
                "category": source["category"],
            }
            if upsert_article(payload):
                saved_count += 1

    # If no articles were saved (e.g. offline environment), load seeds
    if saved_count == 0:
        for sample in SAMPLE_FALLBACK_ARTICLES:
            if upsert_article(sample):
                saved_count += 1

    return saved_count
