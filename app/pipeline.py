"""
Daily pipeline runner — runs the full end-to-end pipeline:

  1. Scrape       — fetch new articles and videos from all sources
  2. Process      — extract markdown (Anthropic) and transcripts (YouTube)
  3. Digest       — generate AI summaries for all unprocessed items
  4. Email        — rank by user profile and send the daily briefing

Run directly:   python app/pipeline.py
Schedule daily: add to cron or Task Scheduler pointing at this file.
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import LOOKBACK_HOURS
from app.runner import run
from app.services.anthropic_processor import process_anthropic_markdown
from app.services.digest_processor import process_digest
from app.services.email_processor import process_email
from app.services.youtube_processor import process_youtube_transcripts

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_pipeline(hours: int = LOOKBACK_HOURS) -> None:
    logger.info("=== Pipeline started (lookback: %dh) ===", hours)

    # Step 1 — Scrape
    logger.info("--- Step 1: Scraping sources ---")
    try:
        result = run(hours=hours)
        logger.info(
            "Scraped — Anthropic: %d, OpenAI: %d, YouTube: %d",
            len(result.anthropic), len(result.openai), len(result.youtube),
        )
    except Exception as exc:
        logger.error("Scrape failed: %s", exc)
        return

    # Step 2 — Process markdown and transcripts
    logger.info("--- Step 2: Extracting markdown and transcripts ---")
    try:
        process_anthropic_markdown()
    except Exception as exc:
        logger.error("Anthropic markdown processing failed: %s", exc)

    try:
        process_youtube_transcripts()
    except Exception as exc:
        logger.error("YouTube transcript processing failed: %s", exc)

    # Step 3 — Generate digests
    logger.info("--- Step 3: Generating digests ---")
    try:
        process_digest()
    except Exception as exc:
        logger.error("Digest processing failed: %s", exc)
        return

    # Step 4 — Curate and send email
    logger.info("--- Step 4: Sending email briefing ---")
    try:
        process_email(hours=hours)
    except Exception as exc:
        logger.error("Email processing failed: %s", exc)
        return

    logger.info("=== Pipeline complete ===")


if __name__ == "__main__":
    run_pipeline()
