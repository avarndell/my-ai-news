from app.scrapers.youtube import get_transcript


def fetch_transcript(video_id: str) -> str:
    """
    Return the transcript for a YouTube video ID as plain text.
    Raises ValueError if the transcript is unavailable.
    """
    transcript = get_transcript(video_id)
    if transcript is None:
        raise ValueError(f"No transcript available for video: {video_id}")
    return transcript


if __name__ == "__main__":
    print(fetch_transcript("PkQIREapb9o"))
