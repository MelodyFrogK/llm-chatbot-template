import os
from pathlib import Path

import psycopg2
from sentence_transformers import SentenceTransformer

# 현재 파일(rag/search_pgvector.py) 기준으로 레포 루트 계산
BASE_DIR = Path(__file__).resolve().parent.parent

PGHOST = os.getenv("PGHOST", "127.0.0.1")
PGPORT = int(os.getenv("PGPORT", "5432"))
PGDATABASE = os.getenv("PGDATABASE", "game_rag")
PGUSER = os.getenv("PGUSER", "postgres")
PGPASSWORD = os.getenv("PGPASSWORD", "password")

EMBED_MODEL_NAME = "intfloat/multilingual-e5-large"
TOP_K = int(os.getenv("TOP_K", "5"))


def format_embedding(vec):
    return "[" + ",".join(f"{x:.8f}" for x in vec) + "]"


def main():
    query = input("질문 입력: ").strip()
    if not query:
        print("질문이 비어 있습니다.")
        return

    print(f"임베딩 모델 로딩: {EMBED_MODEL_NAME}")
    model = SentenceTransformer(EMBED_MODEL_NAME)

    print(f"질문 임베딩 생성 중: {query}")
    query_vec = model.encode(
        f"query: {query}",
        normalize_embeddings=True
    ).tolist()
    query_vec_str = format_embedding(query_vec)

    print("DB 연결 중...")
    print(f"HOST={PGHOST}, PORT={PGPORT}, DB={PGDATABASE}, USER={PGUSER}")

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
                (query_vec_str, query_vec_str, TOP_K),
            )

            rows = cur.fetchall()

        print(f"\n상위 {TOP_K}개 검색 결과")
        for idx, row in enumerate(rows, start=1):
            print("-" * 100)
            print(f"[{idx}] ID       : {row[0]}")
            print(f"[{idx}] 제목     : {row[1]}")
            print(f"[{idx}] 카테고리 : {row[2]}")
            print(f"[{idx}] 거리     : {row[4]}")
            print(f"[{idx}] 내용     : {row[3]}")

    finally:
        conn.close()
        print("\nDB 연결 종료")


if __name__ == "__main__":
    main()
