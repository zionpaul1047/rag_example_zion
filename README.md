Git Huburl :  https://github.com/zionpaul1047/rag_example_zion

# RAG 검증 문서

- [RAG 수동 검증 체크리스트](docs/rag_manual_verification_checklist.md)

# 1. 전체 흐름도

---

<img width="2035" height="2803" alt="Image" src="https://github.com/user-attachments/assets/59eaedfd-a19a-4faf-9330-8192c9fa36c5" />

---

# 2. 인프라 구성

<img width="2098" height="795" alt="Image" src="https://github.com/user-attachments/assets/b2fb395b-d59f-4601-ab8f-a4ca9ea4a78d" />

현재 로컬 기준:

```
C:\dev\rag_example_zion
 ├─ ai-chatbot          # FastAPI 백엔드
 └─ ai-chatbot-ui       # React 프론트엔드 예정/진행
```

Docker 컨테이너:

```
local-pgvector        PostgreSQL + pgvector
local-elasticsearch   Elasticsearch 8.x
```

---

# 3. DB 모델

## PostgreSQL / pgvector

---

# 4. 전체 프로세스 흐름

## 4-1. 문서 인덱싱 흐름

<img width="2137" height="427" alt="Image" src="https://github.com/user-attachments/assets/c676407e-1030-466f-ac1b-7eeb3ce7f998" />

---

## 4-2. 질문 응답 RAG 흐름

<img width="3760" height="1910" alt="Image" src="https://github.com/user-attachments/assets/496d8e8f-fef7-4563-9756-311cd7608be3" />

---

## 4-3. 승인 기반 문서 라이프사이클

<img width="2137" height="427" alt="Image" src="https://github.com/user-attachments/assets/677db66a-b471-4adb-9e54-52761f54ae39" />

---

# 5. 적용한 주요 패턴

## 1) Pipeline Pattern

문서 처리와 질문 처리를 단계별로 나누기

```
문서 처리:
parse → clean → chunk → embed → save

질문 처리:
retrieve → fuse → rerank → generate → save
```

장점:

```
각 단계가 분리되어 있어서 수정하기 쉽다.
예를 들어 임베딩 모델만 바꾸거나, Reranker만 교체할 수 있다.
```

---

## 2) Adapter Pattern

LLM Provider를 교체할 수 있게 구성

```
Ollama 사용
OpenAI 사용
auto 모드: Ollama 우선, 실패 시 OpenAI fallback
```

발표 설명 예시:

```
LLM 호출부를 직접 하나의 모델에 고정하지 않고 Provider Adapter 형태로 분리했습니다.
그래서 로컬 환경에서는 Ollama를 사용하고, 필요 시 OpenAI API로 전환할 수 있습니다.
```

---

## 3) Hybrid Search Pattern

검색 정확도를 높이기 위해 두 가지 검색을 결합

```
Vector Search: 의미가 비슷한 문서 검색
BM25 Search: 키워드가 정확히 포함된 문서 검색
RRF: 두 결과를 하나로 병합
```

---

## 4) Reranking Pattern

1차 검색 결과를 그대로 쓰지 않고 CrossEncoder로 다시 점수를 매

```
검색 후보 TOP_K 조회
→ RRF로 병합
→ CrossEncoder로 질문과 문서 관련도 재평가
→ 최종 TOP_N_CONTEXT만 LLM에 전달
```

---

## 5) LangGraph State Workflow

질문 처리 과정을 노드 단위로 분리

```
retrieve_node   : 관련 문서 찾기(Vector Search와 BM25 검색)
  ↓
rerank_node     : 찾은 문서 중 진짜 중요한 것 재정렬(CrossEncoder)
  ↓
generate_node   : LLM으로 답변 생성(문서를 context로 구성해 LLM에게 전달)
  ↓
memory_node     : 대화 이력 저장(멀티턴 대화)
  ↓
trace logging   : 전체 과정 기록
```

장점:

