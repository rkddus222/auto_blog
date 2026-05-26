from pathlib import Path

from auto_blog.prompts import BlogRequest
from auto_blog.writer import extract_title, save_post, slugify


def test_slugify_basic() -> None:
    assert slugify("Hello, Gemini Blog!") == "hello-gemini-blog"


def test_extract_title_from_markdown() -> None:
    markdown = "# Test Title\n\nBody"
    assert extract_title(markdown, "Fallback") == "Test Title"


def test_save_post_adds_front_matter(tmp_path: Path) -> None:
    request = BlogRequest(topic="AI writing", keywords=["ai", "blog"])
    post = save_post("본문입니다.", topic="AI writing", request=request, output_dir=tmp_path)

    saved = post.path.read_text(encoding="utf-8")
    assert saved.startswith("---")
    assert "# AI writing" in saved
