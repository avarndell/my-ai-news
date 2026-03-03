import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import feedparser
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import CouldNotRetrieveTranscript

logger = logging.getLogger(__name__)

_RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


@dataclass
class VideoEntry:
    video_id: str
    title: str
    url: str
    published_at: datetime
    channel_id: str


def fetch_recent_videos(channel_id: str, hours: int = 24) -> list[VideoEntry]:
    """
    Fetch videos published in the last `hours` hours for the given channel ID
    using the YouTube RSS feed (no API key required).
    """
    rss_url = _RSS_URL.format(channel_id=channel_id)
    logger.info("Fetching RSS feed: %s", rss_url)

    feed = feedparser.parse(rss_url)

    if not feed.entries and feed.bozo:
        raise ValueError(
            f"Failed to parse RSS feed for {channel_id}: {feed.bozo_exception}"
        )

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    recent: list[VideoEntry] = []

    for entry in feed.entries:
        published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        if published_at < cutoff:
            continue

        recent.append(
            VideoEntry(
                video_id=entry.yt_videoid,
                title=entry.title,
                url=entry.link,
                published_at=published_at,
                channel_id=channel_id,
            )
        )

    logger.info(
        "Channel %s: %d video(s) in the last %d hours", channel_id, len(recent), hours
    )
    return recent


def get_transcript(video_id: str, languages: tuple[str, ...] = ("en",)) -> str | None:
    """
    Fetch the transcript for a YouTube video and return it as plain text.
    Returns None if transcripts are unavailable or blocked.
    """
    try:
        fetched = YouTubeTranscriptApi().fetch(video_id, languages=languages)
        return " ".join(snippet.text for snippet in fetched)
    except CouldNotRetrieveTranscript as exc:
        logger.warning("No transcript for %s: %s", video_id, exc)
        return None
    except Exception as exc:
        logger.error("Unexpected error fetching transcript for %s: %s", video_id, exc)
        return None

if __name__ == "__main__":
    videos = fetch_recent_videos(channel_id="UCn8ujwUInbJkBhffxqAPBVQ", hours=1000)