import argparse

from app.runner import run
from app.services.processor_anthropic import process_anthropic_markdown
from app.services.processor_digest import process_digest
from app.services.processor_youtube import process_youtube_transcripts


def main():
    parser = argparse.ArgumentParser(description="AI News pipeline")
    parser.add_argument(
        "command",
        choices=["scrape", "process:anthropic", "process:youtube", "process:digest"],
        help=(
            "scrape            — fetch and store new articles/videos\n"
            "process:anthropic — extract markdown from Anthropic articles\n"
            "process:youtube   — fetch YouTube transcripts\n"
            "process:digest    — generate AI summaries for all unprocessed items"
        ),
    )
    parser.add_argument(
        "--hours", type=int, default=24, help="Lookback window for scrape (default: 24)"
    )
    args = parser.parse_args()

    if args.command == "scrape":
        result = run(hours=args.hours)
        print(f"Anthropic: {len(result.anthropic)} article(s)")
        print(f"YouTube:   {len(result.youtube)} video(s)")
    elif args.command == "process:anthropic":
        process_anthropic_markdown()
    elif args.command == "process:youtube":
        process_youtube_transcripts()
    elif args.command == "process:digest":
        process_digest()


if __name__ == "__main__":
    main()
# run on command line: python main.py scrape --hours 200
