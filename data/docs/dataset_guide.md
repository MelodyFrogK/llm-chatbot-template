# Game RAG Dataset Guide

권장 폴더 구조
- data/raw/items_master.csv
- data/raw/user_inventory.csv
- data/raw/sample_queries.csv
- data/derived/rag_documents_seed.jsonl
- data/sql/create_tables.sql
- data/sql/pgvector_search_examples.sql

학습 흐름
1. 원본 CSV 보기
2. 청킹 규칙 설계
3. JSONL 생성
4. 임베딩 생성
5. rag_documents 적재
6. 검색 호출