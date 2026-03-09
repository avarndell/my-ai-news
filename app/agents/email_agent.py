import logging

from pydantic import BaseModel, Field

from app.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are writing the opening of a personalized daily AI news briefing email.

Produce two fields:
- greeting: a short salutation addressing the reader by name (e.g. "Hey Alex,")
- introduction: 2-3 sentences previewing the key themes in today's top articles.
  Mention the date. Be professional but conversational. Do not list or enumerate articles.
"""


class EmailIntro(BaseModel):
    greeting: str = Field(description="Short salutation addressing the reader by name")
    introduction: str = Field(description="2-3 sentence preview of today's top AI news themes")


class BriefingArticle(BaseModel):
    rank: int = Field(description="Rank position (1 = most relevant)")
    title: str = Field(description="Article title")
    summary: str = Field(description="2-3 sentence summary of the article")
    url: str = Field(description="URL to the original article")
    relevance_score: float = Field(description="Relevance score from 0.0 to 10.0")


class EmailBriefing(BaseModel):
    greeting: str
    introduction: str
    articles: list[BriefingArticle]
    total_ranked: int = Field(description="Total number of articles ranked by the curator")
    top_n: int = Field(description="Number of articles included in this briefing")

    def to_markdown(self) -> str:
        lines = [
            "# AI News Briefing",
            "",
            self.greeting,
            "",
            self.introduction,
            "",
            "---",
            "",
        ]
        for article in self.articles:
            lines += [
                f"## {article.title}",
                "",
                article.summary,
                "",
                f"[Read more]({article.url})",
                "",
                "---",
                "",
            ]
        return "\n".join(lines)


class EmailAgent(BaseAgent):
    def create_intro(self, name: str, date: str, top_articles: list[dict]) -> EmailIntro | None:
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
