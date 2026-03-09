import logging

from pydantic import BaseModel

from app.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class DigestOutput(BaseModel):
    title: str
    summary: str


PROMPT = """You are an AI news analyst. Your job is to read an article or video transcript and produce a concise digest entry for a technical newsletter.

Rules:
- Write a clear, compelling title (5-10 words) that captures the essence of the content
- Write a summary of 2-3 sentences that highlights the main poiints and why they matter
- Focus on what is new, important, or technically significant
- Use clear, accessible language while maintaining technical accuracy
- Avoid marketing fluff - focus on substance"""


class DigestAgent(BaseAgent):
    def create_digest(self, content: str, source_title: str) -> DigestOutput | None:
        """
        Call the OpenAI Responses API to generate a digest title and summary.
        Returns None if the API call fails.
        """
        try:
            response = self.client.responses.parse(
                model=self.model,
                instructions=PROMPT,
                temperature=0.7,
                input=[
                    {"role": "user", "content": f"Title: {source_title}\n\n{content}"},
                ],
                text_format=DigestOutput,
            )
            return response.output_parsed
        except Exception as exc:
            logger.error("Digest agent failed for '%s': %s", source_title, exc)
            return None
