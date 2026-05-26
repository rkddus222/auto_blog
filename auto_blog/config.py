from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(slots=True)
class Settings:
    api_key: str
    model: str = "gemini-2.5-flash"
    output_dir: Path = Path("output")


def load_settings() -> Settings:
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set. Copy .env.example to .env and fill it in.")

    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"
    output_dir = Path(os.getenv("AUTO_BLOG_OUTPUT_DIR", "output")).expanduser()
    return Settings(api_key=api_key, model=model, output_dir=output_dir)
