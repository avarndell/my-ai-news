import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.agents.curator_agent import CuratorAgent
from app.agents.email_agent import BriefingArticle, EmailAgent, EmailBriefing
from app.agents.user_profile import DEFAULT_PROFILE, PROFILES
from app.database.repository import Repository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOP_N = 10


def process_email(hours: int = 24, profile: str = DEFAULT_PROFILE) -> EmailBriefing | None:
    """Run curator → take top 10 → generate email briefing as a structured Pydantic model."""
    curator = CuratorAgent()
    email_agent = EmailAgent()

    profile_data = PROFILES.get(profile, {})
    name = profile_data.get("name", profile)
    today = datetime.now().strftime("%B %d, %Y")

    with Repository() as repo:
        digests = repo.get_recent_digests(hours=hours)

    if not digests:
        logger.info("No digests found in the last %d hours.", hours)
        return None

    logger.info("Email: found %d digest(s), running curator for profile '%s'", len(digests), profile)

    digest_dicts = [
        {
            "digest_id": d.id,
            "source_type": d.source_type,
            "title": d.title,
            "summary": d.summary,
            "url": d.url,
        }
        for d in digests
    ]

    try:
        ranked = curator.score(digest_dicts, profile=profile)
    except Exception as exc:
        logger.error("Curator failed: %s", exc)
        return None

    if not ranked or not ranked.articles:
        logger.warning("Curator returned no results.")
        return None

    top_articles = sorted(ranked.articles, key=lambda a: a.rank)[:TOP_N]
    digest_lookup = {f"{d.source_type}:{d.id}": d for d in digests}

    briefing_articles = []
    top_for_intro = []
    for item in top_articles:
        digest = digest_lookup.get(item.digest_id)
        briefing_articles.append(BriefingArticle(
            rank=item.rank,
            title=digest.title if digest else item.digest_id,
            summary=digest.summary if digest else "",
            url=digest.url if digest else "",
            relevance_score=item.relevance_score,
        ))
        top_for_intro.append({
            "rank": item.rank,
            "title": digest.title if digest else item.digest_id,
            "relevance_score": item.relevance_score,
        })

    logger.info("Generating email intro for %s on %s", name, today)
    intro = email_agent.create_intro(name=name, date=today, top_articles=top_for_intro)

    if not intro:
        logger.error("Failed to generate email intro.")
        return None

    briefing = EmailBriefing(
        greeting=intro.greeting,
        introduction=intro.introduction,
        articles=briefing_articles,
        total_ranked=len(ranked.articles),
        top_n=len(briefing_articles),
    )

    print(briefing.to_markdown())
    return briefing


if __name__ == "__main__":
    process_email()
