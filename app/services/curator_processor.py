import logging
import sys
from pathlib import Path

# python has issues with relative imports in scripts, so we add the project root to the path to allow absolute imports to work
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.agents.curator_agent import CuratorAgent
from app.agents.user_profile import DEFAULT_PROFILE
from app.database.repository import Repository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_curator(hours: int = 24, profile: str = DEFAULT_PROFILE) -> None:
    """Fetch recent digests and rank them against the given user profile."""
    agent = CuratorAgent()

    with Repository() as repo:
        digests = repo.get_recent_digests(hours=hours)

    if not digests:
        logger.info("No digests found in the last %d hours.", hours)
        return

    logger.info("Curator: ranking %d digest(s) for profile '%s'", len(digests), profile)

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
        result = agent.score(digest_dicts, profile=profile)
    except Exception as exc:
        logger.error("Curator agent failed: %s", exc)
        return

    if not result or not result.articles:
        logger.warning("Curator returned no results.")
        return

    ranked = sorted(result.articles, key=lambda a: a.rank)

    # Build a lookup so we can print the URL alongside each ranked item
    digest_by_compound_id = {
        f"{d.source_type}:{d.id}": d for d in digests
    }

    print(f"\n=== Ranked Briefing for '{profile}' (last {hours}h) ===\n")
    for item in ranked:
        digest = digest_by_compound_id.get(item.digest_id)
        url = digest.url if digest else "unknown"
        print(f"#{item.rank}  [{item.relevance_score:.1f}/10]  {item.digest_id}")
        print(f"     {item.reasoning}")
        print(f"     {url}")
        print()


if __name__ == "__main__":
    process_curator(hours=24)
