import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import feedparser
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Article(BaseModel):
    """Shared article model for all RSS-based scrapers."""
    title: str
    url: str
    description: str
    published_at: datetime
    guid: str | None = None
    category: str | None = None


class BaseRSSScraper(ABC):
    """Base class for RSS-based scrapers. Subclasses define feeds and how to build articles."""

    source_name: str = ""
    rss_feeds: list[str] = []

    @abstractmethod
    def _make_article(self, entry, published_at: datetime) -> Article | None:
        """Build an Article from a feed entry. Return None to skip the entry."""
        ...

    def fetch_recent_articles(self, hours: int = 24) -> list[Article]:
        """Fetch articles from all feeds published in the last `hours` hours."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        seen: set[str] = set()
        recent: list[Article] = []

        for feed_url in self.rss_feeds:
            logger.info("Fetching RSS feed: %s", feed_url)
            feed = feedparser.parse(feed_url)

            if not feed.entries and feed.bozo:
                logger.warning("Failed to parse feed %s: %s", feed_url, feed.bozo_exception)
                continue

            for entry in feed.entries:
                guid = getattr(entry, "id", entry.link)

                if guid in seen:
                    continue

                if not getattr(entry, "published", None):
                    logger.debug("Skipping entry with no publish date: %s", guid)
                    continue

                published_at = parsedate_to_datetime(entry.published).astimezone(timezone.utc)
                if published_at < cutoff:
                    continue

                article = self._make_article(entry, published_at)
                if article is not None:
                    seen.add(guid)
                    recent.append(article)

        recent.sort(key=lambda a: a.published_at, reverse=True)
        logger.info("%s: %d article(s) in the last %d hours", self.source_name, len(recent), hours)
        return recent
