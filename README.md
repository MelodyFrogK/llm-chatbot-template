# FastAPI LLM Chatbot Template

이 템플릿은 아래 구조를 기준으로 합니다.

- Nginx: 외부 진입점, reverse proxy
- FastAPI: 웹/API 서버
- LLM: Ollama 기반 추론 서버
- RAG: 문서 적재/검색 서버

## 기본 아키텍처

User → Nginx VM → FastAPI VM → (RAG VM optional) → LLM Server

## 빠른 시작

```bash
git clone <YOUR_REPO_URL>
cd fastapi-llm-chatbot-template
cp .env.example .env
```

역할별 설치 스크립트 실행:

```bash
bash scripts/install_nginx_vm.sh
bash scripts/install_fastapi_vm.sh
bash scripts/install_rag_vm.sh
```

## 로컬 개발 실행

```bash
cd fastapi-app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 주요 API

- GET `/health`
- POST `/chat`
- POST `/chat/stream`
- POST `/rag/search`

## 운영 배포 개요

- FastAPI: uvicorn 또는 gunicorn + uvicorn worker
- Nginx: `/api/` 를 FastAPI VM으로 proxy
- systemd: FastAPI / RAG 서비스 등록
