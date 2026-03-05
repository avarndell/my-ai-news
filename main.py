
import sys
from pathlib import Path

# python has issues with relative imports in scripts, so we add the project root to the path to allow absolute imports to work
sys.path.insert(0, str(Path(__file__).parent.parent.parent)) 

from app.processor import process_anthropic_markdown
from app.runner import run

def main(hours: int = 24):
    """Entry point for the application."""
    result = run(hours=hours)
    
    print(f"Fetched {len(result.anthropic)} Anthropic articles")
    print(f"Fetched {len(result.openai)} OpenAI articles")
    print(f"Fetched {len(result.youtube)} YouTube videos")
    
    return result

if __name__ == "__main__":
    import sys
    result = process_anthropic_markdown()
    print(f"Total articles {result['total']} )")
    print(f"Processed: {result['processed']} )")
    print(f"Failed: {result['railed']} )")

    