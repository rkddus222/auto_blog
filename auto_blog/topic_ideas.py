from __future__ import annotations

import re
from dataclasses import dataclass

from auto_blog.prompts import build_topic_ideas_prompt


@dataclass(slots=True)
class TopicIdeasRequest:
    seed: str
    audience: str = "general readers"
    language: str = "Korean"
    count: int = 10
    keywords: list[str] | None = None


def parse_ideas_list(text: str) -> list[str]:
    ideas: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        cleaned = re.sub(r"^\d+[.)]\s*", "", stripped)
        cleaned = re.sub(r"^[-*]\s*", "", cleaned)
        if cleaned:
            ideas.append(cleaned)
    return ideas


def generate_topic_ideas(request: TopicIdeasRequest, generator: callable) -> list[str]:
    prompt = build_topic_ideas_prompt(
        seed=request.seed,
        audience=request.audience,
        language=request.language,
        count=request.count,
        keywords=request.keywords or [],
    )
    raw = generator(prompt)
    ideas = parse_ideas_list(raw)
    if not ideas:
        raise ValueError("No topic ideas were parsed from the model response.")
    return ideas[: request.count]
