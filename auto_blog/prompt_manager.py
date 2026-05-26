from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from string import Template


PROMPT_KEYS = (
    "blog",
    "research",
    "outline",
    "draft",
    "polish",
    "topic_ideas",
    "blog_image",
)


@dataclass(slots=True)
class PromptTemplates:
    blog: str
    research: str
    outline: str
    draft: str
    polish: str
    topic_ideas: str
    blog_image: str

    def as_dict(self) -> dict[str, str]:
        return {key: getattr(self, key) for key in PROMPT_KEYS}


BASE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = BASE_DIR / "prompt_presets"


def _read_prompt(name: str) -> str:
    return (PROMPT_DIR / f"{name}.md").read_text(encoding="utf-8").strip()


def load_prompt_templates(overrides: dict[str, str] | None = None) -> PromptTemplates:
    overrides = overrides or {}
    values = {
        key: (overrides.get(key) or _read_prompt(key)).strip()
        for key in PROMPT_KEYS
    }
    return PromptTemplates(**values)


def render_prompt(template_text: str, values: dict[str, object]) -> str:
    normalized = {key: str(value) for key, value in values.items()}
    return Template(template_text).safe_substitute(normalized).strip()


def extract_prompt_overrides(source: dict[str, str]) -> dict[str, str]:
    overrides: dict[str, str] = {}
    for key in PROMPT_KEYS:
        field_name = f"prompt_{key}"
        value = source.get(field_name, "")
        if value.strip():
            overrides[key] = value
    return overrides
