from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Literal

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from auto_blog.prompt_manager import PromptTemplates, load_prompt_templates
from auto_blog.prompts import (
    BlogRequest,
    build_classification_prompt,
    build_draft_prompt,
    build_keyword_prompt,
    build_metadata_prompt,
    build_polish_prompt,
    build_grounded_validation_prompt,
    build_tool_draft_prompt,
    build_tool_research_prompt,
)
from auto_blog.writer import GeneratedPost, generate_post, save_post

PromptGenerator = Callable[[str], str]

TOOL_TOPIC_TYPES = {"tool_tutorial", "command_reference"}
CURRENT_FACT_TOPIC_TYPES = {"comparison", "recommendation", "news_or_current"}


class BlogGraphState(TypedDict, total=False):
    request: BlogRequest
    output_dir: Path
    save_output: bool
    generator: PromptGenerator
    grounded_generator: PromptGenerator
    prompt_templates: PromptTemplates
    classification_text: str
    classification: dict[str, object]
    keywords_text: str
    research_notes: str
    draft_markdown: str
    final_markdown: str
    validated_markdown: str
    metadata_text: str
    metadata: dict[str, object]
    post: GeneratedPost


@dataclass(slots=True)
class BlogGraphResult:
    post: GeneratedPost
    keywords: list[str]
    keywords_text: str
    draft_markdown: str
    final_markdown: str
    classification: dict[str, object] = field(default_factory=dict)
    classification_text: str = ""
    research_notes: str = ""
    metadata: dict[str, object] = field(default_factory=dict)
    metadata_text: str = ""


def parse_generated_keywords(raw_keywords: str) -> list[str]:
    keywords: list[str] = []
    for line in raw_keywords.splitlines():
        keyword = line.strip().lstrip("-*0123456789.、) ").strip()
        if keyword:
            keywords.append(keyword)
    return keywords


def parse_classification(raw_text: str) -> dict[str, object]:
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    json_text = match.group(0) if match else cleaned
    try:
        parsed = json.loads(json_text)
    except json.JSONDecodeError:
        return {
            "topic_type": "general_blog",
            "requires_current_facts": False,
            "requires_commands": False,
            "requires_install_steps": False,
            "entities": [],
            "reason": "분류 JSON 파싱 실패로 일반 글 경로를 사용합니다.",
        }

    if not isinstance(parsed, dict):
        parsed = {}

    topic_type = str(parsed.get("topic_type") or "general_blog")
    return {
        "topic_type": topic_type,
        "requires_current_facts": bool(parsed.get("requires_current_facts", False)),
        "requires_commands": bool(parsed.get("requires_commands", False)),
        "requires_install_steps": bool(parsed.get("requires_install_steps", False)),
        "entities": parsed.get("entities") if isinstance(parsed.get("entities"), list) else [],
        "reason": str(parsed.get("reason") or ""),
    }


def parse_metadata(raw_text: str) -> dict[str, object]:
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    json_text = match.group(0) if match else cleaned
    try:
        parsed = json.loads(json_text)
    except json.JSONDecodeError:
        return {"title_candidates": [], "tags": [], "summary": ""}

    if not isinstance(parsed, dict):
        return {"title_candidates": [], "tags": [], "summary": ""}

    title_candidates = parsed.get("title_candidates")
    tags = parsed.get("tags")
    return {
        "title_candidates": title_candidates if isinstance(title_candidates, list) else [],
        "tags": tags if isinstance(tags, list) else [],
        "summary": str(parsed.get("summary") or ""),
    }


def classification_to_text(classification: dict[str, object]) -> str:
    return json.dumps(classification, ensure_ascii=False, sort_keys=True)


def classify_topic_node(state: BlogGraphState) -> dict[str, object]:
    request = state["request"]
    generator = state["generator"]
    classification_text = generator(
        build_classification_prompt(request, templates=state["prompt_templates"])
    )
    classification = parse_classification(classification_text)
    return {
        "classification_text": classification_text,
        "classification": classification,
    }


