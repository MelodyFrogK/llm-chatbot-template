# FastAPI + MLX-LM Chatbot Template

macOS Apple Silicon 환경에서 **MLX-LM**을 사용해 로컬 LLM을 실행하고,  
**FastAPI**로 웹/API 서버를 제공하는 챗봇 템플릿입니다.

## 아키텍처

```text
User → Web UI → FastAPI → MLX-LM
User → Web UI → FastAPI → PostgreSQL(pgvector) → RAG(optional)
```

## 디렉토리 구조

```text
llm-chatbot-template
├── fastapi-app
├── nginx
├── rag
├── scripts
├── deploy
├── docs
├── web
├── data
│   ├── raw
│   ├── derived
│   ├── sql
│   └── docs
├── README.md
└── .env.example
```

---

## 1. 로컬 실행 방법

### 1-1. 저장소 다운로드

```bash
git clone https://github.com/MelodyFrogK/llm-chatbot-template.git
cd llm-chatbot-template
```

### 1-2. FastAPI 가상환경 생성

```bash
cd fastapi-app
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 1-2-1. 기존 가상환경 다시 진입

```bash
cd fastapi-app
source .venv/bin/activate
```

가상환경이 활성화되면 프롬프트 앞에 `(.venv)` 가 표시됩니다.

### 1-2-2. 가상환경 종료

```bash
deactivate
```

### 1-3. 환경파일 생성

```bash
cp .env.example .env
```

### 1-4. `.env` 예시

```env
APP_NAME=fastapi-mlx-chatbot
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000

MLX_MODEL=lmstudio-community/Qwen3-30B-A3B-Instruct-2507-MLX-4bit
MLX_MAX_TOKENS=512

RAG_ENABLED=false
RAG_BASE_URL=http://127.0.0.1:8100
```

### 1-5. MLX-LM 모델 테스트

```bash
cd fastapi-app
source .venv/bin/activate
python3 -c "from mlx_lm import load, generate; model, tokenizer = load('lmstudio-community/Qwen3-30B-A3B-Instruct-2507-MLX-4bit'); print(generate(model, tokenizer, prompt='안녕하세요. 한글로 짧게 인사해줘.', verbose=False))"
```

### 1-6. FastAPI 실행

```bash
cd fastapi-app
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 1-7. 확인

- Swagger UI: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/health`
- Web UI: `http://127.0.0.1:8000`

---

## 2. Chat API 테스트

```bash
curl -X POST http://127.0.0.1:8000/chat \
-H "Content-Type: application/json" \
-d '{"message":"안녕하세요. 한글로 자기소개 해줘.","use_rag":false,"history":[]}'
```

정상 응답 예시:

```json
{
  "model": "lmstudio-community/Qwen3-30B-A3B-Instruct-2507-MLX-4bit",
  "response": "안녕하세요. 저는 질문에 답변하고 설명을 도와드리는 로컬 챗봇입니다.",
  "sources": []
}
```

---

## 3. Web UI 테스트

브라우저에서 질문을 입력하고 FastAPI 응답을 받을 수 있습니다.

동작 구조:

```text
Browser → /chat → FastAPI → MLX-LM
```

현재 Web UI 기능:
- 채팅형 입력/응답
- Enter 전송
- 한글 조합 중복 전송 방지
- 프론트엔드 history 저장 기반 문맥 유지

---

## 4. 데이터셋 구조

실습용 데이터는 `data` 폴더 하위에 둡니다.

```text
data/
├── raw/
│   ├── items_master.csv
│   ├── user_inventory.csv
│   └── sample_queries.csv
├── derived/
│   └── rag_documents_seed.jsonl
├── sql/
│   ├── create_tables.sql
│   └── pgvector_search_examples.sql
└── docs/
    └── dataset_guide.md
```

파일 역할:
- `items_master.csv` → 장비/소모품 마스터 원본
- `user_inventory.csv` → 유저 보유 아이템 원본
- `sample_queries.csv` → 검색 테스트 질문
- `rag_documents_seed.jsonl` → 청킹 완료 예시 문서

---

## 5. PostgreSQL + pgvector 구성

실습용 데이터베이스 이름은 `game_rag` 를 사용합니다.

### 5-1. 관리자/현재 사용자 및 스키마 상태 확인

테이블 만들기 전에 먼저 현재 접속 계정과 스키마 상태를 확인합니다.

```sql
select current_user;
select session_user;
show search_path;
select current_schema();
```

필요하면 `public` 스키마 권한과 소유자를 확인합니다.

```sql
\dn+
```

### 5-2. search_path 설정

일반 테이블은 `public` 스키마에 만들고, 확장 타입은 `cdb_admin` 을 사용합니다.

```sql
set search_path = "$user", public;
```

### 5-3. 테이블 생성

```sql
create table if not exists public.items_master (
    item_id      text primary key,
    category     text not null,
    item_name    text not null,
    attack       integer,
    accuracy     integer,
    defense      integer,
    effect       text,
    rarity       text
);

create table if not exists public.user_inventory (
    inventory_id bigserial primary key,
    user_id      text not null,
    user_name    text not null,
    category     text not null,
    item_name    text not null,
    count        integer not null check (count >= 0)
);

create table if not exists public.rag_documents (
    id         text primary key,
    source     text not null,
    doc_type   text not null,
    category   text not null,
    title      text not null,
    content    text not null,
    embedding  cdb_admin.vector(1024)
);
```

### 5-4. 조회 예시

김택진 인벤토리 조회:

