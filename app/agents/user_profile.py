PROFILES: dict[str, dict] = {
    "alex": {
        "name": "Alex",
        "background": "Software engineer with 10+ years of experience building production applications. Currently focused on AI-powered products and developer tooling. Actively building with LLM APIs on a daily basis.",
        "expertise_level": "Advanced",
        "interests": [
            "Large Language Models (LLMs) and their applications",
            "Retrieval-Augmented Generation (RAG) systems",
            "AI agent architectures and frameworks",
            "Multimodal AI and vision-language models",
            "AI safety and alignment research",
            "Production AI systems and MLOps",
            "Real-world AI applications and case studies",
            "Technical tutorials and implementation guides",
            "Research papers with practical implications",
            "AI infrastructure and scaling challenges",
            "OpenAI and Anthropic product and API announcements",
            "New model releases, capability benchmarks, and evaluations",
        ],
        "preferences": {
            "prefer_practical": True,
            "prefer_technical_depth": True,
            "prefer_research_breakthroughs": True,
            "prefer_production_focus": True,
            "avoid_marketing_hype": True,
        },
    },
}

DEFAULT_PROFILE = "alex"


def get_profile(name: str = DEFAULT_PROFILE) -> str:
    profile = PROFILES.get(name)
    if not profile:
        raise ValueError(f"Unknown profile '{name}'. Available: {list(PROFILES.keys())}")

    interests_str = "\n".join(f"  - {i}" for i in profile["interests"])
    prefs_str = "\n".join(
        f"  - {k.replace('_', ' ').title()}: {'Yes' if v else 'No'}"
        for k, v in profile["preferences"].items()
    )

    return f"""Name: {profile["name"]}
Background: {profile["background"]}
Expertise Level: {profile["expertise_level"]}

Interests:
{interests_str}

Preferences:
{prefs_str}
"""
