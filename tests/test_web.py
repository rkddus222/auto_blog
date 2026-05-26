from fastapi.testclient import TestClient

from auto_blog.web import DashboardState, app, parse_keywords


def test_parse_keywords_for_web_form() -> None:
    assert parse_keywords("ai, automation, startup") == ["ai", "automation", "startup"]


def test_dashboard_state_defaults() -> None:
    state = DashboardState()
    assert state.idea_count == 10
    assert state.ideas == []


def test_index_renders_without_env_key() -> None:
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "프롬프트 편집" in response.text
