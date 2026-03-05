import logging

from app.database.connection import get_session
from app.database.repository import Repository
from app.scrapers.anthropic import AnthropicScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_anthropic_markdown() -> None:
    """Fetch and store markdown for all Anthropic articles that don't have it yet."""
    scraper = AnthropicScraper()

    with get_session() as session:
        repo = Repository(session)
        articles = repo.get_anthropic_articles_without_markdown()

        logger.info("Anthropic: %d article(s) need markdown extraction", len(articles))

        for article in articles:  
            markdown = scraper.url_to_markdown(article.url)
            try:
                if markdown:
                    repo.save_anthropic_markdown(article.id, markdown)
                    logger.info("Saved markdown for: %s", article.title)
            except Exception as exc:
                logger.warning("Failed to extract markdown for '%s': %s", article.title, exc)


if __name__ == "__main__":
    process_anthropic_markdown()
