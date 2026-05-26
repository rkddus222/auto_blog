from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class BlogRequest:
    topic: str
    audience: str = "general readers"
    tone: str = "professional and practical"
    language: str = "Korean"
    cta: str = ""
    keywords: list[str] = field(default_factory=list)


def build_blog_prompt(request: BlogRequest) -> str:
    keywords = ", ".join(request.keywords) if request.keywords else "none provided"
    cta = request.cta if request.cta else "No explicit CTA."

    return f"""
You are an expert blog editor.
Write a polished blog post draft in {request.language}.

Requirements:
- Topic: {request.topic}
- Target audience: {request.audience}
- Tone: {request.tone}
- SEO keywords to naturally include: {keywords}
- CTA: {cta}
- Output only markdown.
- Start with a single H1 title.
- After the title, include a short intro paragraph.
- Use clear H2/H3 sections.
- Include practical examples or steps where useful.
- End with a short conclusion section.
- Do not wrap the result in code fences.
""".strip()


def build_topic_ideas_prompt(
    seed: str,
    audience: str,
    language: str,
    count: int,
    keywords: list[str],
) -> str:
    keyword_text = ", ".join(keywords) if keywords else "none provided"
    return f"""
You are a content strategist for a blog.
Generate {count} strong blog topic ideas in {language}.

Requirements:
- Seed theme: {seed}
- Target audience: {audience}
- Keywords to reflect where relevant: {keyword_text}
- Output only a numbered list.
- Each item must include:
  1. a clear title
  2. one short explanation after a colon
- Avoid generic or repetitive ideas.
- Prefer practical, searchable topics with business value.
""".strip()
