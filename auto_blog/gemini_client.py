from __future__ import annotations

from google import genai


class GeminiBlogClient:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def generate_markdown(self, prompt: str) -> str:
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
        )
        text = getattr(response, "text", "") or ""
        if not text.strip():
            raise ValueError("Gemini returned an empty response.")
        return text.strip()
