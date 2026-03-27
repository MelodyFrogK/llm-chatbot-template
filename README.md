# FastAPI + MLX-LM Chatbot Template

이 템플릿은 macOS Apple Silicon 환경에서 MLX-LM을 사용해 로컬 LLM을 구동하고,
FastAPI로 웹/API 서버를 제공하는 구조입니다.

## 아키텍처
User → Nginx VM → FastAPI VM → MLX-LM
User → Nginx VM → FastAPI VM → RAG VM(optional)

## 로컬 실행

### 1. 가상환경 및 패키지 설치
```bash
cd fastapi-app
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

### 2. MLX 모델 테스트
```bash
python -c "from mlx_lm import load, generate; model, tokenizer = load('mlx-community/Qwen2.5-7B-Instruct-4bit'); print(generate(model, tokenizer, prompt='안녕하세요. 한글로 짧게 인사해줘.', verbose=False))"
```

### 3. FastAPI 실행
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 확인
- Swagger UI: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

## chat API 테스트
```bash
curl -X POST http://127.0.0.1:8000/chat \
-H "Content-Type: application/json" \
-d '{"message":"안녕하세요. 한글로 자기소개 해줘."}'
```

## 환경 변수
`fastapi-app/.env`

```env
APP_NAME=fastapi-mlx-chatbot
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000

MLX_MODEL=mlx-community/Qwen2.5-7B-Instruct-4bit
MLX_MAX_TOKENS=256
MLX_TEMPERATURE=0.7

RAG_ENABLED=false
RAG_BASE_URL=http://127.0.0.1:8100
```

## 학생 실습 흐름
1. 저장소 clone
2. Python 가상환경 생성
3. requirements 설치
4. MLX 모델 테스트
5. FastAPI 실행
6. /health, /chat 테스트
7. Nginx reverse proxy 연결
8. RAG 연동
