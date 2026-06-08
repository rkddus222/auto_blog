from __future__ import annotations

from dataclasses import dataclass, field

from auto_blog.prompt_manager import PromptTemplates, load_prompt_templates, render_prompt


@dataclass(slots=True)
class BlogRequest:
    topic: str
    audience: str = "general readers"
    tone: str = "professional and practical"
    language: str = "Korean"
    cta: str = ""
    keywords: list[str] = field(default_factory=list)


def _join_keywords(keywords: list[str]) -> str:
    return ", ".join(keywords) if keywords else "없음"


def _cta_text(cta: str) -> str:
    return cta if cta else "명시된 CTA 없음"


def _blog_context_block(request: BlogRequest) -> str:
    return f"""
기본 정보:
- 주제: {request.topic}
- 타깃 독자: {request.audience}
- 톤앤매너: {request.tone}
- 출력 언어: {request.language}
- SEO 키워드: {_join_keywords(request.keywords)}
- CTA: {_cta_text(request.cta)}
""".strip()


def _templates(overrides: PromptTemplates | None = None) -> PromptTemplates:
    return overrides or load_prompt_templates()


def _request_values(request: BlogRequest) -> dict[str, str]:
    return {
        "topic": request.topic,
        "audience": request.audience,
        "tone": request.tone,
        "language": request.language,
        "keywords": _join_keywords(request.keywords),
        "cta": _cta_text(request.cta),
        "context_block": _blog_context_block(request),
    }


def build_blog_prompt(request: BlogRequest, templates: PromptTemplates | None = None) -> str:
    return render_prompt(_templates(templates).blog, _request_values(request))


def build_keyword_prompt(request: BlogRequest, templates: PromptTemplates | None = None) -> str:
    values = _request_values(request)
    return render_prompt(_templates(templates).keywords, values)


def build_classification_prompt(request: BlogRequest, templates: PromptTemplates | None = None) -> str:
    values = _request_values(request)
    return render_prompt(_templates(templates).classify_topic, values)


def build_tool_research_prompt(
    request: BlogRequest,
    classification: str,
    templates: PromptTemplates | None = None,
) -> str:
    values = _request_values(request)
    values["classification"] = classification
    return render_prompt(_templates(templates).research_tool, values)


def build_research_brief_prompt(request: BlogRequest, templates: PromptTemplates | None = None) -> str:
    values = _request_values(request)
    return render_prompt(_templates(templates).research, values)


def build_outline_prompt(
    request: BlogRequest,
    research_brief: str,
    templates: PromptTemplates | None = None,
) -> str:
    values = _request_values(request)
    values["research_brief"] = research_brief
    return render_prompt(_templates(templates).outline, values)


def build_draft_prompt(
    request: BlogRequest,
    research_brief: str = "",
    outline: str = "",
    templates: PromptTemplates | None = None,
) -> str:
    values = _request_values(request)
    values["research_brief"] = research_brief
    values["outline"] = outline
    return render_prompt(_templates(templates).draft, values)


def build_tool_draft_prompt(
    request: BlogRequest,
    classification: str,
    research_notes: str,
    templates: PromptTemplates | None = None,
) -> str:
    values = _request_values(request)
    values["classification"] = classification
    values["research_notes"] = research_notes
    return render_prompt(_templates(templates).draft_tool, values)


def build_polish_prompt(
    request: BlogRequest,
    draft_markdown: str,
    classification: str = "",
    research_notes: str = "",
    templates: PromptTemplates | None = None,
) -> str:
    values = _request_values(request)
    values["draft_markdown"] = draft_markdown
    values["classification"] = classification or "없음"
    values["research_notes"] = research_notes or "없음"
    return render_prompt(_templates(templates).polish, values)


def build_grounded_validation_prompt(
    request: BlogRequest,
    draft_markdown: str,
    classification: str,
    research_notes: str,
    templates: PromptTemplates | None = None,
) -> str:
    values = _request_values(request)
    values["draft_markdown"] = draft_markdown
    values["classification"] = classification
    values["research_notes"] = research_notes
    return render_prompt(_templates(templates).validate_grounded, values)


def build_metadata_prompt(
    request: BlogRequest,
    final_text: str,
    templates: PromptTemplates | None = None,
) -> str:
    values = _request_values(request)
    values["final_text"] = final_text
    return render_prompt(_templates(templates).metadata, values)


def build_topic_ideas_prompt(
    seed: str,
    audience: str,
    language: str,
    count: int,
    keywords: list[str],
    templates: PromptTemplates | None = None,
) -> str:
    values = {
        "seed": seed,
        "audience": audience,
        "language": language,
        "count": count,
        "keywords": _join_keywords(keywords),
    }
    return render_prompt(_templates(templates).topic_ideas, values)


def build_blog_image_prompt(
    topic: str,
    title: str = "",
    audience: str = "general readers",
    style_hint: str = "clean editorial illustration",
    templates: PromptTemplates | None = None,
) -> str:
    values = {
        "topic": topic,
        "title": title or "없음",
        "audience": audience,
        "style_hint": style_hint,
    }
    return render_prompt(_templates(templates).blog_image, values)