```sql
select user_name, category, item_name, count
from public.user_inventory
where user_name = '김택진'
order by category, item_name;
```

은빛검 능력치 조회:

```sql
select item_name, attack, accuracy, rarity
from public.items_master
where item_name = '은빛검';
```

---

## 6. CSV 원본 적재

실습 순서:
1. `data/raw/items_master.csv` 확인
2. `data/raw/user_inventory.csv` 확인
3. PostgreSQL 테이블 생성
4. CSV 적재
5. 적재 결과 select로 확인

---

## 7. RAG 임베딩 및 PostgreSQL 적재

### 7-1. RAG 단계용 패키지 설치

가상환경에 진입한 뒤 아래 패키지를 설치합니다.

```bash
cd fastapi-app
source .venv/bin/activate
pip install sentence-transformers psycopg2-binary tqdm
```

패키지 역할:
- `sentence-transformers` : 문서를 임베딩 벡터로 변환
- `psycopg2-binary` : PostgreSQL 접속 및 insert/select
- `tqdm` : 임베딩/적재 진행률 표시

### 7-2. DB 접속 정보 파일 생성

레포 루트에 `.env.db` 파일을 만듭니다.

```bash
nano .env.db
```

내용 예시:

```env
PGHOST=DB서버IP
PGPORT=5432
PGDATABASE=game_rag
PGUSER=계정
PGPASSWORD=비밀번호
```

### 7-3. 실행

레포 루트에서 실행합니다.

```bash
cd ~/llm-chatbot-template
source fastapi-app/.venv/bin/activate
export $(grep -v '^#' .env.db | xargs)
python3 rag/ingest_pgvector.py
```

### 7-4. 현재 ingest 동작

`rag/ingest_pgvector.py` 는 아래 파일을 읽습니다.

```text
data/derived/rag_documents_seed.jsonl
```

동작 흐름:

```text
JSONL 문서 읽기
→ multilingual-e5-large 임베딩 생성
→ public.rag_documents insert
→ on conflict 시 update
```

### 7-5. 적재 확인

```sql
select count(*) from public.rag_documents;
```

```sql
select id, title, category
from public.rag_documents
limit 10;
```

---

## 8. 학생 실습 흐름

### Lab 1. 저장소 clone
### Lab 2. Python 가상환경 생성
### Lab 3. MLX-LM 모델 테스트
### Lab 4. FastAPI 실행
### Lab 5. `/health`, `/chat` 테스트
### Lab 6. Web UI 연결
### Lab 7. CSV 원본 확인
### Lab 8. PostgreSQL 사용자/스키마 상태 확인
### Lab 9. PostgreSQL 테이블 생성
### Lab 10. CSV 적재
### Lab 11. 청킹 JSONL 확인
### Lab 12. 임베딩 생성 및 pgvector 적재
### Lab 13. 유사도 검색
### Lab 14. FastAPI RAG 연동

---

## 9. 자주 발생하는 문제

### `.env` 파일이 안 보임

숨김 파일이므로 `ls -la` 로 확인하거나 아래로 생성합니다.

```bash
cp .env.example .env
```

### `ModuleNotFoundError: No module named 'mlx_lm'`

가상환경에 진입하지 않았거나 패키지가 설치되지 않은 경우입니다.

```bash
cd fastapi-app
source .venv/bin/activate
pip install -r requirements.txt
```

### `ModuleNotFoundError: No module named 'sentence_transformers'`

RAG 단계용 패키지가 설치되지 않은 경우입니다.

```bash
source fastapi-app/.venv/bin/activate
pip install sentence-transformers psycopg2-binary tqdm
```

### `FileNotFoundError: data/derived/rag_documents_seed.jsonl`

실행 위치가 잘못된 경우입니다.  
레포 루트에서 실행합니다.

```bash
cd ~/llm-chatbot-template
python3 rag/ingest_pgvector.py
```

### `psycopg2.OperationalError: 127.0.0.1 port 5432 connection refused`

로컬 DB가 아니라 Ncloud DB를 써야 하므로 `.env.db` 의 `PGHOST` 를 실제 DB 서버 주소로 지정해야 합니다.

### `permission denied for schema cdb_admin`

`cdb_admin` 은 확장 전용 스키마입니다.  
일반 테이블은 `public` 에 만들고, vector 타입만 `cdb_admin.vector(...)` 로 사용합니다.

### `no schema has been selected to create in`

`search_path` 가 비정상이거나 기본 스키마가 선택되지 않은 상태입니다.  
먼저 아래를 확인합니다.

```sql
select current_user;
show search_path;
select current_schema();
```

그리고 필요하면:

```sql
set search_path = "$user", public;
```

### `/chat` 접속 시 `Method Not Allowed`

`/chat` 은 POST 전용입니다.  
브라우저 주소창으로 직접 열지 말고 `/docs`, `curl`, Web UI 로 테스트합니다.

### GitHub push 인증 실패

GitHub 비밀번호 대신 PAT 토큰을 사용해야 합니다.

---

## 10. 운영 방향

현재 템플릿은 **macOS 로컬 개발 기준**입니다.

권장 운영 구조:

```text
개발: Mac + MLX-LM
운영: Linux VM + Nginx + FastAPI + PostgreSQL(pgvector) + 별도 추론엔진 + RAG
```

즉,
- 개발은 MLX-LM
- 운영은 Linux 기반 별도 추론엔진(vLLM, Ollama 등) 분리 권장

---

## 11. Git 반영 예시

```bash
git add .
git commit -m "Update README for pgvector RAG workflow"
git push
```
