# FastAPI + MLX-LM Chatbot Template

macOS Apple Silicon 환경에서 **MLX-LM**을 사용해 로컬 LLM을 실행하고,
**FastAPI**로 웹/API 서버를 제공하는 챗봇 템플릿입니다.

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

### 1-2-1. 기존 가상환경 다시 진입

이미 가상환경을 만든 뒤 다시 작업할 때는 아래처럼 진입합니다.

```bash
cd fastapi-app
source .venv/bin/activate
```

가상환경이 활성화되면 프롬프트 앞에 `(.venv)` 가 표시됩니다.

### 1-2-2. 가상환경 종료

작업이 끝나면 아래 명령으로 가상환경을 종료합니다.

```bash
deactivate
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

MLX_MODEL=lmstudio-community/Qwen3-30B-A3B-Instruct-2507-MLX-4bit
MLX_MAX_TOKENS=512

RAG_ENABLED=false
RAG_BASE_URL=http://127.0.0.1:8100
```

### 1-5. MLX-LM 모델 테스트

가상환경에 진입한 상태에서 실행합니다.

```bash
cd fastapi-app
source .venv/bin/activate
python3 -c "from mlx_lm import load, generate; model, tokenizer = load('lmstudio-community/Qwen3-30B-A3B-Instruct-2507-MLX-4bit'); print(generate(model, tokenizer, prompt='안녕하세요. 한글로 짧게 인사해줘.', verbose=False))"
```

### 1-6. FastAPI 실행

```bash
cd fastapi-app
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 1-7. 확인

* Swagger UI: `http://127.0.0.1:8000/docs`
* Health Check: `http://127.0.0.1:8000/health`
* Web UI: `http://127.0.0.1:8000`

---

## 2. Chat API 테스트

```bash
curl -X POST http://127.0.0.1:8000/chat \
-H "Content-Type: application/json" \
-d '{"message":"안녕하세요. 한글로 자기소개 해줘.","use_rag":false}'
```

정상 응답 예시:

```json
{
  "model": "lmstudio-community/Qwen3-30B-A3B-Instruct-2507-MLX-4bit",
  "response": "안녕하세요. 저는 질문에 답변하고 설명을 도와드리는 로컬 챗봇입니다.",
  "sources": []
}
```

---

## 3. Web UI 테스트

`web/index.html` 을 통해 브라우저에서 질문을 입력하고 FastAPI 응답을 받을 수 있습니다.

동작 구조:

```text
Browser → /chat → FastAPI → MLX-LM
```

테스트 순서:

1. FastAPI 실행
2. 브라우저에서 `http://127.0.0.1:8000` 접속
3. 질문 입력
4. 응답 확인

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

### Lab 3. 가상환경 진입 및 패키지 설치

### Lab 4. MLX-LM 모델 테스트

### Lab 5. FastAPI 실행

### Lab 6. `/health`, `/chat` 테스트

### Lab 7. Web UI 연결

### Lab 8. RAG 구조 이해 및 확장

---

## 6. 자주 발생하는 문제

### `.env` 파일이 안 보임

숨김 파일이므로 `ls -la` 로 확인하거나 아래로 생성합니다.

```bash
cp .env.example .env
```

### `ModuleNotFoundError: No module named 'mlx_lm'`

가상환경에 진입하지 않았거나 패키지가 설치되지 않은 경우입니다.

```bash
cd fastapi-app
source .venv/bin/activate
pip install -r requirements.txt
```

### `zsh: command not found: python`

macOS에서는 `python` 대신 `python3` 를 사용하는 경우가 많습니다.

```bash
python3 --version
```

### `zsh: command not found: --prompt`

명령어 없이 옵션만 입력한 경우입니다.
옵션 앞에 실행 명령어가 있어야 합니다.

잘못된 예시:

```bash
--prompt "안녕하세요"
```

정상 예시:

```bash
mlx_lm.generate --prompt "안녕하세요"
```

### `/chat` 접속 시 `Method Not Allowed`

`/chat` 은 **POST 전용**입니다.
브라우저 주소창으로 직접 열면 `GET` 요청이 들어가므로 405가 발생할 수 있습니다.

테스트는 아래 중 하나로 진행합니다.

* `/docs`
* `curl`
* Web UI

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
* 운영은 Linux 기반 별도 추론엔진(Ollama, vLLM 등) 분리 권장

---

## 8. Git 반영 예시

README 또는 코드 수정 후 아래처럼 반영합니다.

```bash
git add .
git commit -m "Update README for MLX-LM workflow"
git push
```

