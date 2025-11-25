# PopPins II - Product Requirement Document (PRD)

**프로젝트**: PopPins II (어딧세이 가제)  
**문서 타입**: Product Requirement Document  
**버전**: 1.4.2  
**작성일**: 2025-11-22  
**작성자**: 이진걸  
**최종 업데이트**: 2025-11-22

---

## 1. Product Overview

### 1.1 제품 목적

PopPins II는 **AI 기반 PBL (Problem-Based Learning) 생성 플랫폼**입니다. Google Gemini 2.5 Flash와 RAG(Retrieval-Augmented Generation) 기술을 활용하여, 파이썬 PDF 문서를 기반으로 문서 신뢰성을 확보한 자습형 PBL 학습지를 자동 생성합니다.

**핵심 가치**:
- 전문 콘텐츠(PDF)를 벡터 DB에 저장해 AI hallucination 방지
- LMS에 부착 가능한 PBL 모듈로 설계
- 교육 접근성 제고 및 학습 격차 해소

### 1.2 스코프 정렬 (멘토 피드백 반영)

**변경 사항**:
- ❌ LMS 전체 아키텍처 개발
- ✅ LMS 내 PBL 모듈만 개발
- ✅ 컨텐츠 신뢰도 확보 (PDF 벡터 DB)
- ✅ MVP 기능에 집중

### 1.3 핵심 기능 요약

1. **학습 주제 입력** → AI와 대화로 구체화
2. **AI 기반 PBL 생성** → RAG로 교재 기반 학습 자료 생성
3. **4가지 AI 생성기** → 커리큘럼, 개념, 실습, 퀴즈
4. **결과 출력** → JSON/Markdown 형식

---

## 🔑 주요 의사결정 (회의록 기반)

### MVP 개발 우선순위 (2025-11-08 회의)

**우선도 (내림차순)**:
1. **강의 생성** (Course Generation) - ✅ 완료
2. **챕터 생성** (Chapter Generation) - ✅ 완료
3. **개념 생성** (Concept Generation) - ✅ 완료
4. **문제 생성** (Problem Generation) - ✅ 완료
5. **퀴즈 생성 및 채점** (Quiz Generation & Grading) - ✅ 완료
6. **챕터 다운로드** (Chapter Download) - ✅ 완료
7. **캐싱 시스템** (In-Memory Caching) - ✅ 완료
8. **회원가입** (User Registration) - ⏳ 계획

### 멘토링 피드백 반영 (2025-11-17 ~ 11-19)

**핵심 결정사항**:
- **범위 축소**: LMS 전체 → PBL 모듈만 개발
- **컨텐츠 전략**: 전문 PDF 자료를 벡터 DB에 저장하여 신뢰성 확보
- **피드백 루프 도입**: 
  - 기간별/영역별 진도율
  - 평가 성적
  - 사용시간 (페이지뷰, 방문수)
  - 사용자 설문/의견
- **오픈소스 LMS 활용 검토**: Moodle 등을 활용한 코딩 공수 절감 방안

### 기술 스택 결정 (2025-11-08 회의)

| 구성 요소 | 선택 기술 | 상태 |
|----------|----------|------|
| Frontend | React 19 + TypeScript + Vite | ✅ 완료 |
| Backend | FastAPI | ✅ 완료 |
| Database | In-Memory Cache | ✅ 완료 |
| AI | Google Gemini 2.5 Flash | ✅ 완료 |
| Vector DB | FAISS (python_textbook_gemini_db) | ✅ 완료 |
| Embedding | text-embedding-004 | ✅ 완료 |

### RAG 구현 결정 (2025-11-18 회의)

**핵심 사항**:
- 파이썬 전문 PDF 자료 수집 및 벡터화
- FAISS 벡터 DB 로컬 저장 (`python_textbook_gemini_db`) - Git에 포함
- Top-K=3 Similarity Search
- Gemini text-embedding-004 모델 사용

---


## 2. Target Users

### 🎯 Primary User

