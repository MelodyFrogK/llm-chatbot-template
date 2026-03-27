from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="rag-service")


class SearchRequest(BaseModel):
    query: str
    top_k: int = 3


@app.get("/health")
async def health():
    return {"status": "ok", "service": "rag"}


@app.post("/search")
async def search(req: SearchRequest):
    return {
        "query": req.query,
        "results": [
            {"id": 1, "text": "예시 문서 조각 1", "score": 0.91},
            {"id": 2, "text": "예시 문서 조각 2", "score": 0.88},
        ][: req.top_k]
    }
