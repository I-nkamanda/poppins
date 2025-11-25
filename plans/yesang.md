# 구현 예상 형태 (Implementation Preview)

## 📋 개요

PRD와 참고 프로그램(Hack-1st, Pop-pins2)을 분석하여 **Python PDF 기반 RAG Tutor (PBL Generator Lite)**의 구체적인 구현 형태를 정리한 문서입니다.

---

## 🏗️ 시스템 아키텍처

### 전체 구조

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (MVP)                       │
│  - 검색창 (질문 입력)                                    │
│  - 답변 표시 영역 (개념 + PBL)                          │
│  - 히스토리 (선택적)                                     │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP Request
┌────────────────────▼────────────────────────────────────┐
│              FastAPI Backend                            │
│  ┌──────────────────────────────────────────────────┐  │
│  │  /ask     - 질문 처리 및 PBL 생성                │  │
│  │  /index   - PDF 인덱싱                           │  │
│  │  /history - 학습 히스토리 조회 (선택적)          │  │
│  └──────────────────────────────────────────────────┘  │
└───────┬───────────────────────┬────────────────────────┘
        │                       │
        ▼                       ▼
┌───────────────┐      ┌──────────────────────┐
│  RAG Engine   │      │  Activity Logs       │
│               │      │  (Feedback Cycle)    │
│  - PDF Loader │      │  - 질문/응답 기록    │
│  - Chunker    │      │  - PBL 수행 여부     │
│  - Embedding  │      │  - 난이도 조정       │
│  - Qdrant     │      └──────────────────────┘
│  - Retriever  │
└───────┬───────┘
        │ context
        ▼
┌───────────────────────┐
│  LLM (Gemini/Vertex)  │
│  - 개념 설명 생성     │
│  - PBL 미션 생성      │
└───────┬───────────────┘
        │
        ▼
┌───────────────────────┐
│  Output (JSON)        │
│  - 개념 요약          │
│  - 예제 코드          │
│  - PDF 인용           │
│  - Mini PBL (3~5개)   │
└───────────────────────┘
```

---

## 📁 프로젝트 구조

### 디렉토리 레이아웃

```
project_root/
├── app/
│   ├── main.py                 # FastAPI 메인 애플리케이션
│   ├── config.py               # 설정 관리 (GCP, API 키 등)
│   ├── models/
│   │   ├── schemas.py          # Pydantic 스키마 (요청/응답)
│   │   └── database.py         # DB 모델 (선택적, 히스토리용)
│   ├── services/
│   │   ├── rag_service.py      # RAG 엔진 서비스
│   │   ├── llm_service.py      # LLM 호출 서비스
│   │   └── pbl_generator.py    # PBL 생성 로직
│   ├── utils/
│   │   ├── pdf_loader.py       # PDF 로더 (PyPDFLoader)
│   │   ├── chunker.py          # 텍스트 분할 (RecursiveCharacterTextSplitter)
│   │   └── embedding.py        # 임베딩 모델 래퍼
│   └── data/
│       ├── RAG/                # Qdrant 벡터DB 저장소
│       │   ├── python_tutor_db/
│       │   └── metadata.json
│       └── pdfs/               # 원본 PDF 파일들
├── frontend/                   # MVP UI (선택적)
│   ├── index.html
│   ├── script.js
│   └── style.css
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🔧 핵심 컴포넌트 구현 예상

### 1. FastAPI 메인 애플리케이션 (`app/main.py`)

**참고**: Hack-1st의 `main.py` 구조 + Pop-pins2의 라우터 패턴

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

from app.services.rag_service import RAGService
from app.services.llm_service import LLMService
from app.services.pbl_generator import PBLGenerator
from app.models.schemas import AskRequest, AskResponse

