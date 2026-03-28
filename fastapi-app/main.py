import os
from functools import lru_cache
from pathlib import Path
from typing import List

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from mlx_lm import load, generate

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "fastapi-mlx-chatbot")
MLX_MODEL = os.getenv("MLX_MODEL", "lmstudio-community/Qwen3-30B-A3B-Instruct-2507-MLX-4bit")
MLX_MAX_TOKENS = int(os.getenv("MLX_MAX_TOKENS", "512"))

RAG_ENABLED = os.getenv("RAG_ENABLED", "false").lower() == "true"
RAG_BASE_URL = os.getenv("RAG_BASE_URL", "http://127.0.0.1:8100")

app = FastAPI(title=APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"

if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
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
        resp = await client.post(
            f"{RAG_BASE_URL}/search",
            json={"query": query, "top_k": top_k},
        )
        resp.raise_for_status()
        return resp.json()


@app.get("/")
async def index():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "app": APP_NAME,
        "model": MLX_MODEL,
    }


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
                    "다음 참고 문서를 바탕으로 답변하세요.\n\n"
                    f"[문서]\n{context}\n\n"
                    f"[질문]\n{request.message}"
                )
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"RAG request failed: {exc}")

    try:
        model, tokenizer = get_model()

        messages = [
            {
                "role": "system",
                "content": (
                    "당신은 한국어로만 답변하는 챗봇입니다. "
                    "반드시 한국어만 사용하고, 영어, 중국어, 일본어 등 다른 언어는 사용하지 마세요. "
                    "코드, URL, 고유명사 외에는 외국어를 쓰지 마세요. "
                    "답변은 자연스럽고 간결한 한국어로 작성하세요."
                ),
            }
        ]

        for item in request.history:
            if item.role in ["user", "assistant", "system"] and item.content.strip():
                messages.append(
                    {
                        "role": item.role,
                        "content": item.content,
                    }
                )

        messages.append(
            {
                "role": "user",
                "content": user_message,
            }
        )

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
