from pathlib import Path

from auto_blog.graph_flow import build_blog_graph, run_blog_graph
from auto_blog.prompts import BlogRequest


def test_graph_contains_expected_nodes() -> None:
    graph = build_blog_graph()
    node_names = set(graph.get_graph().nodes.keys())
    assert {
        "research_node",
        "outline_node",
        "draft_node",
        "polish_node",
        "preview_post_node",
        "save_post_node",
    }.issubset(node_names)


def test_run_blog_graph_preview_mode() -> None:
    prompts: list[str] = []

    def fake_generator(prompt: str) -> str:
        prompts.append(prompt)
        if "리서치 브리프" in prompt:
            return "- pain point\n- key claim"
        if "마크다운 아웃라인" in prompt:
            return "# Test Title\n\n## Section"
        if "완성형 블로그 글" in prompt:
            return "# Draft Title\n\nBody"
        return "# Final Title\n\nPolished body"

    post = run_blog_graph(
        request=BlogRequest(topic="AI topic"),
        output_dir=Path("output"),
        generator=fake_generator,
        save_output=False,
    )

    assert post.title == "Final Title"
    assert post.path == Path("")
    assert len(prompts) == 4


def test_run_blog_graph_save_mode(tmp_path: Path) -> None:
    def fake_generator(prompt: str) -> str:
        if "리서치 브리프" in prompt:
            return "- research"
        if "마크다운 아웃라인" in prompt:
            return "# Save Title\n\n## Outline"
        if "완성형 블로그 글" in prompt:
            return "# Save Title\n\nDraft"
        return "# Save Title\n\nFinal"

    post = run_blog_graph(
        request=BlogRequest(topic="Save topic"),
        output_dir=tmp_path,
        generator=fake_generator,
        save_output=True,
    )

    assert post.path.exists()
    assert post.title == "Save Title"
