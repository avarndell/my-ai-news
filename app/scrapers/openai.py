import logging
from datetime import datetime

from app.scrapers.base_rss_scraper import Article, BaseRSSScraper

logger = logging.getLogger(__name__)


class OpenAIScraper(BaseRSSScraper):
    """Scraper for OpenAI news articles via RSS feed."""

    source_name = "OpenAI"
    rss_feeds = ["https://openai.com/news/rss.xml"]

    def _make_article(self, entry, published_at: datetime) -> Article:
        return Article(
            title=entry.title,
            url=entry.link,
            description=getattr(entry, "summary", ""),
            category=entry.tags[0].term if getattr(entry, "tags", None) else None,
            published_at=published_at,
        )


if __name__ == "__main__":
    scraper = OpenAIScraper()
    articles = scraper.fetch_recent_articles(hours=200)
    for a in articles:
        print(f"  [{a.published_at.date()}] {a.title}")
