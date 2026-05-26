from auto_blog.prompt_manager import extract_prompt_overrides, load_prompt_templates, render_prompt


def test_load_prompt_templates_reads_defaults() -> None:
    templates = load_prompt_templates()
    assert "블로그 대표 이미지를 생성합니다." in templates.blog_image
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
