import logging
from typing import Sequence
import sys
from pathlib import Path

# python has issues with relative imports in scripts, so we add the project root to the path to allow absolute imports to work
sys.path.insert(0, str(Path(__file__).parent.parent.parent)) 

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.database.models import AnthropicArticle, OpenAIArticle, YoutubeVideo
from app.scrapers.anthropic import AnthropicArticle as AnthropicDTO
from app.scrapers.openai import OpenAIArticle as OpenAIDTO
from app.scrapers.youtube import ChannelVideo

logger = logging.getLogger(__name__)

class Repository:
    def __init__(self, session: Session):
        self.session = session

    def upsert_anthropic_articles(self, articles: Sequence[AnthropicDTO]) -> int:
        """Insert new Anthropic articles, skip duplicates (by guid). Returns insert count."""
        if not articles:
            return 0

        rows = [
            {
                "guid": a.guid,
                "title": a.title,
                "description": a.description,
                "url": a.url,
                "category": a.category,
                "published_at": a.published_at,
            }
            for a in articles
        ]

        stmt = insert(AnthropicArticle).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["guid"],
            set_={"title": stmt.excluded.title,
                  "description": stmt.excluded.description,
                  "category": stmt.excluded.category},
        )
        result = self.session.execute(stmt)
        self.session.commit()
        count = result.rowcount
        logger.info("Anthropic: upserted %d / %d article(s)", count, len(rows))
        return count

    def upsert_openai_articles(self, articles: Sequence[OpenAIDTO]) -> int:
        """Insert new OpenAI articles, skip duplicates (by guid). Returns insert count."""
        if not articles:
            return 0

        rows = [
            {
                "guid": a.url,  # OpenAI model uses url as unique key
                "title": a.title,
                "description": a.description,
                "url": a.url,
                "category": a.category,
                "published_at": a.published_at,
            }
            for a in articles
        ]

        stmt = insert(OpenAIArticle).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["guid"],
            set_={"title": stmt.excluded.title,
                  "description": stmt.excluded.description,
                  "category": stmt.excluded.category},
        )
        result = self.session.execute(stmt)
        self.session.commit()
        count = result.rowcount
        logger.info("OpenAI: upserted %d / %d article(s)", count, len(rows))
        return count

    def upsert_youtube_videos(self, videos: Sequence[ChannelVideo], channel_name: str | None = None) -> int:
        """Insert new YouTube videos, skip duplicates (by video_id). Returns insert count."""
        if not videos:
            return 0

        rows = [
            {
                "video_id": v.video_id,
                "title": v.title,
                "url": v.url,
                "description": v.description,
                "channel_name": channel_name,
                "transcript": v.transcript,
                "published_at": v.published_at,
            }
            for v in videos
        ]

        stmt = insert(YoutubeVideo).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["video_id"],
            set_={"title": stmt.excluded.title,
                  "description": stmt.excluded.description,
                  "channel_name": stmt.excluded.channel_name},
        )
        result = self.session.execute(stmt)
        self.session.commit()
        count = result.rowcount
        logger.info("YouTube: upserted %d / %d video(s)", count, len(rows))
        return count
