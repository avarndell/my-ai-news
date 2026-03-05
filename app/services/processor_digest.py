import logging

from typing import Optional
import sys
from pathlib import Path

# python has issues with relative imports in scripts, so we add the project root to the path to allow absolute imports to work
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.agents.digest_agent import DigestAgent
from app.database.repository import Repository
from app.services.processor_youtube import TRANSCRIPT_UNAVAILABLE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_digest(limit: Optional[int] = None) -> dict:
    """Generate digest summaries for all unprocessed articles and videos."""
    agent = DigestAgent()

    with Repository() as repo:
        anthropic_articles = repo.get_undigested_anthropic_articles()
        openai_articles = repo.get_undigested_openai_articles()
        youtube_videos = repo.get_undigested_youtube_videos()

        logger.info(
            "Digest: %d Anthropic, %d OpenAI, %d YouTube items to process",
            len(anthropic_articles), len(openai_articles), len(youtube_videos),
        )

        processed = failed = 0

        for article in anthropic_articles:
            try:
                content = article.markdown or article.description
                result = agent.create_digest(content, article.title)
                if result:
                    repo.save_digest("anthropic", article.id, article.url, result.title, result.summary)
                    logger.info("[Anthropic] Digested: %s", article.title)
                    processed += 1
            except Exception as exc:
                logger.warning("[Anthropic] Failed to digest '%s': %s", article.title, exc)
                failed += 1

        for article in openai_articles:
            try:
                content = article.description
                result = agent.create_digest(content, article.title)
                if result:
                    repo.save_digest("openai", article.id, article.url, result.title, result.summary)
                    logger.info("[OpenAI] Digested: %s", article.title)
                    processed += 1
            except Exception as exc:
                logger.warning("[OpenAI] Failed to digest '%s': %s", article.title, exc)
                failed += 1

        for video in youtube_videos:
            try:
                content = video.description if video.transcript == TRANSCRIPT_UNAVAILABLE else (video.transcript or video.description)
                result = agent.create_digest(content, video.title)
                if result:
                    repo.save_digest("youtube", video.id, video.url, result.title, result.summary)
                    logger.info("[YouTube] Digested: %s", video.title)
                    processed += 1
            except Exception as exc:
                logger.warning("[YouTube] Failed to digest '%s': %s", video.title, exc)
                failed += 1

        logger.info("Digest complete — processed: %d, failed: %d", processed, failed)


if __name__ == "__main__":
    result = process_digest()
    print(f"Processed: {result.get('processed', 0)}")
