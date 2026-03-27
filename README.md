# FastAPI + MLX-LM Chatbot Template

macOS Apple Silicon 환경에서 **MLX-LM**을 사용해 로컬 LLM을 실행하고,
**FastAPI** 로 웹/API 서버를 제공하는 챗봇 템플릿입니다.

## 아키텍처

```text
User → Web UI → FastAPI → MLX-LM
User → Web UI → FastAPI → RAG(optional)
```

## 디렉토리 구조

```text
llm-chatbot-template
├── fastapi-app
├── nginx
├── rag
├── scripts
├── deploy
├── docs
├── web
├── README.md
└── .env.example
```

## 1. 로컬 실행 방법

### 1-1. 저장소 다운로드

```bash
git clone https://github.com/MelodyFrogK/llm-chatbot-template.git
cd llm-chatbot-template
```

### 1-2. FastAPI 가상환경 생성

```bash
cd fastapi-app
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 1-3. 환경파일 생성

```bash
cp .env.example .env
```

### 1-4. `.env` 예시

```env
APP_NAME=fastapi-mlx-chatbot
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000

MLX_MODEL=mlx-community/Qwen2.5-7B-Instruct-4bit
MLX_MAX_TOKENS=256

RAG_ENABLED=false
RAG_BASE_URL=http://127.0.0.1:8100
```

### 1-5. MLX-LM 모델 테스트

```bash
python -c "from mlx_lm import load, generate; model, tokenizer = load('mlx-community/Qwen2.5-7B-Instruct-4bit'); print(generate(model, tokenizer, prompt='안녕하세요. 한글로 짧게 인사해줘.', verbose=False))"
```

### 1-6. FastAPI 실행

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 1-7. 확인

* Swagger UI: `http://127.0.0.1:8000/docs`
* Health Check: `http://127.0.0.1:8000/health`

---

## 2. Chat API 테스트

```bash
curl -X POST http://127.0.0.1:8000/chat \
-H "Content-Type: application/json" \
-d '{"message":"안녕하세요. 한글로 자기소개 해줘."}'
```

정상 응답 예시:

```json
{
  "model": "mlx-community/Qwen2.5-7B-Instruct-4bit",
  "response": "안녕하세요. 저는...",
  "sources": []
}
```

---

## 3. Web UI 테스트

`web/index.html` 을 통해 브라우저에서 질문을 입력하고 FastAPI 응답을 받을 수 있습니다.

동작 구조:

```text
Browser → /api/chat → FastAPI → MLX-LM
```

---

## 4. RAG 기능

현재 RAG는 placeholder 구조입니다.

추후 추가할 기능:

* 문서 업로드
* 문서 분할(chunking)
* 임베딩 생성
* 벡터DB 저장
* 유사도 검색
* 검색 결과 기반 답변 생성

---

## 5. 학생 실습 순서

### Lab 1. 저장소 clone

### Lab 2. Python 가상환경 생성

### Lab 3. MLX-LM 모델 테스트

### Lab 4. FastAPI 실행

### Lab 5. `/health`, `/chat` 테스트

### Lab 6. Web UI 연결

### Lab 7. RAG 구조 이해 및 확장

---

## 6. 자주 발생하는 문제

### `.env` 파일이 안 보임

숨김 파일이므로 `ls -la` 로 확인하거나 아래로 생성:

```bash
cp .env.example .env
```

### `zsh: command not found: --prompt`

명령어 없이 옵션만 입력한 경우입니다.

정상 예시:

```bash
mlx_lm.generate --prompt "안녕하세요"
```

### GitHub push 인증 실패

GitHub 비밀번호 대신 **PAT 토큰**을 사용해야 합니다.

---

## 7. 운영 방향

현재 템플릿은 **macOS 로컬 개발 기준**입니다.

권장 운영 구조:

```text
개발: Mac + MLX-LM
운영: Linux VM + Nginx + FastAPI + 별도 추론엔진 + RAG
```

즉,

* 개발은 MLX-LM
* 운영은 Linux 기반 별도 추론엔진(Ollama/vLLM 등) 분리 권장

