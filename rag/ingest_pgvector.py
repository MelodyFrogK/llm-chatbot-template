import json
import os
from pathlib import Path

import psycopg2
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# 현재 파일(rag/ingest_pgvector.py) 기준으로 레포 루트 계산
BASE_DIR = Path(__file__).resolve().parent.parent

# 절대경로로 데이터 파일 지정
DATA_FILE = BASE_DIR / "data" / "derived" / "rag_documents_seed.jsonl"

# PostgreSQL 접속 정보
PGHOST = os.getenv("PGHOST", "127.0.0.1")
PGPORT = int(os.getenv("PGPORT", "5432"))
PGDATABASE = os.getenv("PGDATABASE", "game_rag")
PGUSER = os.getenv("PGUSER", "postgres")
PGPASSWORD = os.getenv("PGPASSWORD", "password")

# 임베딩 모델
EMBED_MODEL_NAME = "intfloat/multilingual-e5-large"


def format_embedding(vec):
    return "[" + ",".join(f"{x:.8f}" for x in vec) + "]"


def main():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"파일이 없습니다: {DATA_FILE}")

    print(f"데이터 파일: {DATA_FILE}")
    print(f"임베딩 모델 로딩: {EMBED_MODEL_NAME}")

    model = SentenceTransformer(EMBED_MODEL_NAME)

    print("DB 연결 중...")
    print(f"HOST={PGHOST}, PORT={PGPORT}, DB={PGDATABASE}, USER={PGUSER}")

    conn = psycopg2.connect(
        host=PGHOST,
        port=PGPORT,
        dbname=PGDATABASE,
        user=PGUSER,
        password=PGPASSWORD,
    )
    conn.autocommit = False

    with conn.cursor() as cur:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            docs = [json.loads(line) for line in f if line.strip()]

        print(f"총 문서 수: {len(docs)}")

        for doc in tqdm(docs, desc="임베딩 및 적재"):
            content = doc["content"]

            # e5 계열은 query / passage prefix 권장
            embedding = model.encode(
                f"passage: {content}",
                normalize_embeddings=True
            ).tolist()

            embedding_str = format_embedding(embedding)

            cur.execute(
                """
                insert into public.rag_documents (
                    id, source, doc_type, category, title, content, embedding
                )
                values (%s, %s, %s, %s, %s, %s, %s::cdb_admin.vector)
                on conflict (id) do update
                set source = excluded.source,
                    doc_type = excluded.doc_type,
                    category = excluded.category,
                    title = excluded.title,
                    content = excluded.content,
                    embedding = excluded.embedding
                """,
                (
                    doc["id"],
                    doc["source"],
                    doc["doc_type"],
                    doc["category"],
                    doc["title"],
                    doc["content"],
                    embedding_str,
                ),
            )

        conn.commit()
        print("적재 완료")

    conn.close()
    print("DB 연결 종료")


if __name__ == "__main__":
    main()
