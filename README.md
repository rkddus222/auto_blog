# auto_blog

Gemini API를 사용해 블로그 초안을 자동 생성하는 Python CLI 프로젝트입니다.

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

`.env`에 Gemini API 키를 넣습니다.

```env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash
AUTO_BLOG_OUTPUT_DIR=output
```

공식 Gemini Python 예시는 `google-genai` 패키지와 `from google import genai` 방식을 사용합니다.

## 3. 사용 예시

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

## 4. 테스트

```bash
pytest
```
