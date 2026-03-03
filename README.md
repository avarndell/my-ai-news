# my-ai-news — AI News Aggregator

A daily AI news aggregator that scrapes YouTube channels and blog pages, stores content in PostgreSQL, generates an LLM-powered digest, and emails it to your inbox every day.

---

## What It Does

1. **Scrapes** YouTube channels (via RSS) and AI blog pages (via HTTP + HTML parsing)
2. **Stores** everything in a PostgreSQL database (sources → articles)
3. **Generates** a daily digest using the OpenAI API, shaped by a custom agent system prompt
4. **Emails** the digest (short snippets with links to originals) via Resend

---

## Project Structure

```
my-ai-news/
├── app/
│   ├── config.py              # Pydantic settings (reads .env)
│   ├── database.py            # SQLAlchemy engine, Base, session management
│   ├── models/
│   │   ├── source.py          # Source model (youtube / blog)
│   │   ├── article.py         # Article model (url unique — dedup key)
│   │   └── digest.py          # Digest model
│   ├── scrapers/
│   │   ├── youtube.py         # YouTube RSS feed scraper (feedparser)
│   │   └── blog.py            # Blog HTML scraper (httpx + BeautifulSoup)
│   ├── digest/
│   │   └── generator.py       # OpenAI digest generation
│   └── email/
│       └── sender.py          # Resend email sender
├── agents/
│   └── digest_prompt.md       # Agent system prompt (your interests + output format)
├── docker/
│   └── docker-compose.yml     # PostgreSQL 16 container
├── main.py                    # Pipeline entry point
├── pyproject.toml
├── .env.example
└── .gitignore
```

---

## Tech Stack

| Layer            | Technology                        |
| ---------------- | --------------------------------- |
| Language         | Python 3.14                       |
| Database         | PostgreSQL 16 (Docker)            |
| ORM              | SQLAlchemy 2.0                    |
| YouTube scraping | feedparser (RSS)                  |
| LLM              | OpenAI API (gpt-5.2, configurable) |
| Email            | Resend API                        |
| Config           | pydantic-settings                 |

---

## Database Models

| Model     | Key Fields                                                            |
| --------- | --------------------------------------------------------------------- |
| `Source`  | id, name, type (youtube/blog), url, is_active, created_at             |
| `Article` | id, source_id, title, url (unique), content, published_at, scraped_at |
| `Digest`  | id, content, articles_count, date_from, date_to, sent_at, created_at  |

Tables are created automatically on first run via `Base.metadata.create_all()`.

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```env
# PostgreSQL (matches docker-compose)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ainews

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# Resend (email)
RESEND_API_KEY=re_...
RESEND_FROM_EMAIL=digest@yourdomain.com
DIGEST_EMAIL_TO=you@example.com

# Pipeline
LOOKBACK_HOURS=24
```

---

## Getting Started

### 1. Start the database

```bash
docker compose -f docker/docker-compose.yml up -d
```

### 2. Set up environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Install dependencies

```bash
pip install -e .
```

### 4. Run the pipeline

```bash
python main.py
```

On first run the pipeline will:
- Create all database tables
- Seed starter sources (blogs + YouTube channels)
- Scrape all sources for new content
- Generate a digest via OpenAI
- Send the digest to your email via Resend

---

## Starter Sources

Pre-configured on first run:

**Blogs**
- [OpenAI News](https://openai.com/news/)
- [Anthropic News](https://www.anthropic.com/news)
- [Google DeepMind Blog](https://deepmind.google/discover/blog/)

**YouTube Channels**
- [Andrej Karpathy](https://www.youtube.com/channel/UCXUPKJO5MZQMU11oA6uDd9g)
- [Yannic Kilcher](https://www.youtube.com/channel/UCZHmQk67mSJgfCCTn7xBfew)

To add more, edit `seed_sources_if_empty()` in `main.py` or insert directly into the `sources` table.

---

## Customising the Digest

Edit `agents/digest_prompt.md` to change:
- Which topics you care about
- The output format of each digest entry
- Tone and filtering rules

The prompt is read from disk at runtime — changes take effect on the next run without restarting.

---

## Pipeline Steps

Each step runs in its own database session so a failure in a later step does not roll back earlier work:

1. **init_db** — create tables if they don't exist
2. **seed_sources** — insert starter sources on first run only
3. **scrape_all** — fetch new articles from all active sources; duplicates skipped via `url UNIQUE` constraint
4. **generate_digest** — query articles from last `LOOKBACK_HOURS`, send to OpenAI with system prompt, persist `Digest` row
5. **send_email** — send via Resend, update `digest.sent_at` on success

---

## Notes

- **Blog scraping**: Some blogs (OpenAI, Anthropic) use Next.js and render content client-side. The scraper attempts `<article>` tag extraction first, then falls back to `<script id="__NEXT_DATA__">` JSON payload parsing.
- **YouTube**: Uses the public RSS feed — no API key required. Channel URLs can be full `/channel/UCxxxxx` URLs or bare channel IDs.
- **Email**: Resend free tier allows 3,000 emails/month (100/day). Your sending domain must be verified in Resend's dashboard.
- **Scheduling**: Deploy to [Render](https://render.com) and configure a Cron Job to run `python main.py` every 24 hours.
