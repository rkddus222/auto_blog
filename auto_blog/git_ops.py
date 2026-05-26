from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class GitPublishResult:
    branch: str
    commit_message: str
    pushed_to: str


def run_git(args: list[str], repo_dir: Path) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def current_branch(repo_dir: Path) -> str:
    return run_git(["branch", "--show-current"], repo_dir)


def upstream_branch(repo_dir: Path) -> str:
    try:
        return run_git(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], repo_dir)
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        raise ValueError(
            "No upstream is configured for the current branch. "
            "Set one with `git push -u origin <branch>` first."
        ) from exc


def ensure_clean_target(repo_dir: Path, target: Path) -> None:
    if not target.exists():
        raise ValueError(f"Cannot publish missing file: {target}")
    try:
        run_git(["rev-parse", "--is-inside-work-tree"], repo_dir)
    except subprocess.CalledProcessError as exc:
        raise ValueError(f"Not a git repository: {repo_dir}") from exc


def publish_file(repo_dir: Path, target: Path, commit_message: str | None = None) -> GitPublishResult:
    ensure_clean_target(repo_dir, target)
    branch = current_branch(repo_dir)
    upstream = upstream_branch(repo_dir)
    message = commit_message or f"Add blog post: {target.stem}"

    run_git(["add", str(target)], repo_dir)
    run_git(["commit", "-m", message], repo_dir)
    run_git(["push"], repo_dir)
    return GitPublishResult(branch=branch, commit_message=message, pushed_to=upstream)
