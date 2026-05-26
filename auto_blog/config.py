from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(slots=True)
class Settings:
    auth_mode: str
    model: str = "gemini-2.5-flash"
    output_dir: Path = Path("output")
    api_key: str = ""
    project: str = ""
    location: str = "global"
    service_account_file: Path | None = None


def load_settings() -> Settings:
    load_dotenv()

    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"
    output_dir = Path(os.getenv("AUTO_BLOG_OUTPUT_DIR", "output")).expanduser()
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "global").strip() or "global"

    service_account_raw = os.getenv("VERTEX_SERVICE_ACCOUNT_FILE", "gemini_service_account.json").strip()
    service_account_file = Path(service_account_raw).expanduser()
    project = os.getenv("GOOGLE_CLOUD_PROJECT", "").strip()

    if service_account_file.exists():
        return Settings(
            auth_mode="vertex",
            model=model,
            output_dir=output_dir,
            project=project,
            location=location,
            service_account_file=service_account_file,
        )

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if api_key:
        return Settings(
            auth_mode="api_key",
            model=model,
            output_dir=output_dir,
            api_key=api_key,
        )

    raise ValueError(
        "No authentication configured. Set `VERTEX_SERVICE_ACCOUNT_FILE` to a valid service account JSON "
        "for Vertex AI, or set `GEMINI_API_KEY` for the Gemini Developer API."
    )
