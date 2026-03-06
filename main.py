import sys
from pathlib import Path

# python has issues with relative imports in scripts, so we add the project root to the path to allow absolute imports to work
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.daily_runner import run_daily_pipeline


def main(hours: int = 24, top_n: int = 10):
    return run_daily_pipeline(hours=hours, top_n=top_n)


if __name__ == "__main__":
    import sys

    hours = 24
    top_n = 10

    if len(sys.argv) > 1:
        try:
            hours = int(sys.argv[1])
        except ValueError:
            print("Invalid hours argument, using default of 24.")
            hours = 24

    if len(sys.argv) > 2:
        try:
            top_n = int(sys.argv[2])
        except ValueError:
            print("Invalid top_n argument, using default of 10.")
            top_n = 10

    result = main(hours=hours, top_n=top_n)
    sys.exit(0 if result["success"] else 1)
