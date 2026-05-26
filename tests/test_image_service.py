from pathlib import Path

from auto_blog.image_service import (
    build_default_blog_image_prompt,
    extension_for_mime_type,
    save_generated_image,
)


def test_extension_for_mime_type() -> None:
    assert extension_for_mime_type("image/png") == ".png"
    assert extension_for_mime_type("image/jpeg") == ".jpg"


def test_save_generated_image(tmp_path: Path) -> None:
    generated = save_generated_image(
        image_bytes=b"abc",
        mime_type="image/png",
        output_dir=tmp_path,
        title_or_topic="AI Topic",
        prompt="prompt",
    )
    assert generated.path.exists()
    assert generated.path.suffix == ".png"


def test_build_default_blog_image_prompt() -> None:
    prompt = build_default_blog_image_prompt(
        "AI automation",
        "Test Title",
        "startup founders",
        "clean editorial illustration",
    )
    assert "AI automation" in prompt
    assert "Test Title" in prompt
    assert "이미지 내부에는 어떤 텍스트" in prompt
