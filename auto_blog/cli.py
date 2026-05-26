from __future__ import annotations

import argparse
import sys
from pathlib import Path

from auto_blog.config import load_settings
from auto_blog.git_ops import publish_file
from auto_blog.gemini_client import GeminiBlogClient
from auto_blog.prompts import BlogRequest
from auto_blog.topic_ideas import TopicIdeasRequest, generate_topic_ideas
from auto_blog.writer import generate_and_save, generate_only

KNOWN_COMMANDS = {"write", "ideas", "publish"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate blog content and publish it with Gemini.")
    subparsers = parser.add_subparsers(dest="command")

    write_parser = subparsers.add_parser("write", help="Generate a blog post draft")
    write_parser.add_argument("topic", help="Main blog topic")
    write_parser.add_argument("--audience", default="general readers", help="Target audience")
    write_parser.add_argument("--tone", default="professional and practical", help="Desired tone")
    write_parser.add_argument("--language", default="Korean", help="Output language")
    write_parser.add_argument("--cta", default="", help="Optional call to action")
    write_parser.add_argument(
        "--keywords",
        default="",
        help="Comma-separated SEO keywords",
    )
    write_parser.add_argument(
        "--model",
        default="",
        help="Override GEMINI_MODEL just for this run",
    )
    write_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print generated markdown instead of saving it",
    )

    ideas_parser = subparsers.add_parser("ideas", help="Generate blog topic ideas")
    ideas_parser.add_argument("seed", help="Seed theme or niche")
    ideas_parser.add_argument("--audience", default="general readers", help="Target audience")
    ideas_parser.add_argument("--language", default="Korean", help="Output language")
    ideas_parser.add_argument("--count", type=int, default=10, help="Number of ideas to generate")
    ideas_parser.add_argument("--keywords", default="", help="Comma-separated keywords")
    ideas_parser.add_argument("--model", default="", help="Override GEMINI_MODEL just for this run")

    publish_parser = subparsers.add_parser("publish", help="Generate a post and commit/push it")
    publish_parser.add_argument("topic", help="Main blog topic")
    publish_parser.add_argument("--audience", default="general readers", help="Target audience")
    publish_parser.add_argument("--tone", default="professional and practical", help="Desired tone")
    publish_parser.add_argument("--language", default="Korean", help="Output language")
    publish_parser.add_argument("--cta", default="", help="Optional call to action")
    publish_parser.add_argument("--keywords", default="", help="Comma-separated SEO keywords")
    publish_parser.add_argument("--model", default="", help="Override GEMINI_MODEL just for this run")
    publish_parser.add_argument("--commit-message", default="", help="Override git commit message")

    return parser


def parse_keywords(raw_keywords: str) -> list[str]:
    return [item.strip() for item in raw_keywords.split(",") if item.strip()]


def normalize_argv(argv: list[str]) -> list[str]:
    if not argv:
        return ["write"]
    if argv[0] in KNOWN_COMMANDS or argv[0] in {"-h", "--help"}:
        return argv
    return ["write", *argv]


def main() -> int:
    parser = build_parser()
    args = parser.parse_args(normalize_argv(sys.argv[1:]))
    command = args.command or "write"

    try:
        settings = load_settings()
        model = args.model.strip() or settings.model
        client = GeminiBlogClient(api_key=settings.api_key, model=model)

        if command == "ideas":
            request = TopicIdeasRequest(
                seed=args.seed.strip(),
                audience=args.audience.strip(),
                language=args.language.strip(),
                count=args.count,
                keywords=parse_keywords(args.keywords),
            )
            ideas = generate_topic_ideas(request=request, generator=client.generate_markdown)
            for index, idea in enumerate(ideas, start=1):
                print(f"{index}. {idea}")
            return 0

        request = BlogRequest(
            topic=args.topic.strip(),
            audience=args.audience.strip(),
            tone=args.tone.strip(),
            language=args.language.strip(),
            cta=args.cta.strip(),
            keywords=parse_keywords(args.keywords),
        )

        if command == "write" and args.dry_run:
            post = generate_only(request=request, generator=client.generate_markdown)
        else:
            post = generate_and_save(
                request=request,
                output_dir=settings.output_dir,
                generator=client.generate_markdown,
            )
            if command == "publish":
                result = publish_file(
                    repo_dir=Path.cwd(),
                    target=post.path,
                    commit_message=args.commit_message.strip() or None,
                )
    except Exception as exc:  # pragma: no cover
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if command == "write" and args.dry_run:
        print(post.markdown)
    elif command == "publish":
        print(f"Saved draft: {post.path}")
        print(f"Title: {post.title}")
        print(f"Model: {model}")
        print(f"Committed: {result.commit_message}")
        print(f"Pushed to: {result.pushed_to}")
    else:
        print(f"Saved draft: {post.path}")
        print(f"Title: {post.title}")
        print(f"Model: {model}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