**파이썬 초~중급 학습자**
- 함수/반복문은 이해함
- 클래스/Node/LinkedList를 배우고 싶어함
- 예: "class는 어렴풋, Node/LinkedList 구현이 목표"

### 🎯 Secondary Users

1. **대학생** (23세, 비전공자)
   - 짧은 시간 내 핵심 개념 학습 필요
   - 비전공자도 이해 가능한 설명 원함

2. **직장인** (31세, 리스킬링)
   - 팀 단위 학습 자료 필요
   - 실무 적용 가능한 실습 중심 콘텐츠

3. **교사** (35세, 방과후 담당)
   - 한 학기 분량 커리큘럼 필요
   - 한국어 실습형 교육 자료

---

## 3. User Scenarios

### 시나리오 A: "LinkedList를 2시간 안에 이해하고 싶어요"

**사용자 입력**:
```
"단순 연결 리스트를 자습으로 배우고 싶어요."
```

**시스템 처리**:
1. PDF에서 LinkedList 관련 단락 Top-K 검색 (k=3)
2. 학습자 레벨 반영 (초급)
3. PBL 미션 생성 (Day1~Day5 기반 미니 버전)
   - 개념 → 실습 → 순회 → 삽입/삭제 → 원형리스트

**출력**:
- 개념 요약 (1000~1200자)
- PDF 기반 인용
- 예제 코드
- 미니 PBL 세트 (3~5개 미션)
- 퀴즈 3개

### 시나리오 B: "람다 함수 핵심 요약 + 작은 실습 문제 줘"

**처리 흐름**:
1. 사용자 질문 → RAG 검색
2. LLM이 PDF 근거 기반으로 정확한 설명 생성
3. 1~2개 실습(PBL) 출력

---

## 4. Functional Requirements

### 4.1 핵심 기능 (MVP)

#### FR-1: 학습 주제 입력 및 구체화 ✅

**설명**: 사용자가 학습 주제를 입력하고, 시스템이 이를 처리

**입력**:
- `topic` (string, 필수): 학습 주제 (예: "파이썬 리스트")
- `difficulty` (string, 선택): 난이도 (초급/중급/고급, 기본값: 중급)
- `max_chapters` (integer, 선택): 최대 챕터 수 (기본값: 3)
- `course_description` (string, 선택): 강의 설명

**출력**:
- 구체화된 학습 목표 및 범위
- Course ID 생성
- 챕터 리스트

**구현 상태**: ✅ 완료 (`main_with_RAG.py` - `generate_course()`)

#### FR-2: RAG 기반 콘텐츠 검색 ✅

**설명**: PDF 문서를 벡터 DB에 저장하고, 관련 콘텐츠 검색

**구성**:
1. **PDF Loader**: PyPDFLoader로 PDF 텍스트 추출
2. **Chunking**: RecursiveCharacterTextSplitter (chunk_size=1000, overlap=200)
3. **Embedding**: GoogleGenerativeAIEmbeddings (text-embedding-004)
4. **Vector Store**: FAISS 벡터 DB
5. **Retriever**: Similarity Search (k=3)

**구현 상태**: ✅ 완료 (`main_with_RAG.py` - `search_rag_context()`)

#### FR-3: AI 기반 PBL 생성 ✅

**설명**: 4가지 AI 생성기로 학습 자료 생성

**3.1 CourseMaker** ✅
- **입력**: topic, difficulty, max_chapters
- **출력**: Course (id + chapters)
- **프롬프트**: 커리큘럼 설계 전문가 역할
- **RAG 적용**: ✅ (커리큘럼 구조 참고)

**3.2 ConceptMaker** ✅
- **입력**: course_title, chapter_title, chapter_description
- **출력**: Concept (title + description + contents)
- **분량**: 1000~1200자
- **형식**: Markdown
- **RAG 적용**: ✅ (교재 내용 참고)

**3.3 ExerciseMaker** ✅
- **입력**: course_title, chapter_title, chapter_description
- **출력**: Exercise (title + description + contents)
- **미션 수**: 3개 (기본 → 응용 → 확장)
- **RAG 적용**: ✅ (예제 문제 참고)

