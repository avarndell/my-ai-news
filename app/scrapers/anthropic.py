import logging
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import List, Optional
from zoneinfo import ZoneInfo

import feedparser
from docling.document_converter import DocumentConverter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

RSS_FEEDS = [
    "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml",
    "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_engineering.xml",
    "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_research.xml",
]

class OpenAIMarkdown(BaseModel):
    markdown: str
    
class AnthropicArticle(BaseModel):
    title: str
    description: str
    url: str
    guid: str
    published_at: datetime
    category: Optional[str] = None


class AnthropicScraper:
    """Scraper for Anthropic articles across news, engineering, and research feeds."""

    def __init__(self, tz: str = "America/New_York"):
        self.tz = ZoneInfo(tz)

    def fetch_recent_articles(self, hours: int = 24) -> list[AnthropicArticle]:
        """Fetch articles from all Anthropic feeds published in the last `hours` hours."""
        cutoff = datetime.now(self.tz) - timedelta(hours=hours)
        seen_guids: set[str] = set()
        recent: list[AnthropicArticle] = []

        for rss_url in RSS_FEEDS:
            logger.info("Fetching RSS feed: %s", rss_url)
            feed = feedparser.parse(rss_url)

            if not feed.entries and feed.bozo:
                logger.warning("Failed to parse feed %s: %s", rss_url, feed.bozo_exception)
                continue

            for entry in feed.entries:
                guid = entry.id
                if guid in seen_guids:
                    continue

                if not getattr(entry, "published", None):
                    logger.debug("Skipping entry with no publish date: %s", guid)
                    continue

                # Convert feed timestamp (midnight UTC) into the configured timezone so
                # date boundaries are evaluated in local time, not UTC.
                published_at = parsedate_to_datetime(entry.published).astimezone(self.tz)
                if published_at < cutoff:
                    continue

                seen_guids.add(guid)
                recent.append(
                    AnthropicArticle(
                        title=entry.title,
                        description=getattr(entry, "summary", ""),
                        url=entry.link,
                        guid=guid,
                        published_at=published_at,
                        category=entry.tags[0].term if getattr(entry, "tags", None) else None,
                    )
                )

        recent.sort(key=lambda a: a.published_at, reverse=True)
        logger.info("Anthropic: %d article(s) in the last %d hours", len(recent), hours)
        return recent

    def url_to_markdown(self, url: str) -> Optional[str]:
        """Fetch article content from a URL and return it as markdown."""
        logger.info("Converting article to markdown: %s", url)
        converter = DocumentConverter()
        result = converter.convert(url)
        return result.document.export_to_markdown()
    
if __name__ == "__main__":
    scraper = AnthropicScraper()
    articles: List[AnthropicArticle] = scraper.fetch_recent_articles(hours=200)
    markdown: str = scraper.url_to_markdown(articles[0].url)
    print(markdown)
