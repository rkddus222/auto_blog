from pathlib import Path

from auto_blog.graph_flow import (
    build_blog_graph,
    parse_classification,
    parse_generated_keywords,
    parse_metadata,
    run_blog_graph,
    run_blog_graph_details,
)
from auto_blog.prompts import BlogRequest


def test_graph_contains_expected_nodes() -> None:
    graph = build_blog_graph()
    node_names = set(graph.get_graph().nodes.keys())
    assert {
        "classify_topic_node",
        "extract_keywords_node",
        "research_tool_node",
        "draft_node",
        "tool_draft_node",
        "polish_node",
        "validate_grounded_node",
        "metadata_node",
        "preview_post_node",
        "save_post_node",
    }.issubset(node_names)


def test_run_blog_graph_preview_mode() -> None:
    prompts: list[str] = []

    def fake_generator(prompt: str) -> str:
        prompts.append(prompt)
        if "네이버 블로그 업로드를 돕는" in prompt:
            return '{"title_candidates":["제목1","제목2"],"tags":["태그1","태그2"],"summary":"요약"}'
        if "JSON 객체만 출력합니다" in prompt:
            return '{"topic_type":"general_blog","requires_current_facts":false,"requires_commands":false,"requires_install_steps":false,"entities":[]}'
        if "핵심 키워드" in prompt:
            return "AI 자동화\n업무 생산성\n스타트업 운영"
        if "블로그 초안" in prompt:
            assert "AI 자동화, 업무 생산성, 스타트업 운영" in prompt
            assert "Markdown 형식" in prompt
            return "Draft Title\n\nBody"
        return "Final Title\n\nPolished body"

    result = run_blog_graph_details(
        request=BlogRequest(topic="AI topic"),
        output_dir=Path("output"),
        generator=fake_generator,
        save_output=False,
    )

    assert result.post.title == "Final Title"
    assert result.post.path == Path("")
    assert result.keywords == ["AI 자동화", "업무 생산성", "스타트업 운영"]
    assert result.classification["topic_type"] == "general_blog"
    assert result.metadata["summary"] == "요약"
    assert len(prompts) == 5


def test_run_blog_graph_save_mode(tmp_path: Path) -> None:
    def fake_generator(prompt: str) -> str:
        if "네이버 블로그 업로드를 돕는" in prompt:
            return '{"title_candidates":["저장 제목"],"tags":["저장"],"summary":"저장 요약"}'
        if "JSON 객체만 출력합니다" in prompt:
            return '{"topic_type":"general_blog","requires_current_facts":false,"requires_commands":false,"requires_install_steps":false,"entities":[]}'
        if "핵심 키워드" in prompt:
            return "콘텐츠 자동화"
        if "블로그 초안" in prompt:
            return "Save Title\n\nDraft"
        return "Save Title\n\nFinal"

    post = run_blog_graph(
        request=BlogRequest(topic="Save topic"),
        output_dir=tmp_path,
        generator=fake_generator,
        save_output=True,
    )

    assert post.path.exists()
    assert post.title == "Save Title"


def test_parse_generated_keywords_removes_common_markers() -> None:
    raw = "1. AI 자동화\n- 생산성\n* 업무 효율"
    assert parse_generated_keywords(raw) == ["AI 자동화", "생산성", "업무 효율"]


def test_run_blog_graph_routes_tool_topics_to_grounded_research() -> None:
    prompts: list[str] = []
    grounded_prompts: list[str] = []

    def fake_generator(prompt: str) -> str:
        prompts.append(prompt)
        if "네이버 블로그 업로드를 돕는" in prompt:
            assert "검수된 최종 글" in prompt
            return '{"title_candidates":["Claude Code 제목"],"tags":["Claude Code"],"summary":"검수 요약"}'
        if "JSON 객체만 출력합니다" in prompt:
            return (
                '{"topic_type":"tool_tutorial","requires_current_facts":true,'
                '"requires_commands":true,"requires_install_steps":true,"entities":["Claude Code"]}'
            )
        if "핵심 키워드" in prompt:
            return "클로드 코드 설치\n클로드 코드 명령어"
        if "제품/도구 사용법 글을 작성" in prompt:
            assert "공식 설치 명령 확인" in prompt
            return "Claude Code 사용법\n\n설치하고 실행합니다."
        if "사실성을 점검" in prompt:
            return "Claude Code 사용법\n\n검수된 최종 글"
        return "Claude Code 사용법\n\n최종 글"

    def fake_grounded_generator(prompt: str) -> str:
        grounded_prompts.append(prompt)
        return "공식 설치 명령 확인\n주요 슬래시 명령어 확인"

    result = run_blog_graph_details(
        request=BlogRequest(topic="클로드 코드 사용법"),
        output_dir=Path("output"),
        generator=fake_generator,
        grounded_generator=fake_grounded_generator,
        save_output=False,
    )

    assert result.post.title == "Claude Code 사용법"
    assert result.research_notes == "공식 설치 명령 확인\n주요 슬래시 명령어 확인"
    assert result.classification["topic_type"] == "tool_tutorial"
    assert result.metadata["summary"] == "검수 요약"
    assert len(grounded_prompts) == 1


def test_parse_classification_falls_back_on_invalid_json() -> None:
    parsed = parse_classification("분류 실패")
    assert parsed["topic_type"] == "general_blog"


def test_parse_metadata_falls_back_on_invalid_json() -> None:
    parsed = parse_metadata("메타데이터 실패")
    assert parsed == {"title_candidates": [], "tags": [], "summary": ""}