**3.4 QuizMaker** ✅
- **입력**: course_title, chapter_title, course_prompt
- **출력**: Quiz (quizes: List[QuizItem])
- **문제 수**: 3개 (주관식)
- **RAG 적용**: ✅ (핵심 개념 기반)

**구현 상태**: ✅ 완료 (`main_with_RAG.py`)

#### FR-4: REST API 제공 ✅

**엔드포인트**:

**POST /generate-study-material**
- 학습 주제 입력 → 자습 과제 생성
- Request: StudyTopicRequest
- Response: StudyMaterialResponse (course + chapters)
- 상태: ✅ 구현 완료

**GET /**
- API 정보 반환
- 상태: ✅ 구현 완료

**GET /health**
- 서버 상태 확인
- 상태: ✅ 구현 완료

**구현 상태**: ✅ 완료

### 4.2 확장 기능 (Post-MVP)

#### FR-5: Frontend 웹 앱 🔄

**설명**: React + Vite 기반 웹 인터페이스

**컴포넌트**:
- TopicForm: 주제 입력 폼
- CourseViewer: 커리큘럼 표시
- ConceptViewer: 개념 정리 표시
- ExerciseViewer: 실습 과제 표시
- QuizViewer: 퀴즈 표시
- LoadingSpinner: 로딩 표시

**구현 상태**: 🔄 예정

#### FR-6: 학습 관리 및 피드백 🔄

**설명**: 학습 기록 저장 및 분석

**기능**:
- 활동 로그 저장
- 질문/응답 히스토리
- PBL 수행 여부 추적
- 난이도 조정 모델

**구현 상태**: 🔄 설계 단계

#### FR-7: 캐싱 전략 🔄

**설명**: 동일 주제 재요청 시 캐시 활용

**기능**:
- "Generate Again" 버튼
- 과거 생성 학습 자료 불러오기

**구현 상태**: 🔄 예정

---

## 5. Technical Requirements

### 5.1 Backend (FastAPI) ✅

**프레임워크**: FastAPI 0.104.0+

**의존성**:
```python
fastapi
uvicorn
pydantic
google-generativeai
python-dotenv
langchain
langchain-community
langchain-google-genai
faiss-cpu
```

**API 구조**:
- RESTful API
- JSON 요청/응답
- CORS 설정 (모든 origin 허용)
- HTTPException 에러 처리

**구현 상태**: ✅ 완료

### 5.2 AI Engine (Gemini) ✅

**모델**: Gemini 2.5 Flash

**설정**:
- Temperature: 0.7
- Max Output Tokens: 2048~8192
- Response Format: JSON/Markdown

**임베딩 모델**: text-embedding-004

**구현 상태**: ✅ 완료

### 5.3 Vector Database (FAISS) ✅

**DB**: FAISS (Facebook AI Similarity Search)

**설정**:
- Embedding 차원: 768
- Chunk Size: 1000자
- Chunk Overlap: 200자
- Top-K 검색: 3

**메타데이터**:
- file_name: 파일명
- source_file: 파일 경로
- page: 페이지 번호

**구현 상태**: ✅ 완료

### 5.4 Frontend (React + Vite) 🔄

**프레임워크**: React 18+ + Vite

**UI 라이브러리**: TailwindCSS (선택적)

**주요 페이지**:
- 홈 페이지: 주제 입력
- 결과 페이지: 학습 자료 표시

**구현 상태**: 🔄 예정

---

## 6. Non-Functional Requirements

### NFR-1: 성능 (Performance)

**요구사항**:
- 학습지 생성 시간: 1분 이내
- 챕터당 생성 시간: 10-30초
- RAG 검색 시간: 0.1-0.5초

**현재 성능**: ✅ 요구사항 충족

### NFR-2: 안정성 (Reliability)

**요구사항**:
- 고의적 입력 오류에도 크래시 없이 응답
- JSON 파싱 실패 시 재시도

**구현**:
- HTTPException 처리
- JSON 파싱 헬퍼 함수 (`clean_json_response()`)
- 정규식 기반 fallback 파싱

**현재 상태**: ✅ 구현 완료

### NFR-3: 정확성 (Accuracy)

**요구사항**:
- PDF 문서 기반 정확한 내용 생성
- AI 환각 최소화
- 문서 근거 포함 응답률: 90% 이상

**구현**:
- RAG로 PDF 컨텍스트 강제 포함
- 프롬프트에 "문서 기반" 명시

**현재 상태**: ✅ 구현 완료

### NFR-4: 확장성 (Scalability)

**요구사항**:
- 다양한 PDF 교재 지원
- 다국어 확장 가능
- 다른 LLM 통합 가능

**현재 상태**: 🔄 향후 확장

### NFR-5: 보안 (Security)

**요구사항**:
- API 키 환경 변수 관리
- 사용자 입력 검증

**구현**:
- `.env` 파일로 API 키 관리
- Pydantic으로 입력 검증

**현재 상태**: ✅ 구현 완료

### NFR-6: 유지보수성 (Maintainability)

**요구사항**:
- 모듈화된 코드 구조
- API 문서화
- 에러 로깅

**구현**:
- 함수별 역할 분리
- Swagger UI 자동 생성
- FastAPI 로깅

**현재 상태**: ✅ 구현 완료

---

## 7. System Architecture

### 7.1 전체 구조

```
┌─────────────────────┐
│   Frontend (예정)   │
│   React + Vite      │
└──────────┬──────────┘
           │ HTTP
┌──────────▼──────────┐
│   FastAPI Backend   │
│  - /generate-...    │
│  - /health          │
└─────┬─────────┬─────┘
      │         │
      ▼         ▼
┌────────┐  ┌──────────┐
│  RAG   │  │ Gemini   │
│ Engine │  │ 2.5      │
│ (FAISS)│  │ Flash    │
└────────┘  └──────────┘
```

### 7.2 데이터 흐름

```
사용자 입력 (주제)
    ↓
1. CourseMaker
   - RAG 검색 (커리큘럼 참고)
   - Gemini로 챕터 리스트 생성
    ↓
2. ConceptMaker (각 챕터별)
   - RAG 검색 (개념 설명 참고)
   - Gemini로 개념 정리 생성 (1000~1200자)
    ↓
3. ExerciseMaker (각 챕터별)
   - RAG 검색 (실습 예제 참고)
   - Gemini로 실습 3개 생성
    ↓
4. QuizMaker (각 챕터별)
   - RAG 검색 (핵심 개념 참고)
   - Gemini로 퀴즈 3개 생성
    ↓
JSON 응답 반환
```

---

## 8. Data Models

### 8.1 Request Models

**StudyTopicRequest**:
```python
{
    "topic": str,               # 필수
    "difficulty": str,          # 선택, 기본값: "중급"
    "max_chapters": int,        # 선택, 기본값: 3
    "course_description": str   # 선택
}
```

### 8.2 Response Models

**StudyMaterialResponse**:
```python
{
    "course": Course,
    "chapters": List[ChapterContent]
}
```

**Course**:
```python
{
    "id": int,
    "chapters": List[Chapter]
}
```

**Chapter**:
```python
{
    "chapterId": int,
    "chapterTitle": str,
    "chapterDescription": str
}
```

**ChapterContent**:
```python
{
    "chapter": Chapter,
    "concept": ConceptResponse,
    "exercise": ExerciseResponse,
    "quiz": QuizResponse
}
```

**ConceptResponse**:
```python
{
    "title": str,
    "description": str,
    "contents": str  # Markdown 형식
}
```

**ExerciseResponse**:
```python
{
    "title": str,
    "description": str,
    "contents": str  # Markdown 형식, 3개 문제
}
```

**QuizResponse**:
```python
{
    "quizes": List[QuizItem]
}
```

**QuizItem**:
```python
{
    "quiz": str  # 주관식 문제
}
```

---

## 9. Success Metrics

### 9.1 기술적 지표

| 지표 | 목표 | 현재 상태 |
|------|------|----------|
| 학습지 생성 시간 | 1분 이내 | ✅ 달성 |
| RAG 정확도 | 90% 이상 | ✅ 달성 |
| 시스템 안정성 | 크래시 0건 | ✅ 달성 |
| JSON 출력 성공률 | 95% 이상 | ✅ 달성 |

### 9.2 사용자 경험 지표

| 지표 | 목표 | 현재 상태 |
|------|------|----------|
| 페르소나 시나리오 만족 | 3/3 | ✅ 달성 (Backend) |
| UI 직관성 | 5점 만점 4점 이상 | 🔄 Frontend 예정 |
| 학습 진도 추적 | 가능 | 🔄 향후 확장 |

### 9.3 비즈니스 지표

| 지표 | 목표 | 현재 상태 |
|------|------|----------|
| MVP 프로토타입 완성 | ✅ | ✅ Backend 완료 |
| 발표 시연 성공 | ✅ | 🔄 Frontend 개발 중 |
| 심사 기준 달성 | 4/4 | 🔄 진행 중 |

---

## 10. Risk & Mitigation

| Risk | Impact | Mitigation | 상태 |
|------|--------|------------|------|
| AI 응답 품질 저하 | 높음 | RAG + Prompt 최적화 | ✅ 완료 |
| PDF 품질 저하 | 중간 | pdfminer fallback | ✅ 구현 |
| LLM 환각 | 높음 | RAG 강제 + 문서 인용 | ✅ 구현 |
| 일정 지연 | 중간 | MVP 집중 + 우선순위 | ✅ Backend 완료 |
| API 비용 초과 | 낮음 | 캐싱 + 효율적 호출 | 🔄 모니터링 |
| Frontend 미완성 | 중간 | 백엔드 API 우선 완성 | 🔄 진행 중 |

---

## 11. Development Timeline

### Phase 1: 전단계 (~ 11/9) ✅
- 역할 분담
- API 설계
- RAG 연구

### Phase 2: 개발 (11/10 ~ 11/23) ✅
- **완료 항목**:
  - ✅ FastAPI Backend 구현
  - ✅ RAG 벡터 DB 통합
  - ✅ 4가지 AI 생성기 구현
  - ✅ API 문서 작성
  - ✅ Prompt 최적화

### Phase 3: 통합 및 발표 (11/24 ~ 11/28) 🔄
- **진행 중**:
  - 🔄 Frontend 개발
  - 🔄 UI/UX 디자인
  - 🔄 시연 준비
  - 🔄 발표 리허설

---

## 12. MVP Scope

### ✅ Included (완료)

1. PDF → FAISS 인덱싱
2. RAG 검색 구현
3. Gemini 통합
4. 4가지 AI 생성기
5. FastAPI 엔드포인트
6. API 문서화

### 🔄 In Progress (진행 중)

1. Frontend 웹 앱
2. UI/UX 디자인
3. 시연 데모

### ⏳ Future (향후)

1. 사용자 인증
2. 학습 히스토리 DB
3. 캐싱 시스템
4. 다국어 지원
5. 모바일 앱

---

## 13. References

- [API Reference](../app/API_REFERENCE.md)
- [RAG Integration Guide](../app/RAG_INTEGRATION_GUIDE.md)
- [통합 기획 문서](./pop_pins_ii_planning_document.md)
- [원본 PRD](./prd.md)
- [구현 예상 형태](./yesang.md)

---

## 14. Appendix

### A. Environment Variables

```env
# Required
GEMINI_API_KEY=your-gemini-api-key

# Optional (RAG)
VECTOR_DB_PATH=../vector_db/python_textbook_gemini_db
VECTOR_DB_EMBEDDING_MODEL=gemini
USE_RAG=true
```

### B. API Testing

**cURL Example**:
```bash
curl -X POST "http://localhost:8001/generate-study-material" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "파이썬 리스트",
    "difficulty": "초급",
    "max_chapters": 2
  }'
```

---

**문서 버전**: 1.4.2  
**최종 수정일**: 2025-11-22  
**승인자**: 이진걸  
**상태**: Backend MVP 완료, Frontend 개발 진행 중  
**다음 마일스톤**: Frontend 웹 앱 완성 (11/28)
