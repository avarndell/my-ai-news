import logging
import os

from openai import OpenAI
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are writing the opening introduction for a personalized daily AI news briefing email.

Your introduction should:
- Address the reader by name
- Mention today's date
- Give a warm, 2-3 sentence preview of the key themes in today's top articles
- Be professional but conversational in tone
- Not list or enumerate the articles — just set the stage for what is coming

Keep it concise. No sign-off or subject line — just the opening paragraph.
"""


class EmailIntro(BaseModel):
    introduction: str = Field(description="Opening paragraph for the daily AI news briefing email")


class EmailAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAPI_API_KEY"))
        self.model = os.getenv("OPENAPI_MODEL")

    def create_intro(self, name: str, date: str, top_articles: list[dict]) -> EmailIntro | None:
        """
        Generate an intro paragraph for the email briefing.

        `top_articles` is a list of dicts with keys: rank, title, summary, relevance_score.
        Returns an EmailIntro or None on failure.
        """
        articles_text = "\n".join(
            f"{a['rank']}. {a['title']} (score: {a['relevance_score']:.1f})"
            for a in top_articles
        )
        user_content = (
            f"Reader name: {name}\n"
            f"Date: {date}\n\n"
            f"Top articles in today's briefing:\n{articles_text}"
        )

        try:
            response = self.client.responses.parse(
                model=self.model,
                input=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                text_format=EmailIntro,
            )
            return response.output_parsed
        except Exception as exc:
            logger.error("Email agent failed: %s", exc)
            return None