```
각 노드의 입력/출력을 trace로 확인 가능
디버깅이 쉬움
나중에 조건 분기, fallback, 평가 노드 추가 가능
```

---

# 6. 주요 파일/코드 위치 정리

```
ai-chatbot/
 ├─ app/
 │   ├─ main.py
 │   ├─ core/
 │   │   └─ config.py
 │   ├─ api/
 │   │   └─ routes/
 │   ├─ services/
 │   │   ├─ document_service.py
 │   │   ├─ embedding_service.py
 │   │   ├─ retrieval_service.py
 │   │   ├─ reranker_service.py
 │   │   ├─ llm_service.py
 │   │   └─ chat_memory_service.py
 │   ├─ rag/
 │   │   ├─ langgraph_pipeline.py
 │   │   ├─ state.py
 │   │   └─ prompt.py
 │   ├─ db/
 │   │   ├─ postgres.py
 │   │   └─ elasticsearch.py
 │   └─ models/
 │       └─ schemas.py
 │
 ├─ tests_manual/
 │   ├─ rag_test.py
 │   ├─ reranker_test.py
 │   ├─ langgraph_rag_test.py
 │   ├─ chat_memory_test.py
 │   ├─ sse_stream_test.py
 │   └─ llm_provider_test.py
 │
 ├─ .env
 ├─ requirements.txt
 └─ docker-compose.yml
```

---

# 8. 주요 코드 기능 설명

## `app/main.py`

FastAPI 서버 시작점

주요 역할:

```
FastAPI 앱 생성
라우터 등록
CORS 설정
health check API 제공
uvicorn 실행 대상
```

실행 명령:

```
uvicorn app.main:app--reload
```

---

## `app/core/config.py`

환경설정 관리 파일

주요 역할:

```
.env 값 로딩
PostgreSQL 접속 정보
Elasticsearch 접속 정보
LLM Provider 설정
Ollama/OpenAI 모델 설정
Chunk size, top_k, timeout 설정
```

예시 설정:

```
LLM_PROVIDER=auto
OLLAMA_MODEL=llama3.2
OPENAI_CHAT_MODEL=gpt-4.1-mini
EMBEDDING_PROVIDER=bge
BGE_MODEL_NAME=BAAI/bge-m3
TOP_K_RETRIEVAL=5
TOP_N_RERANK=3
```

---

## `document_service.py`

문서 업로드 후 텍스트를 추출하는 역할

주요 기능:

```
PDF 파싱
DOCX 파싱
TXT/MD/HTML 파싱
스캔 PDF인 경우 OCR 처리
추출된 텍스트 정제
```

---

## `embedding_service.py`

텍스트 청크를 벡터로 바꾸는 역할

주요 기능:

```
BAAI/bge-m3 모델 로딩
청크별 embedding 생성
batch 단위 임베딩 처리
```

---

## `retrieval_service.py`

검색 담당

주요 기능:

```
pgvector에서 Vector Search
Elasticsearch에서 BM25 Search
두 검색 결과를 RRF로 병합
```

---

## `reranker_service.py`

검색 결과를 다시 정렬

사용 모델:

```
cross-encoder/ms-marco-MiniLM-L-6-v2
```

주요 기능:

```
질문과 문서 청크를 pair로 구성
관련도 점수 계산
상위 N개 문서 선택
```

---

## `llm_service.py`

LLM 호출 담당

주요 기능:

```
Ollama 호출
OpenAI 호출
auto provider 처리
timeout 처리
fallback 처리
streaming 응답 처리
```

---

## `langgraph_pipeline.py`

RAG 질문 처리의 핵심 파일

주요 역할:

```
질문 상태 생성
retrieve node 실행
rerank node 실행
generate node 실행
memory 저장
trace 정보 반환
```

---

## `chat_memory_service.py`

대화 이력 저장/조회 담당

주요 기능:

```
사용자 질문 저장
AI 답변 저장
conversation_id 기준 대화 조회
멀티턴 대화 지원
```

---
