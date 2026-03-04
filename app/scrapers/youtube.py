import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List

import feedparser
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import CouldNotRetrieveTranscript

logger = logging.getLogger(__name__)

_RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


class ChannelVideo(BaseModel):
    title: str
    url: str
    video_id: str
    published_at: datetime
    description: str
    transcript: Optional[str] = None


class Transcript(BaseModel):
    text: str


class YouTubeScraper:
    """Scraper for YouTube channels and video transcripts (no API key required)."""

    def fetch_recent_videos(
        self, channel_id: str, hours: int = 24
    ) -> list[ChannelVideo]:
        """
        Fetch videos published in the last `hours` hours for the given channel ID
        using the YouTube RSS feed.
        """
        rss_url = _RSS_URL.format(channel_id=channel_id)
        logger.info("Fetching RSS feed: %s", rss_url)

        feed = feedparser.parse(rss_url)

        if not feed.entries and feed.bozo:
            raise ValueError(
                f"Failed to parse RSS feed for {channel_id}: {feed.bozo_exception}"
            )

        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent: list[ChannelVideo] = []

        for entry in feed.entries:
            published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            if published_at < cutoff:
                continue

            recent.append(
                ChannelVideo(
                    title=entry.title,
                    url=entry.link,
                    video_id=entry.yt_videoid,
                    published_at=published_at,
                    description=getattr(entry, "summary", ""),
                )
            )

        logger.info(
            "Channel %s: %d video(s) in the last %d hours",
            channel_id,
            len(recent),
            hours,
        )
        return recent

    def get_transcript(
        self, video_id: str, languages: tuple[str, ...] = ("en",)
    ) -> Transcript | None:
        """
        Fetch the transcript for a video.
        Returns None if the transcript is unavailable or blocked.
        """
        try:
            fetched = YouTubeTranscriptApi().fetch(video_id, languages=languages)
            text = " ".join(snippet.text for snippet in fetched)
            return Transcript(text=text)
        except CouldNotRetrieveTranscript as exc:
            logger.warning("No transcript for %s: %s", video_id, exc)
            return None
        except Exception as exc:
            logger.error(
                "Unexpected error fetching transcript for %s: %s", video_id, exc
            )
            return None

    def fetch_transcript(self, video_id: str) -> Transcript:
        """
        Fetch the transcript for a video.
        Raises ValueError if the transcript is unavailable.
        """
        transcript = self.get_transcript(video_id)
        if transcript is None:
            raise ValueError(f"No transcript available for video: {video_id}")
        return transcript


if __name__ == "__main__":
    scraper = YouTubeScraper()
    transcript: Transcript = scraper.get_transcript("jqd6_bbjhS8")
    print(transcript.text)
    channel_videos: List[ChannelVideo] = scraper.fetch_recent_videos(
        channel_id="UCn8ujwUInbJkBhffxqAPBVQ", hours=1000
    )
