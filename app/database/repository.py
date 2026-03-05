import logging
from typing import Sequence
import sys
from pathlib import Path

# python has issues with relative imports in scripts, so we add the project root to the path to allow absolute imports to work
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session  # used in type hint only

from app.database.connection import get_session
from app.database.models import AnthropicArticle, Digest, OpenAIArticle, YoutubeVideo
from app.scrapers.anthropic import AnthropicArticle as AnthropicDTO
from app.scrapers.openai import OpenAIArticle as OpenAIDTO
from app.scrapers.youtube import ChannelVideo

logger = logging.getLogger(__name__)


class Repository:
    def __init__(self):
        self._cm = get_session()
        self.session: Session | None = None

    def __enter__(self) -> "Repository":
        self.session = self._cm.__enter__()
        return self

    def __exit__(self, *args) -> None:
        self._cm.__exit__(*args)

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
            set_={
                "title": stmt.excluded.title,
                "description": stmt.excluded.description,
                "category": stmt.excluded.category,
            },
        )
        result = self.session.execute(stmt)
        self.session.commit()
        count = result.rowcount
        logger.info("Anthropic: upserted %d / %d article(s)", count, len(rows))
        return count

    def get_anthropic_articles_without_markdown(self) -> list[AnthropicArticle]:
        """Return all Anthropic articles that have not yet had markdown extracted."""
        stmt = select(AnthropicArticle).where(AnthropicArticle.markdown.is_(None))
        return list(self.session.execute(stmt).scalars())

    def save_anthropic_markdown(self, article_id: int, markdown: str) -> None:
        """Persist the extracted markdown for a single Anthropic article."""
        article = self.session.get(AnthropicArticle, article_id)
        if article:
            article.markdown = markdown
            self.session.commit()

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
            set_={
                "title": stmt.excluded.title,
                "description": stmt.excluded.description,
                "category": stmt.excluded.category,
            },
        )
        result = self.session.execute(stmt)
        self.session.commit()
        count = result.rowcount
        logger.info("OpenAI: upserted %d / %d article(s)", count, len(rows))
        return count

    def get_youtube_videos_without_transcript(self) -> list[YoutubeVideo]:
        """Return all YouTube videos that have not yet had a transcript fetched."""
        stmt = select(YoutubeVideo).where(YoutubeVideo.transcript.is_(None))
        return list(self.session.execute(stmt).scalars())

    def save_youtube_transcript(self, video_id: int, transcript: str) -> None:
        """Persist the transcript (or unavailability marker) for a single YouTube video."""
        video = self.session.get(YoutubeVideo, video_id)
        if video:
            video.transcript = transcript
            self.session.commit()

    def upsert_youtube_videos(
        self, videos: Sequence[ChannelVideo], channel_name: str | None = None
    ) -> int:
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
            set_={
                "title": stmt.excluded.title,
                "description": stmt.excluded.description,
                "channel_name": stmt.excluded.channel_name,
            },
        )
        result = self.session.execute(stmt)
        self.session.commit()
        count = result.rowcount
        logger.info("YouTube: upserted %d / %d video(s)", count, len(rows))
        return count

    # ── Digest ────────────────────────────────────────────────────────────────

    def _digested_ids(self, source_type: str) -> set[int]:
        stmt = select(Digest.source_id).where(Digest.source_type == source_type)
        return set(self.session.execute(stmt).scalars())

    def get_undigested_anthropic_articles(self) -> list[AnthropicArticle]:
        done = self._digested_ids("anthropic")
        stmt = select(AnthropicArticle).where(
            AnthropicArticle.id.not_in(done) if done else True
        )
        return list(self.session.execute(stmt).scalars())

    def get_undigested_openai_articles(self) -> list[OpenAIArticle]:
        done = self._digested_ids("openai")
        stmt = select(OpenAIArticle).where(
            OpenAIArticle.id.not_in(done) if done else True
        )
        return list(self.session.execute(stmt).scalars())

    def get_undigested_youtube_videos(self) -> list[YoutubeVideo]:
        done = self._digested_ids("youtube")
        stmt = select(YoutubeVideo).where(
            YoutubeVideo.id.not_in(done) if done else True
        )
        return list(self.session.execute(stmt).scalars())

    def save_digest(
        self, source_type: str, source_id: int, url: str, title: str, summary: str
    ) -> None:
        stmt = (
            insert(Digest)
            .values(
                source_type=source_type,
                source_id=source_id,
                url=url,
                title=title,
                summary=summary,
            )
            .on_conflict_do_nothing(index_elements=["source_type", "source_id"])
        )
        self.session.execute(stmt)
        self.session.commit()