def extract_keywords_node(state: BlogGraphState) -> dict[str, object]:
    request = state["request"]
    generator = state["generator"]
    keywords_text = generator(build_keyword_prompt(request, templates=state["prompt_templates"]))
    keywords = parse_generated_keywords(keywords_text)
    return {
        "keywords_text": keywords_text,
        "request": BlogRequest(
            topic=request.topic,
            audience=request.audience,
            tone=request.tone,
            language=request.language,
            cta=request.cta,
            keywords=keywords,
        ),
    }


def should_research(state: BlogGraphState) -> Literal["research_tool_node", "draft_node"]:
    classification = state.get("classification", {})
    topic_type = str(classification.get("topic_type") or "general_blog")
    if topic_type in TOOL_TOPIC_TYPES:
        return "research_tool_node"
    if topic_type in CURRENT_FACT_TOPIC_TYPES and classification.get("requires_current_facts"):
        return "research_tool_node"
    if classification.get("requires_commands") or classification.get("requires_install_steps"):
        return "research_tool_node"
    return "draft_node"


def research_tool_node(state: BlogGraphState) -> dict[str, str]:
    request = state["request"]
    classification = state.get("classification", {})
    generator = state.get("grounded_generator") or state["generator"]
    return {
        "research_notes": generator(
            build_tool_research_prompt(
                request=request,
                classification=classification_to_text(classification),
                templates=state["prompt_templates"],
            )
        )
    }


def draft_node(state: BlogGraphState) -> dict[str, str]:
    request = state["request"]
    generator = state["generator"]
    return {
        "draft_markdown": generator(
            build_draft_prompt(
                request=request,
                templates=state["prompt_templates"],
            )
        )
    }


def tool_draft_node(state: BlogGraphState) -> dict[str, str]:
    request = state["request"]
    generator = state["generator"]
    classification = state.get("classification", {})
    return {
        "draft_markdown": generator(
            build_tool_draft_prompt(
                request=request,
                classification=classification_to_text(classification),
                research_notes=state.get("research_notes", ""),
                templates=state["prompt_templates"],
            )
        )
    }


def polish_node(state: BlogGraphState) -> dict[str, str]:
    request = state["request"]
    generator = state["generator"]
    classification = state.get("classification", {})
    return {
        "final_markdown": generator(
            build_polish_prompt(
                request=request,
                draft_markdown=state["draft_markdown"],
                classification=classification_to_text(classification),
                research_notes=state.get("research_notes", ""),
                templates=state["prompt_templates"],
            )
        )
    }


def preview_node(state: BlogGraphState) -> dict[str, GeneratedPost]:
    request = state["request"]
    final_markdown = state.get("validated_markdown") or state["final_markdown"]
    return {"post": generate_post(final_markdown, topic=request.topic, request=request)}


def save_node(state: BlogGraphState) -> dict[str, GeneratedPost]:
    request = state["request"]
    final_markdown = state.get("validated_markdown") or state["final_markdown"]
    return {
        "post": save_post(
            final_markdown,
            topic=request.topic,
            request=request,
            output_dir=state["output_dir"],
        )
    }


def validate_grounded_node(state: BlogGraphState) -> dict[str, str]:
    request = state["request"]
    generator = state["generator"]
    classification = state.get("classification", {})
    return {
        "validated_markdown": generator(
            build_grounded_validation_prompt(
                request=request,
                draft_markdown=state["final_markdown"],
                classification=classification_to_text(classification),
                research_notes=state.get("research_notes", ""),
                templates=state["prompt_templates"],
            )
        )
    }


def metadata_node(state: BlogGraphState) -> dict[str, object]:
    request = state["request"]
    generator = state["generator"]
    final_text = state.get("validated_markdown") or state["final_markdown"]
    metadata_text = generator(
        build_metadata_prompt(
            request=request,
            final_text=final_text,
            templates=state["prompt_templates"],
        )
    )
    return {
        "metadata_text": metadata_text,
        "metadata": parse_metadata(metadata_text),
    }


