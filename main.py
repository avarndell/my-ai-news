from app.runner import run

def main(hours: int = 24):
    """Entry point for the application."""
    result = run(hours=hours)
    
    print(f"Fetched {len(result.anthropic)} Anthropic articles")
    print(f"Fetched {len(result.openai)} OpenAI articles")
    print(f"Fetched {len(result.youtube)} YouTube videos")
    
    return result

if __name__ == "__main__":
    main(hours=150)
    