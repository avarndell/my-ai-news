import logging
from datetime import datetime

import requests
from html_to_markdown import convert

from app.scrapers.base_rss_scraper import Article, BaseRSSScraper

logger = logging.getLogger(__name__)


class AnthropicScraper(BaseRSSScraper):
    """Scraper for Anthropic articles across news, engineering, and research feeds."""

    source_name = "Anthropic"
    rss_feeds = [
        "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml",
        "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_engineering.xml",
        "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_research.xml",
    ]

    def _make_article(self, entry, published_at: datetime) -> Article:
        return Article(
            title=entry.title,
            description=getattr(entry, "summary", ""),
            url=entry.link,
            guid=entry.id,
            published_at=published_at,
            category=entry.tags[0].term if getattr(entry, "tags", None) else None,
        )

    def url_to_markdown(self, url: str) -> str | None:
        """Fetch article content from a URL and return it as markdown."""
        logger.info("Converting article to markdown: %s", url)
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return convert(response.text)


if __name__ == "__main__":
    scraper = AnthropicScraper()
    articles = scraper.fetch_recent_articles(hours=400)
    markdown = scraper.url_to_markdown(articles[0].url)
    print(markdown)
