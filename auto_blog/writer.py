from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from auto_blog.prompts import BlogRequest, build_blog_prompt


@dataclass(slots=True)
class GeneratedPost:
    title: str
    markdown: str
    slug: str
    path: Path


def slugify(value: str) -> str:
    slug = value.strip().lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", "-", slug)
    slug = slug.strip("-")
    return slug or "blog-post"


def extract_title(markdown: str, fallback: str) -> str:
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip() or fallback
    return fallback


def ensure_h1(markdown: str, title: str) -> str:
    if any(line.strip().startswith("# ") for line in markdown.splitlines()):
        return markdown.strip()
    return f"# {title}\n\n{markdown.strip()}"


def build_front_matter(title: str, topic: str, request: BlogRequest) -> str:
    tags = request.keywords or [topic]
    quoted_tags = ", ".join(f'"{tag}"' for tag in tags)
    return "\n".join(
        [
            "---",
            f'title: "{title}"',
            f'date: "{datetime.now().date().isoformat()}"',
            f'language: "{request.language}"',
            f'topic: "{topic}"',
            f"tags: [{quoted_tags}]",
            "---",
            "",
        ]
    )


def save_post(markdown: str, topic: str, request: BlogRequest, output_dir: Path) -> GeneratedPost:
    title = extract_title(markdown, topic)
    normalized = ensure_h1(markdown, title)
    slug = slugify(title)
    output_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{datetime.now().date().isoformat()}-{slug}.md"
    path = output_dir / file_name
    content = build_front_matter(title=title, topic=topic, request=request) + normalized + "\n"
    path.write_text(content, encoding="utf-8")
    return GeneratedPost(title=title, markdown=normalized, slug=slug, path=path)


def generate_post(markdown: str, topic: str, request: BlogRequest) -> GeneratedPost:
    title = extract_title(markdown, topic)
    normalized = ensure_h1(markdown, title)
    slug = slugify(title)
    return GeneratedPost(title=title, markdown=normalized, slug=slug, path=Path(""))


def generate_and_save(request: BlogRequest, output_dir: Path, generator: Callable[[str], str]) -> GeneratedPost:
    prompt = build_blog_prompt(request)
    markdown = generator(prompt)
    return save_post(markdown=markdown, topic=request.topic, request=request, output_dir=output_dir)


def generate_only(request: BlogRequest, generator: Callable[[str], str]) -> GeneratedPost:
    prompt = build_blog_prompt(request)
    markdown = generator(prompt)
    return generate_post(markdown=markdown, topic=request.topic, request=request)
