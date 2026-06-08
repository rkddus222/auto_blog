from auto_blog.prompt_manager import extract_prompt_overrides, load_prompt_templates, render_prompt
from auto_blog.prompts import BlogRequest, build_classification_prompt, build_metadata_prompt, build_tool_research_prompt


def test_load_prompt_templates_reads_defaults() -> None:
    templates = load_prompt_templates()
    assert "블로그 대표 이미지를 생성합니다." in templates.blog_image
    assert "블로그 작성 요청을 분석" in templates.classify_topic
    assert "핵심 키워드" in templates.keywords
    assert "공식 문서" in templates.research_tool
    assert "제품/도구 사용법 글을 작성" in templates.draft_tool
    assert "사실성을 점검" in templates.validate_grounded
    assert "업로드를 돕는 콘텐츠 마케터" in templates.metadata
    assert "리서치 브리프" in templates.research


def test_render_prompt_substitutes_values() -> None:
    rendered = render_prompt("안녕 ${name}", {"name": "세상"})
    assert rendered == "안녕 세상"


def test_extract_prompt_overrides_filters_empty_values() -> None:
    overrides = extract_prompt_overrides(
        {
            "prompt_blog": "블로그 프롬프트",
            "prompt_draft": "",
            "prompt_polish": "다듬기 프롬프트",
        }
    )
    assert overrides == {
        "blog": "블로그 프롬프트",
        "polish": "다듬기 프롬프트",
    }


def test_tool_research_prompt_is_topic_agnostic() -> None:
    prompt = build_tool_research_prompt(
        BlogRequest(topic="클로드 코드 사용법"),
        classification='{"topic_type":"tool_tutorial"}',
    )
    assert "공식 문서" in prompt
    assert "클로드 코드 사용법" in prompt
    assert "curl -fsSL https://claude.ai/install.sh | bash" not in prompt


def test_classification_prompt_requests_json() -> None:
    prompt = build_classification_prompt(BlogRequest(topic="Docker 설치법"))
    assert "JSON 객체만 출력합니다" in prompt


def test_metadata_prompt_requests_upload_helpers() -> None:
    prompt = build_metadata_prompt(BlogRequest(topic="AI 자동화"), "AI 자동화 제목\n\n본문")
    assert "title_candidates" in prompt
    assert "tags" in prompt
    assert "summary" in prompt
