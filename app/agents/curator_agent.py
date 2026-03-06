import logging
import os

from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List

from app.agents.user_profile import DEFAULT_PROFILE, get_profile

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert AI news curator specializing in personalized content ranking for AI professionals.

Your job is to read a list of AI news digests and score each one based on how relevant and valuable it is to the reader described below. Evaluate every item independently.

Ranking Criteria:
1. Relevance to user's stated interests and background
2. Technical depth and practical value
3. Novelty and significance of the content
4. Alignment with user's expertise level
5. Actionability and real-world applicability

Scoring Guidelines:
- 9.0-10.0: Highly relevant, directly aligns with user interests, significant value
- 7.0-8.9: Very relevant, strong alignment with interests, good value
- 5.0-6.9: Moderately relevant, some alignment, decent value
- 3.0-4.9: Somewhat relevant, limited alignment, lower value
- 0.0-2.9: Low relevance, minimal alignment, little value

Rank articles from most relevant (rank 1) to least relevant. Ensure each article has a unique rank.
"""


class RankedArticle(BaseModel):
    digest_id: str = Field(description="The ID of the digest (source_type:article_id)")
    relevance_score: float = Field(
        description="Relevance score from 0.0 to 10.0", ge=0.0, le=10.0
    )
    rank: int = Field(description="Rank position (1 = most relevant)", ge=1)
    reasoning: str = Field(
        description="Brief explanation of why this article is ranked here"
    )


class RankedDigestList(BaseModel):
    articles: List[RankedArticle] = Field(description="List of ranked articles")


class CuratorAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAPI_API_KEY"))
        self.model = os.getenv("OPENAPI_MODEL")

    def score(
        self, digests: list[dict], profile: str = DEFAULT_PROFILE
    ) -> RankedDigestList | None:
        """
        Score a list of digests against the given user profile.

        Each dict in `digests` must have: digest_id, title, summary, source_type.
        `profile` is a key from PROFILES (defaults to DEFAULT_PROFILE).
        Returns a RankedDigestList with a RankedArticle per digest, or None on failure.
        """
        if not digests:
            return RankedDigestList(articles=[])

        lines = []
        for d in digests:
            compound_id = f"{d['source_type']}:{d['digest_id']}"
            lines.append(
                f"[ID:{compound_id}] [{d['source_type'].upper()}] {d['title']}\n{d['summary']}"
            )
        digests_content = "\n\n---\n\n".join(lines)
        user_content = f"READER PROFILE:\n{get_profile(profile)}\n\nARTICLES TO RANK:\n{digests_content}"

        try:
            response = self.client.responses.parse(
                model=self.model,
                input=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                text_format=RankedDigestList,
            )
            return response.output_parsed
        except Exception as exc:
            logger.error("Curator agent failed: %s", exc)
            return None
