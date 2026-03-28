import os
from functools import lru_cache
from pathlib import Path
from typing import List

import psycopg2
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer

from mlx_lm import load, generate


BASE_DIR = Path(__file__).resolve().parent.parent

# .env, .env.db 로드
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / ".env.db")

APP_NAME = os.getenv("APP_NAME", "fastapi-mlx-chatbot")
MLX_MODEL = os.getenv(
    "MLX_MODEL",
    "lmstudio-community/Qwen3-30B-A3B-Instruct-2507-MLX-4bit",
)
MLX_MAX_TOKENS = int(os.getenv("MLX_MAX_TOKENS", "1024"))

RAG_ENABLED = os.getenv("RAG_ENABLED", "true").lower() == "true"
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
RAG_TOP_K_WIDE = int(os.getenv("RAG_TOP_K_WIDE", "30"))

PGHOST = os.getenv("PGHOST", "127.0.0.1")
PGPORT = int(os.getenv("PGPORT", "5432"))
PGDATABASE = os.getenv("PGDATABASE", "game_rag")
PGUSER = os.getenv("PGUSER", "postgres")
PGPASSWORD = os.getenv("PGPASSWORD", "password")

EMBED_MODEL_NAME = "intfloat/multilingual-e5-large"

WEB_DIR = BASE_DIR / "web"

app = FastAPI(title=APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = Field(default_factory=list)
    use_rag: bool = False


def format_embedding(vec: list[float]) -> str:
    return "[" + ",".join(f"{x:.8f}" for x in vec) + "]"


@lru_cache(maxsize=1)
def get_llm():
    model, tokenizer = load(MLX_MODEL)
    return model, tokenizer


@lru_cache(maxsize=1)
def get_embedder():
    return SentenceTransformer(EMBED_MODEL_NAME)


def choose_top_k(query: str) -> int:
    q = query.strip()
    wide_keywords = [
        "전체",
        "모든",
        "전부",
        "목록",
        "리스트",
        "유저 정보",
        "유저정보",
        "모든 유저",
        "전체 유저",
        "전체 무기",
        "전체 방어구",
        "전체 소모품",
    ]
    if any(keyword in q for keyword in wide_keywords):
        return RAG_TOP_K_WIDE
    return RAG_TOP_K


def rewrite_query_with_history(current_message: str, history: List[ChatMessage]) -> str:
    current_message = current_message.strip()
    if not history:
        return current_message

    recent_user_messages = [
        h.content.strip()
        for h in history
        if h.role == "user" and h.content.strip()
    ]
    last_user = recent_user_messages[-1] if recent_user_messages else ""

    short_followups = [
        "방어구는?",
        "무기는?",
        "소모품은?",
        "그럼 방어구는?",
        "그럼 무기는?",
        "그럼 소모품은?",
        "능력치는?",
        "그 능력치는?",
        "그건?",
        "그럼?",
        "그리고?",
    ]

    if current_message in short_followups or len(current_message) <= 8:
        if last_user:
            return f"{last_user} / 후속 질문: {current_message}"
        return current_message

    return current_message


def search_pgvector(query: str, top_k: int = 5) -> list[dict]:
    embedder = get_embedder()
    query_vec = embedder.encode(
        f"query: {query}",
        normalize_embeddings=True,
    ).tolist()
    query_vec_str = format_embedding(query_vec)

    conn = psycopg2.connect(
        host=PGHOST,
        port=PGPORT,
        dbname=PGDATABASE,
        user=PGUSER,
        password=PGPASSWORD,
    )

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                select
                    id,
                    title,
                    category,
                    content,
                    embedding <=> %s::cdb_admin.vector as distance
                from public.rag_documents
                order by embedding <=> %s::cdb_admin.vector
                limit %s
                """,
                (query_vec_str, query_vec_str, top_k),
            )
            rows = cur.fetchall()

        results = []
        for row in rows:
            results.append(
                {
                    "id": row[0],
                    "title": row[1],
                    "category": row[2],
                    "content": row[3],
                    "distance": float(row[4]),
                }
            )
        return results
    finally:
        conn.close()


@app.get("/")
async def index():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "app": APP_NAME,
        "model": MLX_MODEL,
        "rag_enabled": RAG_ENABLED,
        "rag_top_k": RAG_TOP_K,
        "rag_top_k_wide": RAG_TOP_K_WIDE,
        "pg_host": PGHOST,
        "pg_db": PGDATABASE,
    }


@app.post("/chat")
async def chat(request: ChatRequest):
    user_message = request.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="message is empty")

    sources = []
    rag_context = ""
    search_query = user_message
    selected_top_k = RAG_TOP_K

    if request.use_rag and RAG_ENABLED:
        try:
            search_query = rewrite_query_with_history(user_message, request.history)
            selected_top_k = choose_top_k(search_query)
            sources = search_pgvector(search_query, selected_top_k)

            if sources:
                rag_context = "\n\n".join(
                    [
                        f"[문서{i+1}] 제목: {doc['title']}\n카테고리: {doc['category']}\n내용: {doc['content']}"
                        for i, doc in enumerate(sources)
                    ]
                )
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"RAG search failed: {repr(exc)}")

    try:
        model, tokenizer = get_llm()

        system_prompt = (
            "당신은 한국어로만 답변하는 챗봇입니다. "
            "반드시 한국어만 사용하고, 영어, 중국어, 일본어 등 다른 언어는 사용하지 마세요. "
            "코드, URL, 고유명사 외에는 외국어를 쓰지 마세요. "
            "답변은 자연스럽고 간결한 한국어로 작성하세요."
        )

        if request.use_rag and RAG_ENABLED and rag_context:
            system_prompt += (
                " 아래 제공되는 검색 문서를 우선적으로 참고해서 답변하세요. "
                "문서에 근거가 있으면 그 내용을 기준으로 답변하고, 문서에 없는 내용은 추측하지 마세요. "
                "후속 질문이라면 이전 대화와 검색 문서를 함께 참고하세요. "
                "목록을 요청받았는데 검색 문서가 여러 개라면 가능한 한 빠짐없이 정리하세요."
            )

        messages = [{"role": "system", "content": system_prompt}]

        for item in request.history:
            if item.role in ["user", "assistant", "system"] and item.content.strip():
                messages.append({"role": item.role, "content": item.content})

        if rag_context:
            messages.append(
                {
                    "role": "system",
                    "content": (
                        f"검색에 사용한 질의: {search_query}\n"
                        f"검색 문서 개수: {len(sources)}\n\n"
                        f"검색 문서:\n{rag_context}"
                    ),
                }
            )

        messages.append({"role": "user", "content": user_message})

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

        return {
            "model": MLX_MODEL,
            "response": response,
            "sources": sources,
            "search_query": search_query,
            "top_k": selected_top_k,
        }

    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"MLX generate failed: {repr(exc)}")
