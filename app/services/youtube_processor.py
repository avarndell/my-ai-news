import logging
import sys
from pathlib import Path

# python has issues with relative imports in scripts, so we add the project root to the path to allow absolute imports to work
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database.repository import Repository
from app.scrapers.youtube import YouTubeScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TRANSCRIPT_UNAVAILABLE = "UNAVAILABLE"


def process_youtube_transcripts() -> None:
    """Fetch and store transcripts for all YouTube videos that don't have one yet."""
    scraper = YouTubeScraper()

    with Repository() as repo:
        videos = repo.get_youtube_videos_without_transcript()
        logger.info("YouTube: %d video(s) need transcript fetching", len(videos))

        for video in videos:
            transcript = scraper.get_transcript(video.video_id)
            if transcript:
                repo.save_youtube_transcript(video.id, transcript.text)
                logger.info("Saved transcript for: %s", video.title)
            else:
                repo.save_youtube_transcript(video.id, TRANSCRIPT_UNAVAILABLE)
                logger.info("Marked transcript unavailable for: %s", video.title)


if __name__ == "__main__":
    process_youtube_transcripts()
