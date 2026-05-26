from __future__ import annotations

from pathlib import Path

from auto_blog.config import load_settings


def test_load_settings_prefers_vertex_service_account(monkeypatch, tmp_path: Path) -> None:
    credential_file = tmp_path / "service_account.json"
    credential_file.write_text('{"type":"service_account","project_id":"demo-project"}', encoding="utf-8")
    monkeypatch.setenv("VERTEX_SERVICE_ACCOUNT_FILE", str(credential_file))
    monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "global")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    settings = load_settings()

    assert settings.auth_mode == "vertex"
    assert settings.service_account_file == credential_file
    assert settings.location == "global"


def test_load_settings_falls_back_to_api_key(monkeypatch) -> None:
    monkeypatch.setenv("VERTEX_SERVICE_ACCOUNT_FILE", "missing.json")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    settings = load_settings()

    assert settings.auth_mode == "api_key"
    assert settings.api_key == "test-key"