app = FastAPI(
    title="Python PDF RAG Tutor API",
    description="PDF 기반 RAG 시스템으로 PBL 학습지 자동 생성",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 서비스 초기화 (싱글톤 패턴)
rag_service = RAGService()
llm_service = LLMService()
pbl_generator = PBLGenerator(rag_service, llm_service)

@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """
    질문을 받아 개념 설명 + PBL 미션을 생성합니다.
    
    - RAG로 관련 문서 검색
    - LLM으로 개념 설명 생성
    - PBL 미션 생성 (3~5개)
    """
    try:
        # 1. RAG 검색
        context_docs = await rag_service.search(request.query, k=5)
        
        # 2. LLM으로 개념 설명 생성
        concept_explanation = await llm_service.generate_concept(
            query=request.query,
            context=context_docs,
            level=request.level  # "beginner", "intermediate"
        )
        
        # 3. PBL 미션 생성
        pbl_missions = await pbl_generator.generate(
            query=request.query,
            concept=concept_explanation,
            context=context_docs,
            level=request.level
        )
        
        return AskResponse(
            concept=concept_explanation,
            pbl_missions=pbl_missions,
            sources=[doc.metadata.get("source_file") for doc in context_docs]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/index")
async def index_pdf(file_path: str):
    """
    PDF 파일을 벡터DB에 인덱싱합니다.
    """
    try:
        result = await rag_service.index_pdf(file_path)
        return {"status": "success", "message": f"Indexed {result['chunks']} chunks"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 2. RAG 서비스 (`app/services/rag_service.py`)

**참고**: Hack-1st의 `rag_data_generator.py` 구조

```python
from pathlib import Path
from typing import List, Optional
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from langchain_community.vectorstores import Qdrant

class RAGService:
    def __init__(
        self,
        qdrant_url: str = "http://localhost:6333",
        collection_name: str = "python_tutor",
        embedding_model: str = "models/embedding-001"
    ):
        # 임베딩 모델 초기화 (Gemini 또는 Vertex AI)
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=embedding_model,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        
        # Qdrant 클라이언트
        self.client = QdrantClient(url=qdrant_url)
        
        # 벡터 스토어 초기화
        self.vector_store = self._init_vector_store(collection_name)
        
        # 텍스트 분할기
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
    
    def _init_vector_store(self, collection_name: str):
        """Qdrant 컬렉션 초기화 또는 로드"""
        try:
            return Qdrant(
                client=self.client,
                collection_name=collection_name,
                embeddings=self.embeddings
            )
        except:
            # 컬렉션이 없으면 생성
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=768,  # embedding 차원
                    distance=Distance.COSINE
                )
            )
            return Qdrant(
                client=self.client,
                collection_name=collection_name,
                embeddings=self.embeddings
            )
    
    async def index_pdf(self, pdf_path: str) -> dict:
        """PDF 파일을 벡터DB에 인덱싱"""
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        
        # 메타데이터 추가
        for doc in documents:
            doc.metadata['source_file'] = pdf_path
            doc.metadata['file_name'] = Path(pdf_path).name
        
        # 텍스트 분할
        chunks = self.text_splitter.split_documents(documents)
        
        # 벡터DB에 추가
        self.vector_store.add_documents(chunks)
        
        return {
            "chunks": len(chunks),
            "pages": len(documents)
        }
    
    async def search(self, query: str, k: int = 5) -> List:
        """질문에 대한 유사 문서 검색"""
        docs = self.vector_store.similarity_search(query, k=k)
        return docs
```

### 3. LLM 서비스 (`app/services/llm_service.py`)

**참고**: Pop-pins2의 N8N 워크플로우 + Hack-1st의 Agent 패턴

```python
import google.generativeai as genai
from typing import List, Dict

class LLMService:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    async def generate_concept(
        self,
        query: str,
        context: List,
        level: str = "beginner"
    ) -> Dict:
        """
        개념 설명을 생성합니다.
        
        Returns:
            {
                "summary": "요약",
                "example_code": "예제 코드",
                "explanation": "상세 설명",
                "citations": ["출처 파일명"]
            }
        """
        # 컨텍스트 텍스트 조합
        context_text = "\n\n".join([
            f"[출처: {doc.metadata.get('file_name', 'Unknown')}]\n{doc.page_content}"
            for doc in context
        ])
        
        prompt = f"""
당신은 파이썬 초급 학습자를 위한 튜터입니다.

학습자 질문: {query}
학습자 레벨: {level}

아래 문서를 참고하여 정확한 개념 설명을 생성하세요:

{context_text}

다음 형식으로 응답하세요:
1. 요약 (2-3문장)
2. 예제 코드 (실행 가능한 간단한 코드)
3. 상세 설명 (초급자가 이해하기 쉽게)
4. 출처 인용

JSON 형식으로 응답하세요:
{{
    "summary": "...",
    "example_code": "...",
    "explanation": "...",
    "citations": ["파일명1", "파일명2"]
}}
"""
        
        response = self.model.generate_content(prompt)
        # JSON 파싱 및 반환
        return self._parse_response(response.text)
    
    def _parse_response(self, text: str) -> Dict:
        """LLM 응답을 파싱하여 구조화된 데이터로 변환"""
        # JSON 파싱 로직
        import json
        # ... 파싱 구현
        pass
```

### 4. PBL 생성기 (`app/services/pbl_generator.py`)

**참고**: Pop-pins2의 Exercise 생성 로직 + PRD의 PBL 구조

```python
from typing import List, Dict
from app.services.llm_service import LLMService

class PBLGenerator:
    def __init__(self, rag_service, llm_service: LLMService):
        self.rag_service = rag_service
        self.llm_service = llm_service
    
    async def generate(
        self,
        query: str,
        concept: Dict,
        context: List,
        level: str = "beginner"
    ) -> List[Dict]:
        """
        PBL 미션을 생성합니다.
        
        Returns:
            [
                {
                    "mission_id": 1,
                    "title": "실습 1: 기본 구현",
                    "description": "...",
                    "hint": "...",
                    "solution_template": "..."
                },
                ...
            ]
        """
        prompt = f"""
학습자 질문: {query}
개념 요약: {concept['summary']}
학습자 레벨: {level}

다음 구조로 3~5개의 PBL 미션을 생성하세요:

1. 실습 1: 기본 개념 적용 (쉬움)
2. 실습 2: 응용 문제 (중간)
3. 실습 3: 확장 문제 (어려움, 선택적)

각 미션은 다음 형식:
{{
    "mission_id": 1,
    "title": "미션 제목",
    "description": "학습자가 해야 할 작업 설명",
    "hint": "힌트 (선택적)",
    "solution_template": "해결 방법 템플릿 (선택적)"
}}

JSON 배열로 응답하세요.
"""
        
        response = self.llm_service.model.generate_content(prompt)
        missions = self._parse_missions(response.text)
        
        return missions
    
    def _parse_missions(self, text: str) -> List[Dict]:
        """PBL 미션 JSON 파싱"""
        import json
        # ... 파싱 구현
        pass
```

### 5. Pydantic 스키마 (`app/models/schemas.py`)

**참고**: Pop-pins2의 `schemas.py` 구조

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class AskRequest(BaseModel):
    """질문 요청"""
    query: str = Field(description="학습자 질문")
    level: str = Field(default="beginner", description="학습자 레벨: beginner/intermediate")

class ConceptResponse(BaseModel):
    """개념 설명 응답"""
    summary: str
    example_code: str
    explanation: str
    citations: List[str]

class PBLMission(BaseModel):
    """PBL 미션"""
    mission_id: int
    title: str
    description: str
    hint: Optional[str] = None
    solution_template: Optional[str] = None

class AskResponse(BaseModel):
    """질문 응답 (최종)"""
    concept: ConceptResponse
    pbl_missions: List[PBLMission]
    sources: List[str]  # PDF 출처
```

---

## 🔄 데이터 흐름

### 1. PDF 인덱싱 플로우

```
PDF 파일 업로드
    ↓
PyPDFLoader로 텍스트 추출
    ↓
RecursiveCharacterTextSplitter로 청킹 (1000자, 200자 overlap)
    ↓
GoogleGenerativeAIEmbeddings로 임베딩
    ↓
Qdrant 벡터DB에 저장
    ↓
메타데이터 저장 (파일명, 청크 수 등)
```

### 2. 질문 처리 플로우

```
사용자 질문 입력
    ↓
RAG 검색 (Top-K=5 유사 문서)
    ↓
LLM에 컨텍스트 + 질문 전달
    ↓
개념 설명 생성 (요약 + 예제 코드 + 설명)
    ↓
PBL 생성기로 미션 생성 (3~5개)
    ↓
JSON 응답 반환
```

---

## 🛠️ 기술 스택 상세

### Backend
- **FastAPI**: REST API 프레임워크
- **LangChain**: RAG 파이프라인 (PDF 로더, 텍스트 분할, 벡터 스토어)
- **Qdrant**: 벡터 데이터베이스 (로컬 또는 클라우드)
- **Google Generative AI (Gemini)**: 
  - 임베딩: `models/embedding-001`
  - LLM: `gemini-2.0-flash-exp` 또는 `gemini-pro`
- **Pydantic**: 데이터 검증 및 스키마

### Frontend (MVP)
- **HTML/CSS/JavaScript**: 최소한의 UI
- 또는 **React + Vite** (Pop-pins2 스타일)

### 인프라
- **Qdrant**: Docker로 로컬 실행 또는 Qdrant Cloud
- **GCP**: Vertex AI (선택적, 무료 티어 활용)

---

## 📊 API 엔드포인트 명세

### POST /ask

**요청:**
```json
{
  "query": "LinkedList를 배우고 싶어요",
  "level": "beginner"
}
```

**응답:**
```json
{
  "concept": {
    "summary": "LinkedList는 노드들이 연결된 선형 자료구조입니다...",
    "example_code": "class Node:\n    def __init__(self, data):\n        self.data = data\n        self.next = None",
    "explanation": "상세 설명...",
    "citations": ["python_data_structures.pdf"]
  },
  "pbl_missions": [
    {
      "mission_id": 1,
      "title": "실습 1: Node 클래스 구현",
      "description": "Node 클래스를 만들어보세요...",
      "hint": "data와 next 속성을 가집니다",
      "solution_template": "class Node:\n    def __init__(self, data):\n        # 구현하세요"
    },
    {
      "mission_id": 2,
      "title": "실습 2: LinkedList 기본 연산",
      "description": "..."
    }
  ],
  "sources": ["python_data_structures.pdf"]
}
```

### POST /index

**요청:**
```json
{
  "file_path": "/path/to/python_tutorial.pdf"
}
```

**응답:**
```json
{
  "status": "success",
  "message": "Indexed 150 chunks from 20 pages"
}
```

---

## 🎯 MVP 구현 우선순위

### Phase 1: 핵심 기능 (필수)
1. ✅ PDF → Qdrant 인덱싱
2. ✅ RAG 검색 구현
3. ✅ LLM 개념 설명 생성
4. ✅ PBL 미션 생성 (기본 3개)
5. ✅ FastAPI `/ask` 엔드포인트

### Phase 2: UI 및 개선 (선택)
6. ⚠️ 최소 UI (검색창 + 답변 표시)
7. ⚠️ 히스토리 저장 (SQLite 또는 JSON)
8. ⚠️ 난이도 조정 로직

---

## 🔍 참고 프로그램에서 가져올 패턴

### Hack-1st에서
- ✅ **RAG 데이터 생성기 구조**: `rag_data_generator.py`
  - PDF 로더, 청킹, 임베딩, 벡터DB 저장
  - 메타데이터 관리 (파일 해시, 처리 상태)
- ✅ **FAISS → Qdrant 전환**: Qdrant가 더 확장 가능

### Pop-pins2에서
- ✅ **API 라우터 구조**: `/v1/concept`, `/v1/exercise` 패턴
- ✅ **Pydantic 스키마**: 요청/응답 모델 정의
- ✅ **교육 콘텐츠 생성**: Concept + Exercise 구조
- ✅ **단일 학습 페이지**: 한 번에 모든 데이터 조회

---

## ⚠️ 주의사항 및 고려사항

### 1. 임베딩 모델 선택
- **Gemini Embedding**: 무료 티어 활용 가능
- **Vertex AI Embedding**: GCP 통합 시 사용
- **SentenceTransformer**: 로컬 실행 가능 (성능은 낮음)

### 2. 벡터DB 선택
- **Qdrant**: PRD 명시, 확장 가능
- **FAISS**: Hack-1st에서 사용, 파일 기반 (간단)

### 3. LLM 선택
- **Gemini 2.0 Flash**: 빠르고 저렴
- **Gemini Pro**: 더 정확한 응답
- **Vertex AI**: GCP 통합 시 사용

### 4. 에러 처리
- PDF 로딩 실패 → `pdfminer` fallback
- LLM 환각 → RAG 컨텍스트 강제 포함
- 벡터DB 오류 → 재시도 로직

---

## 📝 다음 단계

1. **프로젝트 초기 설정**
   - `requirements.txt` 작성
   - `.env.example` 생성
   - 기본 디렉토리 구조 생성

2. **RAG 서비스 구현**
   - PDF 로더 통합
   - Qdrant 설정
   - 인덱싱 스크립트 작성

3. **LLM 서비스 구현**
   - Gemini API 연동
   - 프롬프트 템플릿 작성
   - 응답 파싱 로직

4. **PBL 생성기 구현**
   - 미션 생성 프롬프트
   - 난이도별 분류
   - JSON 파싱

5. **FastAPI 통합**
   - 엔드포인트 구현
   - 에러 처리
   - 로깅

6. **MVP UI 구현**
   - 간단한 HTML/JS
   - API 호출
   - 결과 표시

---

## 📚 참고 자료

- **PRD**: `prd.md`
- **Hack-1st**: `References/Hack-1st/backend/`
- **Pop-pins2**: `References/Pop-pins2/backend/`
- **LangChain 문서**: https://python.langchain.com/
- **Qdrant 문서**: https://qdrant.tech/documentation/
- **Gemini API**: https://ai.google.dev/

---

**작성일**: 2025-01-XX  
**최종 업데이트**: 2025-11-22  
**버전**: 1.4.2

