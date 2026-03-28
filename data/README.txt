# data 폴더 운영 기준

이 데이터셋은 llm-chatbot-template/data 아래에 두고 관리하는 것을 기준으로 정리되었습니다.

파일명 규칙
- raw/items_master.csv        -> public.items_master 적재용
- raw/user_inventory.csv      -> public.user_inventory 적재용
- raw/sample_queries.csv      -> 검색 테스트 질문
- derived/rag_documents_seed.jsonl -> public.rag_documents 적재 전 청킹 결과 예시

추천 저장 위치
llm-chatbot-template/
└── data/
    ├── raw/
    ├── derived/
    ├── sql/
    └── docs/