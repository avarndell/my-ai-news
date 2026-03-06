import logging
from dataclasses import dataclass

from app.config import YOUTUBE_CHANNELS
from app.database.repository import Repository
from app.scrapers.anthropic import AnthropicArticle, AnthropicScraper
from app.scrapers.openai import OpenAIArticle, OpenAIScraper
from app.scrapers.youtube import ChannelVideo, YouTubeScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RunResult:
    anthropic: list[AnthropicArticle]
    openai: list[OpenAIArticle]
    youtube: list[ChannelVideo]


def run(hours: int = 24) -> RunResult:
    """Fetch recent content from all sources and persist to the database."""
    logger.info("Running scrapers for the last %d hours", hours)

    anthropic_articles = AnthropicScraper().fetch_recent_articles(hours=hours)
    openai_articles = OpenAIScraper().fetch_recent_articles(hours=hours)

    youtube_videos: list[ChannelVideo] = []
    yt = YouTubeScraper()
    with Repository() as repo:
        repo.upsert_anthropic_articles(anthropic_articles)
        repo.upsert_openai_articles(openai_articles)

        for channel in YOUTUBE_CHANNELS:
            if not channel["channel_id"]:
                logger.warning("Skipping YouTube channel '%s' — no channel_id configured", channel["name"])
                continue
            try:
                videos = yt.fetch_recent_videos(channel_id=channel["channel_id"], hours=hours)
                repo.upsert_youtube_videos(videos, channel_name=channel["name"])
                youtube_videos.extend(videos)
            except Exception as exc:
                logger.warning("Failed to fetch YouTube channel '%s': %s", channel["name"], exc)

    result = RunResult(
        anthropic=anthropic_articles,
        openai=openai_articles,
        youtube=youtube_videos,
    )

    logger.info(
        "Done — Anthropic: %d, OpenAI: %d, YouTube: %d",
        len(result.anthropic),
        len(result.openai),
        len(result.youtube),
    )
    return result


if __name__ == "__main__":
    result = run()

    print(f"\n=== Anthropic ({len(result.anthropic)}) ===")
    for a in result.anthropic:
        print(f"  [{a.published_at.date()}] {a.title}")

    print(f"\n=== OpenAI ({len(result.openai)}) ===")
    for a in result.openai:
        print(f"  [{a.published_at.date()}] {a.title}")

    print(f"\n=== YouTube ({len(result.youtube)}) ===")
    for v in result.youtube:
        print(f"  [{v.published_at.date()}] {v.title}")
