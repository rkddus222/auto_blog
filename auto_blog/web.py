from __future__ import annotations

import html
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

import markdown
import uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from markupsafe import Markup

from auto_blog.config import load_settings
from auto_blog.gemini_client import GeminiBlogClient
from auto_blog.graph_flow import run_blog_graph_details
from auto_blog.image_service import build_default_blog_image_prompt, save_generated_image
from auto_blog.prompts import BlogRequest


@dataclass(slots=True)
class DashboardState:
    topic: str = ""
    audience: str = "일반 독자"
    tone: str = "명확하고 실무적"
    language: str = "Korean"
    model: str = ""
    keywords: list[str] = field(default_factory=list)
    draft_markdown: str = ""
    final_title: str = ""
    final_markdown: str = ""
    final_html: str = ""
    title_candidates: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    summary: str = ""
    image_path: str = ""
    image_url: str = ""
    image_caption: str = ""
    error_message: str = ""


BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="auto_blog")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

TONE_OPTIONS = (
    "명확하고 실무적",
    "친근하고 쉽게 설명하는",
    "전문적이고 신뢰감 있는",
    "스토리텔링 중심의",
    "검색 최적화에 강한 정보형",
    "문제 해결 중심의",
    "경험담처럼 자연스러운",
    "차분하고 설득력 있는",
)


def parse_keywords(raw_keywords: str) -> list[str]:
    return [item.strip() for item in raw_keywords.split(",") if item.strip()]


def to_context(request: Request, state: DashboardState) -> dict[str, object]:
    return {
        "request": request,
        "state": asdict(state),
        "tone_options": TONE_OPTIONS,
    }


def default_model() -> str:
    try:
        return load_settings().model
    except Exception:
        return "gemini-2.5-flash"


def build_client(model_override: str) -> tuple[GeminiBlogClient, str]:
    settings = load_settings()
    model = model_override.strip() or settings.model
    client = GeminiBlogClient(settings=settings, model=model)
    return client, model


def build_request(topic: str, audience: str, tone: str, language: str) -> BlogRequest:
    return BlogRequest(
        topic=topic.strip(),
        audience=audience.strip(),
        tone=tone.strip(),
        language=language.strip(),
    )


def build_state(
    topic: str,
    audience: str,
    tone: str,
    language: str,
    model: str,
    final_title: str = "",
    final_markdown: str = "",
    keywords: str = "",
    title_candidates: str = "",
    tags: str = "",
    summary: str = "",
) -> DashboardState:
    return DashboardState(
        topic=topic,
        audience=audience,
        tone=tone,
        language=language,
        model=model,
        final_title=final_title,
        final_markdown=final_markdown,
        final_html=render_markdown(final_markdown),
        keywords=parse_keywords(keywords),
        title_candidates=parse_keywords(title_candidates),
        tags=parse_keywords(tags),
        summary=summary,
    )


def image_prompt_from_post(topic: str, title: str, audience: str, markdown: str) -> str:
    base_prompt = build_default_blog_image_prompt(
        topic=topic,
        title=title,
        audience=audience,
        style_hint="clean modern editorial illustration for a business blog",
    )
    excerpt = markdown.strip()[:2400]
    return f"{base_prompt}\n\n최종 블로그 본문 요약 참고:\n{excerpt}"


def render_markdown(markdown_text: str) -> Markup:
    if not markdown_text.strip():
        return Markup("")
    escaped = html.escape(markdown_text)
    rendered = markdown.markdown(
        escaped,
        extensions=["nl2br", "sane_lists"],
        output_format="html5",
    )
    return Markup(rendered)


def image_url_for(path: Path) -> str:
    return f"/generated-images/{path.name}"


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    state = DashboardState(model=default_model())
    return templates.TemplateResponse(request, "index.html", to_context(request, state))


@app.post("/generate", response_class=HTMLResponse)
async def generate(
    request: Request,
    topic: str = Form(...),
    audience: str = Form("일반 독자"),
    tone: str = Form("명확하고 실무적"),
    language: str = Form("Korean"),
    model: str = Form(""),
) -> HTMLResponse:
    state = build_state(topic, audience, tone, language, model)
    try:
        client, resolved_model = build_client(model)
        settings = load_settings()
        result = run_blog_graph_details(
            request=build_request(topic, audience, tone, language),
            output_dir=settings.output_dir,
            generator=client.generate_markdown,
            grounded_generator=client.generate_grounded_markdown,
            save_output=False,
        )
        state.model = resolved_model
        state.keywords = result.keywords
        state.draft_markdown = result.draft_markdown
        state.final_title = result.post.title
        state.final_markdown = result.post.markdown
        state.final_html = render_markdown(result.post.markdown)
        state.title_candidates = [str(item) for item in result.metadata.get("title_candidates", [])]
        state.tags = [str(item) for item in result.metadata.get("tags", [])]
        state.summary = str(result.metadata.get("summary") or "")
    except Exception as exc:
        state.error_message = str(exc)
    return templates.TemplateResponse(request, "index.html", to_context(request, state))


@app.post("/generate-image", response_class=HTMLResponse)
async def generate_image(
    request: Request,
    topic: str = Form(...),
    audience: str = Form("일반 독자"),
    tone: str = Form("명확하고 실무적"),
    language: str = Form("Korean"),
    model: str = Form(""),
    final_title: str = Form(""),
    final_markdown: str = Form(...),
    keywords: str = Form(""),
    title_candidates: str = Form(""),
    tags: str = Form(""),
    summary: str = Form(""),
) -> HTMLResponse:
    state = build_state(
        topic=topic,
        audience=audience,
        tone=tone,
        language=language,
        model=model,
        final_title=final_title,
        final_markdown=final_markdown,
        keywords=keywords,
        title_candidates=title_candidates,
        tags=tags,
        summary=summary,
    )
    try:
        client, resolved_model = build_client(model)
        settings = load_settings()
        prompt = image_prompt_from_post(
            topic=topic,
            title=final_title or topic,
            audience=audience,
            markdown=final_markdown,
        )
        payload = client.generate_image(prompt)
        generated = save_generated_image(
            image_bytes=payload.image_bytes,
            mime_type=payload.mime_type,
            output_dir=settings.output_dir,
            title_or_topic=final_title or topic,
            prompt=prompt,
            caption=payload.text,
        )
        state.model = resolved_model
        state.image_path = str(generated.path)
        state.image_url = image_url_for(generated.path)
        state.image_caption = generated.caption
    except Exception as exc:
        state.error_message = str(exc)
    return templates.TemplateResponse(request, "index.html", to_context(request, state))


@app.get("/generated-images/{file_name}")
async def generated_image(file_name: str) -> FileResponse:
    image_path = load_settings().output_dir / "images" / Path(file_name).name
    return FileResponse(image_path)


def run() -> None:
    host = os.getenv("AUTO_BLOG_HOST", "127.0.0.1")
    port = int(os.getenv("AUTO_BLOG_PORT", "8000"))
    uvicorn.run("auto_blog.web:app", host=host, port=port, reload=False)
