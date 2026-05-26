from pathlib import Path

import pytest

from auto_blog.git_ops import ensure_clean_target


def test_ensure_clean_target_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Cannot publish missing file"):
        ensure_clean_target(tmp_path, tmp_path / "missing.md")