def after_polish(state: BlogGraphState) -> Literal["metadata_node"]:
    return "metadata_node"


def after_polish_or_validate(
    state: BlogGraphState,
) -> Literal["validate_grounded_node", "metadata_node"]:
    if state.get("research_notes"):
        return "validate_grounded_node"
    return after_polish(state)


def after_metadata(state: BlogGraphState) -> Literal["save_post_node", "preview_post_node"]:
    return "save_post_node" if state.get("save_output", False) else "preview_post_node"


def build_blog_graph():
    builder = StateGraph(BlogGraphState)
    builder.add_node("classify_topic_node", classify_topic_node)
    builder.add_node("extract_keywords_node", extract_keywords_node)
    builder.add_node("research_tool_node", research_tool_node)
    builder.add_node("draft_node", draft_node)
    builder.add_node("tool_draft_node", tool_draft_node)
    builder.add_node("polish_node", polish_node)
    builder.add_node("validate_grounded_node", validate_grounded_node)
    builder.add_node("metadata_node", metadata_node)
    builder.add_node("preview_post_node", preview_node)
    builder.add_node("save_post_node", save_node)
    builder.add_edge(START, "classify_topic_node")
    builder.add_edge("classify_topic_node", "extract_keywords_node")
    builder.add_conditional_edges(
        "extract_keywords_node",
        should_research,
        {"research_tool_node": "research_tool_node", "draft_node": "draft_node"},
    )
    builder.add_edge("research_tool_node", "tool_draft_node")
    builder.add_edge("draft_node", "polish_node")
    builder.add_edge("tool_draft_node", "polish_node")
    builder.add_conditional_edges(
        "polish_node",
        after_polish_or_validate,
        {
            "validate_grounded_node": "validate_grounded_node",
            "metadata_node": "metadata_node",
        },
    )
    builder.add_conditional_edges(
        "validate_grounded_node",
        after_polish,
        {"metadata_node": "metadata_node"},
    )
    builder.add_conditional_edges(
        "metadata_node",
        after_metadata,
        {"save_post_node": "save_post_node", "preview_post_node": "preview_post_node"},
    )
    builder.add_edge("save_post_node", END)
    builder.add_edge("preview_post_node", END)
    return builder.compile()


def run_blog_graph_details(
    request: BlogRequest,
    output_dir: Path,
    generator: PromptGenerator,
    save_output: bool,
    prompt_templates: PromptTemplates | None = None,
    grounded_generator: PromptGenerator | None = None,
) -> BlogGraphResult:
    graph = build_blog_graph()
    initial_state: BlogGraphState = {
        "request": request,
        "output_dir": output_dir,
        "save_output": save_output,
        "generator": generator,
        "prompt_templates": prompt_templates or load_prompt_templates(),
    }
    if grounded_generator:
        initial_state["grounded_generator"] = grounded_generator

    result = graph.invoke(initial_state)
    keywords_text = result.get("keywords_text", "")
    return BlogGraphResult(
        post=result["post"],
        keywords=parse_generated_keywords(keywords_text),
        keywords_text=keywords_text,
        draft_markdown=result.get("draft_markdown", ""),
        final_markdown=result.get("validated_markdown") or result.get("final_markdown", ""),
        classification=result.get("classification", {}),
        classification_text=result.get("classification_text", ""),
        research_notes=result.get("research_notes", ""),
        metadata=result.get("metadata", {}),
        metadata_text=result.get("metadata_text", ""),
    )


def run_blog_graph(
    request: BlogRequest,
    output_dir: Path,
    generator: PromptGenerator,
    save_output: bool,
    prompt_templates: PromptTemplates | None = None,
    grounded_generator: PromptGenerator | None = None,
) -> GeneratedPost:
    return run_blog_graph_details(
        request=request,
        output_dir=output_dir,
        generator=generator,
        save_output=save_output,
        prompt_templates=prompt_templates,
        grounded_generator=grounded_generator,
    ).post
