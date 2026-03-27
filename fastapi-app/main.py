import os
from typing import AsyncGenerator, Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "fastapi-llm-chatbot")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
RAG_ENABLED = os.getenv("RAG_ENABLED", "false").lower() == "true"
RAG_BASE_URL = os.getenv("RAG_BASE_URL", "http://127.0.0.1:8100")

app = FastAPI(title=APP_NAME)


class ChatRequest(BaseModel):
    message: str
    use_rag: bool = False


class RagSearchRequest(BaseModel):
    query: str
    top_k: int = 3


async def rag_search(query: str, top_k: int = 3) -> dict:
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(f"{RAG_BASE_URL}/search", json={"query": query, "top_k": top_k})
        resp.raise_for_status()
        return resp.json()


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "app": APP_NAME}


@app.post("/chat")
async def chat(request: ChatRequest) -> dict:
    prompt = request.message
    sources = []

    if request.use_rag and RAG_ENABLED:
        try:
            rag_result = await rag_search(request.message, 3)
            chunks = rag_result.get("results", [])
            if chunks:
                context = "\n\n".join([item.get("text", "") for item in chunks])
                sources = chunks
                prompt = f"다음 참고 문서를 바탕으로 답변하세요.\n\n[문서]\n{context}\n\n[질문]\n{request.message}"
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"RAG request failed: {exc}")

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }

    try:
        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Ollama request failed: {exc}")

    return {
        "model": OLLAMA_MODEL,
        "response": data.get("response", ""),
        "sources": sources
    }


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": request.message,
        "stream": True
    }

    async def event_generator() -> AsyncGenerator[bytes, None]:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", f"{OLLAMA_BASE_URL}/api/generate", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line:
                        yield (line + "\n").encode("utf-8")

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")


@app.post("/rag/search")
async def proxy_rag_search(request: RagSearchRequest) -> dict:
    if not RAG_ENABLED:
        raise HTTPException(status_code=400, detail="RAG is disabled")
    return await rag_search(request.query, request.top_k)
