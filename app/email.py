import logging
import os
import smtplib
from email.message import EmailMessage

import markdown as md
from dotenv import load_dotenv
import sys
from pathlib import Path

# python has issues with relative imports in scripts, so we add the project root to the path to allow absolute imports to work
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.agents.email_agent import EmailBriefing

load_dotenv()

logger = logging.getLogger(__name__)


def _markdown_to_html(briefing: EmailBriefing) -> str:
    body_html = md.markdown(briefing.to_markdown(), extensions=["extra"])
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 680px; margin: auto; padding: 24px; color: #333;">
        {body_html}
        <p style="color: #999; font-size: 12px; margin-top: 32px;">
            {briefing.top_n} of {briefing.total_ranked} articles ranked for you.
        </p>
    </body>
    </html>
    """


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
    msg.add_alternative(_markdown_to_html(briefing), subtype="html")

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
