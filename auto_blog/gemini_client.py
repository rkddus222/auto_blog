from __future__ import annotations

from dataclasses import dataclass

from google import genai
from google.genai import types
from google.oauth2 import service_account

from auto_blog.config import Settings


@dataclass(slots=True)
class GeneratedImagePayload:
    image_bytes: bytes
    mime_type: str
    text: str = ""


class GeminiBlogClient:
    def __init__(self, settings: Settings, model: str) -> None:
        self._model = model
        if settings.auth_mode == "vertex":
            if not settings.service_account_file:
                raise ValueError("Vertex AI auth requires a service account file.")
            credentials = service_account.Credentials.from_service_account_file(
                str(settings.service_account_file),
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
            project = settings.project or credentials.project_id or ""
            if not project:
                raise ValueError(
                    "Vertex AI requires a Google Cloud project. "
                    "Set `GOOGLE_CLOUD_PROJECT` or use a service account file with `project_id`."
                )
            self._client = genai.Client(
                vertexai=True,
                project=project,
                location=settings.location,
                credentials=credentials,
                http_options=types.HttpOptions(api_version="v1"),
            )
            return

        if settings.auth_mode == "api_key" and settings.api_key:
            self._client = genai.Client(api_key=settings.api_key)
            return

        raise ValueError("Unsupported auth configuration.")

    def generate_markdown(self, prompt: str) -> str:
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
        )
        text = getattr(response, "text", "") or ""
        if not text.strip():
            raise ValueError("Gemini returned an empty response.")
        return text.strip()

    def generate_grounded_markdown(self, prompt: str) -> str:
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            ),
        )
        text = getattr(response, "text", "") or ""
        if not text.strip():
            raise ValueError("Gemini returned an empty grounded response.")
        return text.strip()

    def generate_image(self, prompt: str, model: str = "gemini-2.5-flash-image") -> GeneratedImagePayload:
        response = self._client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=[types.Modality.TEXT, types.Modality.IMAGE]
            ),
        )

        text_chunks: list[str] = []
        for candidate in getattr(response, "candidates", []) or []:
            content = getattr(candidate, "content", None)
            if not content:
                continue
            for part in getattr(content, "parts", []) or []:
                text = getattr(part, "text", None)
                if text:
                    text_chunks.append(text.strip())
                inline_data = getattr(part, "inline_data", None)
                if inline_data and getattr(inline_data, "data", None):
                    return GeneratedImagePayload(
                        image_bytes=inline_data.data,
                        mime_type=getattr(inline_data, "mime_type", "") or "image/png",
                        text="\n".join(chunk for chunk in text_chunks if chunk).strip(),
                    )

        raise ValueError("Gemini image model did not return an image.")
