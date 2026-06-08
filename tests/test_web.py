from fastapi.testclient import TestClient

from auto_blog.web import DashboardState, TONE_OPTIONS, app, image_prompt_from_post, parse_keywords, render_markdown


def test_parse_keywords_for_web_form() -> None:
    assert parse_keywords("ai, automation, startup") == ["ai", "automation", "startup"]


def test_dashboard_state_defaults() -> None:
    state = DashboardState()
    assert state.audience == "일반 독자"
    assert state.keywords == []
    assert state.title_candidates == []
    assert state.tags == []


def test_index_renders_without_env_key() -> None:
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "에이전트 실행" in response.text
    assert "처음 입력 한 번" in response.text
    assert 'select name="tone"' in response.text
    assert TONE_OPTIONS[0] in response.text
    assert 'name="cta"' not in response.text
    assert "대표 이미지 생성" not in response.text


def test_image_prompt_uses_final_markdown() -> None:
    prompt = image_prompt_from_post(
        topic="AI 자동화",
        title="AI 자동화 전략",
        audience="스타트업 운영자",
        markdown="# AI 자동화 전략\n\n반복 업무를 줄이는 방법",
    )
    assert "AI 자동화 전략" in prompt
    assert "반복 업무를 줄이는 방법" in prompt


def test_render_markdown_outputs_safe_html() -> None:
    rendered = render_markdown("# 제목\n\n**강조** <script>alert(1)</script>")
    assert "<h1>제목</h1>" in rendered
    assert "<strong>강조</strong>" in rendered
    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered
