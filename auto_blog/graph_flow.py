from __future__ import annotations

from pathlib import Path
from typing import Callable, Literal

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from auto_blog.prompt_manager import PromptTemplates, load_prompt_templates
from auto_blog.prompts import (
    BlogRequest,
    build_draft_prompt,
    build_outline_prompt,
    build_polish_prompt,
    build_research_brief_prompt,
)
from auto_blog.writer import GeneratedPost, generate_post, save_post

PromptGenerator = Callable[[str], str]


class BlogGraphState(TypedDict, total=False):
    request: BlogRequest
    output_dir: Path
    save_output: bool
    generator: PromptGenerator
    prompt_templates: PromptTemplates
    research_brief: str
    outline: str
    draft_markdown: str
    final_markdown: str
    post: GeneratedPost


def research_node(state: BlogGraphState) -> dict[str, str]:
    request = state["request"]
    generator = state["generator"]
    return {
        "research_brief": generator(
            build_research_brief_prompt(request, templates=state["prompt_templates"])
        )
    }


def outline_node(state: BlogGraphState) -> dict[str, str]:
    request = state["request"]
    generator = state["generator"]
    return {
        "outline": generator(
            build_outline_prompt(
                request=request,
                research_brief=state["research_brief"],
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
                research_brief=state["research_brief"],
                outline=state["outline"],
                templates=state["prompt_templates"],
            )
        )
    }


def polish_node(state: BlogGraphState) -> dict[str, str]:
    request = state["request"]
    generator = state["generator"]
    return {
        "final_markdown": generator(
            build_polish_prompt(
                request=request,
                draft_markdown=state["draft_markdown"],
                templates=state["prompt_templates"],
            )
        )
    }


def preview_node(state: BlogGraphState) -> dict[str, GeneratedPost]:
    request = state["request"]
    return {"post": generate_post(state["final_markdown"], topic=request.topic, request=request)}


def save_node(state: BlogGraphState) -> dict[str, GeneratedPost]:
    request = state["request"]
    return {
        "post": save_post(
            state["final_markdown"],
            topic=request.topic,
            request=request,
            output_dir=state["output_dir"],
        )
    }


def after_polish(state: BlogGraphState) -> Literal["save_post_node", "preview_post_node"]:
    return "save_post_node" if state.get("save_output", False) else "preview_post_node"


def build_blog_graph():
    builder = StateGraph(BlogGraphState)
    builder.add_node("research_node", research_node)
    builder.add_node("outline_node", outline_node)
    builder.add_node("draft_node", draft_node)
    builder.add_node("polish_node", polish_node)
    builder.add_node("preview_post_node", preview_node)
    builder.add_node("save_post_node", save_node)
    builder.add_edge(START, "research_node")
    builder.add_edge("research_node", "outline_node")
    builder.add_edge("outline_node", "draft_node")
    builder.add_edge("draft_node", "polish_node")
    builder.add_conditional_edges(
        "polish_node",
        after_polish,
        {"save_post_node": "save_post_node", "preview_post_node": "preview_post_node"},
    )
    builder.add_edge("save_post_node", END)
    builder.add_edge("preview_post_node", END)
    return builder.compile()


def run_blog_graph(
    request: BlogRequest,
    output_dir: Path,
    generator: PromptGenerator,
    save_output: bool,
    prompt_templates: PromptTemplates | None = None,
) -> GeneratedPost:
    graph = build_blog_graph()
    result = graph.invoke(
        {
            "request": request,
            "output_dir": output_dir,
            "save_output": save_output,
            "generator": generator,
            "prompt_templates": prompt_templates or load_prompt_templates(),
        }
    )
    return result["post"]
