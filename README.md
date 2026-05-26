# auto_blog

Gemini를 사용해 블로그 초안을 자동 생성하는 Python 프로젝트입니다. CLI와 웹 UI를 같이 제공합니다.

## 1. 설치

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

## 2. 환경 변수 설정

```bash
cp .env.example .env
```

기본 인증 방식은 Vertex AI 서비스 계정 JSON입니다. 현재 저장소에는 `gemini_service_account.json` 파일명을 기준으로 읽도록 구성했습니다.

```env
GEMINI_MODEL=gemini-2.5-flash
AUTO_BLOG_OUTPUT_DIR=output
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=global
VERTEX_SERVICE_ACCOUNT_FILE=gemini_service_account.json
GEMINI_API_KEY=
```

우선순위는 다음과 같습니다.

- `VERTEX_SERVICE_ACCOUNT_FILE`가 가리키는 JSON 파일이 있으면 Vertex AI로 인증
- 없으면 `GEMINI_API_KEY`로 Gemini Developer API 사용

`gemini_service_account.json`은 민감 정보이므로 Git에 올리지 않도록 `.gitignore`에 추가했습니다.

## 3. 사용 예시

### 웹 UI 실행

```bash
autoblog-web
```

브라우저에서 `http://127.0.0.1:8000`으로 접속하면 다음 흐름을 사용할 수 있습니다.

- 주제 아이디어 생성
- 블로그 초안 생성
- 생성된 Markdown 미리보기
- Git 커밋 및 푸시

## 4. LangGraph 파이프라인

글 생성은 이제 LangGraph 다중 노드로 동작합니다.

- `research`: 독자 의도와 핵심 포인트 정리
- `outline`: 제목과 섹션 구조 설계
- `draft`: 초안 작성
- `polish`: 문장 흐름과 SEO 표현 정리
- `preview` 또는 `save`: `dry-run`이면 메모리에서만 반환, 일반 실행이면 파일 저장

구현 파일은 [auto_blog/graph_flow.py](/mnt/d/GitHub/auto_blog/auto_blog/graph_flow.py)입니다.

## 5. 프롬프트 구조

프롬프트는 이제 코드에 박아두지 않고 [auto_blog/prompt_presets](/mnt/d/GitHub/auto_blog/auto_blog/prompt_presets) 아래 Markdown 파일로 분리했습니다.

- `topic_ideas.md`
- `research.md`
- `outline.md`
- `draft.md`
- `polish.md`
- `blog_image.md`

템플릿 변수는 `${topic}`, `${audience}`, `${language}`, `${keywords}`, `${research_brief}`, `${outline}` 같은 형태로 치환됩니다.

웹 UI에서는 각 단계의 프롬프트를 textarea로 직접 수정해 바로 실행할 수 있습니다.

## 6. CLI 사용

주제 아이디어 먼저 뽑기:

```bash
autoblog ideas "AI 자동화" \
  --audience "스타트업 운영자" \
  --keywords "자동화,에이전트,생산성" \
  --count 10
```

초안 생성:

```bash
autoblog write "2026년 AI 자동화 트렌드" \
  --audience "스타트업 운영자" \
  --tone "명확하고 실무적" \
  --language "Korean" \
  --keywords "AI 자동화,생산성,업무 효율" \
  --cta "뉴스레터 구독을 유도"
```

생성된 초안은 `output/` 아래에 Markdown 파일로 저장됩니다.

대표 이미지 생성:

```bash
autoblog image "AI 자동화로 반복 업무 줄이는 방법" \
  --title "업무 효율 급상승! AI 자동화로 반복 업무를 줄이는 방법" \
  --audience "1인 사업자"
```

생성된 이미지는 `output/images/` 아래에 저장됩니다.

생성 후 Git 커밋과 푸시까지 한 번에:

```bash
autoblog publish "2026년 AI 자동화 트렌드" \
  --audience "스타트업 운영자" \
  --keywords "AI 자동화,생산성,업무 효율"
```

`publish`는 다음을 수행합니다.

- Markdown 파일 생성
- 해당 파일만 `git add`
- 자동 커밋 메시지 생성
- 현재 브랜치 upstream으로 `git push`

주의:

- 현재 브랜치에 upstream이 먼저 설정되어 있어야 합니다.
- 예: `git push -u origin main`

## 7. 테스트

```bash
pytest
```
