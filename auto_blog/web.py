from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from auto_blog.config import load_settings
from auto_blog.graph_flow import run_blog_graph
from auto_blog.git_ops import publish_file
from auto_blog.gemini_client import GeminiBlogClient
from auto_blog.prompt_manager import extract_prompt_overrides, load_prompt_templates
from auto_blog.prompts import BlogRequest
from auto_blog.topic_ideas import TopicIdeasRequest, generate_topic_ideas


@dataclass(slots=True)
class DashboardState:
    topic: str = ""
    audience: str = "general readers"
    tone: str = "professional and practical"
    language: str = "Korean"
    cta: str = ""
    keywords: str = ""
    model: str = ""
    seed: str = ""
    idea_count: int = 10
    ideas: list[str] = field(default_factory=list)
    draft_title: str = ""
    draft_markdown: str = ""
    draft_path: str = ""
    commit_message: str = ""
    publish_result: str = ""
    error_message: str = ""
    prompt_blog: str = ""
    prompt_research: str = ""
    prompt_outline: str = ""
    prompt_draft: str = ""
    prompt_polish: str = ""
    prompt_topic_ideas: str = ""
    prompt_blog_image: str = ""


BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="auto_blog")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def parse_keywords(raw_keywords: str) -> list[str]:
    return [item.strip() for item in raw_keywords.split(",") if item.strip()]


def to_context(request: Request, state: DashboardState) -> dict[str, object]:
    return {
        "request": request,
        "state": asdict(state),
    }


def build_client(model_override: str) -> tuple[GeminiBlogClient, str]:
    settings = load_settings()
    model = model_override.strip() or settings.model
    client = GeminiBlogClient(settings=settings, model=model)
    return client, model


def default_model() -> str:
    try:
        return load_settings().model
    except Exception:
        return "gemini-2.5-flash"


def build_request(
    topic: str,
    audience: str,
    tone: str,
    language: str,
    cta: str,
    keywords: str,
) -> BlogRequest:
    return BlogRequest(
        topic=topic.strip(),
        audience=audience.strip(),
        tone=tone.strip(),
        language=language.strip(),
        cta=cta.strip(),
        keywords=parse_keywords(keywords),
    )


def default_prompt_state() -> dict[str, str]:
    templates = load_prompt_templates()
    return {f"prompt_{key}": value for key, value in templates.as_dict().items()}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    state = DashboardState(model=default_model(), **default_prompt_state())
    return templates.TemplateResponse(request, "index.html", to_context(request, state))


@app.post("/ideas", response_class=HTMLResponse)
async def ideas(
    request: Request,
    seed: str = Form(...),
    audience: str = Form("general readers"),
    language: str = Form("Korean"),
    keywords: str = Form(""),
    count: int = Form(10),
    model: str = Form(""),
    prompt_blog: str = Form(""),
    prompt_research: str = Form(""),
    prompt_outline: str = Form(""),
    prompt_draft: str = Form(""),
    prompt_polish: str = Form(""),
    prompt_topic_ideas: str = Form(""),
    prompt_blog_image: str = Form(""),
) -> HTMLResponse:
    prompt_templates = load_prompt_templates(extract_prompt_overrides(locals()))
    state = DashboardState(
        seed=seed,
        audience=audience,
        language=language,
        keywords=keywords,
        idea_count=count,
        model=model,
        **{f"prompt_{key}": value for key, value in prompt_templates.as_dict().items()},
    )
    try:
        client, resolved_model = build_client(model)
        state.model = resolved_model
        state.ideas = generate_topic_ideas(
            request=TopicIdeasRequest(
                seed=seed.strip(),
                audience=audience.strip(),
                language=language.strip(),
                count=count,
                keywords=parse_keywords(keywords),
            ),
            generator=client.generate_markdown,
            templates=prompt_templates,
        )
    except Exception as exc:
        state.error_message = str(exc)
    return templates.TemplateResponse(request, "index.html", to_context(request, state))


