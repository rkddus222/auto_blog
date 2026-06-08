from pathlib import Path

from auto_blog.prompts import BlogRequest
from auto_blog.writer import extract_title, save_post, slugify


def test_slugify_basic() -> None:
    assert slugify("Hello, Gemini Blog!") == "hello-gemini-blog"


def test_extract_title_from_markdown() -> None:
    markdown = "# Test Title\n\nBody"
    assert extract_title(markdown, "Fallback") == "Test Title"


def test_extract_title_from_plain_blog_text() -> None:
    markdown = "네이버 블로그용 제목\n\n본문입니다."
    assert extract_title(markdown, "Fallback") == "네이버 블로그용 제목"


def test_save_post_adds_front_matter(tmp_path: Path) -> None:
    request = BlogRequest(topic="AI writing", keywords=["ai", "blog"])
    post = save_post("본문입니다.", topic="AI writing", request=request, output_dir=tmp_path)

    saved = post.path.read_text(encoding="utf-8")
    assert saved.startswith("---")
    assert "# AI writing" not in saved
    assert "본문입니다." in saved
