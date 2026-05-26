from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from auto_blog.prompt_manager import PromptTemplates
from auto_blog.prompts import build_blog_image_prompt
from auto_blog.writer import slugify


@dataclass(slots=True)
class GeneratedImage:
    path: Path
    mime_type: str
    prompt: str
    caption: str = ""


def extension_for_mime_type(mime_type: str) -> str:
    mapping = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/webp": ".webp",
    }
    return mapping.get(mime_type, ".bin")


def build_image_output_path(output_dir: Path, title_or_topic: str, mime_type: str) -> Path:
    date_prefix = datetime.now().date().isoformat()
    slug = slugify(title_or_topic)
    return output_dir / "images" / f"{date_prefix}-{slug}{extension_for_mime_type(mime_type)}"


def save_generated_image(
    image_bytes: bytes,
    mime_type: str,
    output_dir: Path,
    title_or_topic: str,
    prompt: str,
    caption: str = "",
) -> GeneratedImage:
    path = build_image_output_path(output_dir, title_or_topic, mime_type)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(image_bytes)
    return GeneratedImage(path=path, mime_type=mime_type, prompt=prompt, caption=caption)


def build_default_blog_image_prompt(
    topic: str,
    title: str,
    audience: str,
    style_hint: str,
    templates: PromptTemplates | None = None,
) -> str:
    return build_blog_image_prompt(
        topic=topic,
        title=title,
        audience=audience,
        style_hint=style_hint,
        templates=templates,
    )