@app.post("/draft", response_class=HTMLResponse)
async def draft(
    request: Request,
    topic: str = Form(...),
    audience: str = Form("general readers"),
    tone: str = Form("professional and practical"),
    language: str = Form("Korean"),
    cta: str = Form(""),
    keywords: str = Form(""),
    model: str = Form(""),
    prompt_blog: str = Form(""),
    prompt_research: str = Form(""),
    prompt_outline: str = Form(""),
    prompt_draft: str = Form(""),
    prompt_polish: str = Form(""),
    prompt_topic_ideas: str = Form(""),
    prompt_blog_image: str = Form(""),
) -> HTMLResponse:
    prompt_templates = load_prompt_templates(extract_prompt_overrides(locals()))
    state = DashboardState(
        topic=topic,
        audience=audience,
        tone=tone,
        language=language,
        cta=cta,
        keywords=keywords,
        model=model,
        **{f"prompt_{key}": value for key, value in prompt_templates.as_dict().items()},
    )
    try:
        client, resolved_model = build_client(model)
        settings = load_settings()
        state.model = resolved_model
        post = run_blog_graph(
            request=build_request(topic, audience, tone, language, cta, keywords),
            output_dir=settings.output_dir,
            generator=client.generate_markdown,
            save_output=True,
            prompt_templates=prompt_templates,
        )
        state.draft_title = post.title
        state.draft_markdown = post.markdown
        state.draft_path = str(post.path)
        state.commit_message = f"Add blog post: {post.slug}"
    except Exception as exc:
        state.error_message = str(exc)
    return templates.TemplateResponse(request, "index.html", to_context(request, state))


@app.post("/publish", response_class=HTMLResponse)
async def publish(
    request: Request,
    topic: str = Form(...),
    audience: str = Form("general readers"),
    tone: str = Form("professional and practical"),
    language: str = Form("Korean"),
    cta: str = Form(""),
    keywords: str = Form(""),
    model: str = Form(""),
    draft_path: str = Form(...),
    draft_title: str = Form(""),
    draft_markdown: str = Form(""),
    commit_message: str = Form(""),
    prompt_blog: str = Form(""),
    prompt_research: str = Form(""),
    prompt_outline: str = Form(""),
    prompt_draft: str = Form(""),
    prompt_polish: str = Form(""),
    prompt_topic_ideas: str = Form(""),
    prompt_blog_image: str = Form(""),
) -> HTMLResponse:
    prompt_templates = load_prompt_templates(extract_prompt_overrides(locals()))
    state = DashboardState(
        topic=topic,
        audience=audience,
        tone=tone,
        language=language,
        cta=cta,
        keywords=keywords,
        model=model,
        draft_path=draft_path,
        draft_title=draft_title,
        draft_markdown=draft_markdown,
        commit_message=commit_message,
        **{f"prompt_{key}": value for key, value in prompt_templates.as_dict().items()},
    )
    try:
        target = Path(draft_path)
        if not target.exists():
            client, resolved_model = build_client(model)
            state.model = resolved_model
            settings = load_settings()
            post = run_blog_graph(
                request=build_request(topic, audience, tone, language, cta, keywords),
                output_dir=settings.output_dir,
                generator=client.generate_markdown,
                save_output=True,
                prompt_templates=prompt_templates,
            )
            state.draft_title = post.title
            state.draft_markdown = post.markdown
            state.draft_path = str(post.path)
            target = post.path
        else:
            state.model = model.strip() or default_model()
        result = publish_file(
            repo_dir=Path.cwd(),
            target=target,
            commit_message=commit_message.strip() or None,
        )
        state.publish_result = f"{result.commit_message} pushed to {result.pushed_to}"
    except Exception as exc:
        state.error_message = str(exc)
    return templates.TemplateResponse(request, "index.html", to_context(request, state))


def run() -> None:
    uvicorn.run("auto_blog.web:app", host="127.0.0.1", port=8000, reload=False)
