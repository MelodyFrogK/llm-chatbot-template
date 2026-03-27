import os
from functools import lru_cache
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from mlx_lm import load, generate

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "fastapi-mlx-chatbot")
MLX_MODEL = os.getenv("MLX_MODEL", "mlx-community/Qwen2.5-7B-Instruct-4bit")
MLX_MAX_TOKENS = int(os.getenv("MLX_MAX_TOKENS", "256"))

RAG_ENABLED = os.getenv("RAG_ENABLED", "false").lower() == "true"
RAG_BASE_URL = os.getenv("RAG_BASE_URL", "http://127.0.0.1:8100")

app = FastAPI(title=APP_NAME)

# CORS 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 프로젝트 루트 기준 web 폴더 경로
BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"

if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


class ChatRequest(BaseModel):
    message: str
    use_rag: bool = False


class RagSearchRequest(BaseModel):
    query: str
    top_k: int = 3


@lru_cache(maxsize=1)
def get_model():
    model, tokenizer = load(MLX_MODEL)
    return model, tokenizer


async def rag_search(query: str, top_k: int = 3) -> dict:
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(f"{RAG_BASE_URL}/search", json={"query": query, "top_k": top_k})
        resp.raise_for_status()
        return resp.json()


@app.get("/")
async def index():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "app": APP_NAME, "model": MLX_MODEL}


@app.post("/chat")
async def chat(request: ChatRequest) -> dict:
    sources = []
    user_message = request.message

    if request.use_rag and RAG_ENABLED:
        try:
            rag_result = await rag_search(user_message, 3)
            chunks = rag_result.get("results", [])
            if chunks:
                context = "\n\n".join([item.get("text", "") for item in chunks])
                sources = chunks
                user_message = (
                    "다음 참고 문서를 바탕으로 한국어로만 답변하세요.\n\n"
                    f"[문서]\n{context}\n\n"
                    f"[질문]\n{request.message}"
                )
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"RAG request failed: {exc}")
    else:
        user_message = f"다음 질문에 한국어로만 답변하세요.\n\n{request.message}"

    try:
        model, tokenizer = get_model()
        messages = [{"role": "user", "content": user_message}]
        prompt = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
        )

        response = generate(
            model,
            tokenizer,
            prompt=prompt,
            max_tokens=MLX_MAX_TOKENS,
            verbose=False,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"MLX generate failed: {repr(exc)}")

    return {
        "model": MLX_MODEL,
        "response": response,
        "sources": sources,
    }


@app.post("/rag/search")
async def proxy_rag_search(request: RagSearchRequest) -> dict:
    if not RAG_ENABLED:
        raise HTTPException(status_code=400, detail="RAG is disabled")
    return await rag_search(request.query, request.top_k)
