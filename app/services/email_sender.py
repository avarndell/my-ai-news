import logging
import os
import smtplib
import sys
from email.message import EmailMessage
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv

from app.agents.email_agent import EmailBriefing

load_dotenv()

logger = logging.getLogger(__name__)


def _briefing_to_html(briefing: EmailBriefing) -> str:
    articles_html = ""
    for article in briefing.articles:
        articles_html += f"""
        <div>
            <h3 style="margin: 0 0 6px 0;">{article.title}</h3>
            <p style="margin: 0 0 8px 0;">{article.summary}</p>
            <p style="margin: 0;">
                <a href="{article.url}" style="color: #1a73e8; text-decoration: none;">Read more &rarr;</a>
                &nbsp; <em style="color: #999; font-size: 12px;">score {article.relevance_score:.1f}/10</em>
            </p>
            <hr style="border: none; border-top: 1px solid #e8e8e8; margin: 20px 0;">
        </div>
        """

    return f"""<!DOCTYPE html>
<html>
<body style="font-family: arial, serif; max-width: 620px; margin: auto; padding: 32px 24px; color: #222; line-height: 1.6;">
    <h1 style="font-size: 18px; font-weight: bold; letter-spacing: 0.5px; border-bottom: 2px solid #222; padding-bottom: 10px; margin-bottom: 20px;">
        AI News Briefing
    </h1>
    <p style="margin: 0 0 6px 0;"><strong>{briefing.greeting}</strong></p>
    <p style="margin: 0 0 28px 0; color: #444;">{briefing.introduction}</p>
    {articles_html}
    <p style="color: #aaa; font-size: 11px; margin-top: 8px;">
        Showing {briefing.top_n} of {briefing.total_ranked} ranked articles.
    </p>
</body>
</html>"""


def send_email(subject: str, body: str, to: str) -> None:
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("GMAIL_APP_PASSWORD")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(user=sender, password=password)
        smtp.send_message(msg)

    logger.info("Email sent to %s", to)


def send_briefing(briefing: EmailBriefing, to: str | None = None) -> None:
    sender = os.getenv("EMAIL_SENDER")
    recipient = to or sender

    msg = EmailMessage()
    msg["Subject"] = "Your Daily AI News Briefing"
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content(briefing.to_markdown())
    msg.add_alternative(_briefing_to_html(briefing), subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(user=sender, password=os.getenv("GMAIL_APP_PASSWORD"))
        smtp.send_message(msg)

    logger.info("Briefing sent to %s", recipient)


if __name__ == "__main__":
    send_email(
        subject="Test email from Python",
        body="This is a test email sent from a Python script using smtplib.",
        to=os.getenv("EMAIL_SENDER"),
    )
