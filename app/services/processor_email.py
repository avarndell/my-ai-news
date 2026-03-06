import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.agents.curator_agent import CuratorAgent
from app.agents.email_agent import EmailAgent
from app.agents.user_profile import DEFAULT_PROFILE, PROFILES
from app.database.repository import Repository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOP_N = 10


def process_email(hours: int = 24, profile: str = DEFAULT_PROFILE) -> None:
    """Run curator → take top 10 → generate email intro and print the briefing."""
    curator = CuratorAgent()
    email_agent = EmailAgent()

    profile_data = PROFILES.get(profile, {})
    name = profile_data.get("name", profile)
    today = datetime.now().strftime("%B %d, %Y")

    with Repository() as repo:
        digests = repo.get_recent_digests(hours=hours)

    if not digests:
        logger.info("No digests found in the last %d hours.", hours)
        return

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
        return

    if not ranked or not ranked.articles:
        logger.warning("Curator returned no results.")
        return

    top_articles = sorted(ranked.articles, key=lambda a: a.rank)[:TOP_N]

    # Build lookup for title/summary/url from digest_id
    digest_lookup = {f"{d.source_type}:{d.id}": d for d in digests}

    top_with_content = []
    for item in top_articles:
        digest = digest_lookup.get(item.digest_id)
        top_with_content.append({
            "rank": item.rank,
            "title": digest.title if digest else item.digest_id,
            "summary": digest.summary if digest else "",
            "relevance_score": item.relevance_score,
            "reasoning": item.reasoning,
            "url": digest.url if digest else "",
        })

    logger.info("Generating email intro for %s on %s", name, today)

    intro = email_agent.create_intro(name=name, date=today, top_articles=top_with_content)

    if not intro:
        logger.error("Failed to generate email intro.")
        return

    # Print the full briefing
    print(f"\n{'='*60}")
    print(f"  AI News Briefing — {today}")
    print(f"{'='*60}\n")
    print(intro.introduction)
    print(f"\n{'—'*60}\n")

    for article in top_with_content:
        print(f"#{article['rank']}  [{article['relevance_score']:.1f}/10]  {article['title']}")
        print(f"     {article['summary']}")
        print(f"     {article['url']}")
        print()


if __name__ == "__main__":
    process_email()
