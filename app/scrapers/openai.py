import logging
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import List, Optional

import feedparser
from docling.document_converter import DocumentConverter
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class OpenAIMarkdown(BaseModel):
    markdown: str


class OpenAIArticle(BaseModel):
    title: str
    url: str
    description: str
    category: str
    published_at: datetime


class OpenAIScraper:
    def __init__(self):
        self.rss_url = "https://openai.com/news/rss.xml"

    """Scraper for OpenAI news articles via RSS feed."""

    def fetch_recent_articles(self, hours: int = 24) -> list[OpenAIArticle]:
        """Fetch articles published in the last `hours` hours."""
        logger.info("Fetching RSS feed: %s", self.rss_url)
        feed = feedparser.parse(self.rss_url)

        if not feed.entries and feed.bozo:
            raise ValueError(f"Failed to parse OpenAI RSS feed: {feed.bozo_exception}")

        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent: list[OpenAIArticle] = []

        for entry in feed.entries:
            published_at = parsedate_to_datetime(entry.published).astimezone(
                timezone.utc
            )
            if published_at < cutoff:
                continue

            recent.append(
                OpenAIArticle(
                    title=entry.title,
                    url=entry.link,
                    description=getattr(entry, "summary", ""),
                    category=entry.tags[0].term if getattr(entry, "tags", None) else "",
                    published_at=published_at,
                )
            )

        logger.info("OpenAI: %d article(s) in the last %d hours", len(recent), hours)
        return recent

    #
if __name__ == "__main__":
    scraper = OpenAIScraper()
    articles: List[OpenAIArticle] = scraper.fetch_recent_articles(hours=200)