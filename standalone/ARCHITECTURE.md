# PopPins II Standalone - Architecture

## 개요

PopPins II Standalone은 Tauri 2.x 기반의 완전 독립형 데스크탑 애플리케이션입니다. 이 문서는 Standalone 앱의 전체 아키텍처와 각 컴포넌트의 역할을 상세히 설명합니다.

---

## 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    Tauri Desktop App                        │
│  ┌───────────────────────────────────────────────────────┐ │
│  │           WebView (React Frontend)                    │ │
│  │  - React 19 + TypeScript                             │ │
│  │  - TailwindCSS                                        │ │
│  │  - Vite Build                                         │ │
│  └────────────────┬──────────────────────────────────────┘ │
│                   │ http://localhost:8001                  │
│  ┌────────────────▼──────────────────────────────────────┐ │
│  │           Tauri Core (Rust)                           │ │
│  │  - Window Management                                  │ │
│  │  - Process Lifecycle                                  │ │
│  │  - IPC Communication                                  │ │
│  │  - Backend Process Management                         │ │
│  └────────────────┬──────────────────────────────────────┘ │
└───────────────────┼──────────────────────────────────────────┘
                    │ Spawns & Manages
┌───────────────────▼──────────────────────────────────────────┐
│              Python FastAPI Backend                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  FastAPI Server (Port 8001)                           │ │
│  │  - RESTful API Endpoints                              │ │
│  │  - Content Generation                                 │ │
│  │  - Quiz Grading                                       │ │
│  └──────────┬─────────────────────┬──────────────────────┘ │
│             │                     │                         │
│  ┌──────────▼──────────┐  ┌──────▼──────────────────────┐ │
│  │  RAG Engine         │  │  Database (SQLite)          │ │
│  │  - FAISS VectorDB   │  │  - history.db               │ │
│  │  - Embeddings       │  │  - Course/Chapter Data      │ │
│  └─────────────────────┘  └─────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## 주요 컴포넌트

### 1. Tauri Frontend (React)

**위치**: `standalone/frontend/`

**역할**:
- 사용자 인터페이스 제공
- 백엔드 API와 통신
- 상태 관리 및 라우팅

**주요 구성**:
```
frontend/
├── src/
│   ├── pages/          # 페이지 컴포넌트
│   │   ├── HomePage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── ObjectivesPage.tsx
│   │   ├── ResultPage.tsx
│   │   └── ChapterPage.tsx
│   ├── components/     # 재사용 컴포넌트
│   ├── services/       # API 클라이언트
│   │   └── api.ts      # HTTP 요청 로직
│   └── App.tsx         # 메인 앱
├── dist/              # 빌드 결과물
└── src-tauri/         # Tauri 코어
    ├── src/
    │   └── lib.rs     # Rust 메인 로직
    ├── Cargo.toml     # Rust 의존성
    └── tauri.conf.json # Tauri 설정
```

**주요 기능**:
- 학습 목표 선택 UI
- 코스 생성 및 관리
- 챕터 콘텐츠 표시
- 객관식 퀴즈 (MCQ) UI
- 고급 학습 (주관식) UI
- AI 채점 결과 표시

---

### 2. Tauri Core (Rust)

**위치**: `standalone/frontend/src-tauri/`

**역할**:
- 네이티브 윈도우 관리
- 백엔드 프로세스 실행 및 관리
- 시스템 리소스 접근
- IPC (Inter-Process Communication)

**주요 파일**:
- `lib.rs`: 메인 애플리케이션 로직
- `tauri.conf.json`: 앱 설정 (이름, 아이콘, 권한 등)

**프로세스 생명주기**:
1. **앱 시작**: Tauri 윈도우 생성
2. **백엔드 실행**: Python FastAPI 서버 자동 시작
3. **연결 대기**: 백엔드가 준비될 때까지 대기
4. **UI 로드**: React 앱을 WebView에 로드
5. **종료**: 앱 종료 시 백엔드 프로세스도 함께 종료

---

### 3. FastAPI Backend

**위치**: `standalone/app/`

**역할**:
- RESTful API 제공
- AI 기반 콘텐츠 생성
- RAG 엔진 통합
- 데이터베이스 관리

**주요 파일**:
```
app/
├── main.py                  # FastAPI 메인 앱
├── services/
│   └── generator.py         # 콘텐츠 생성 로직
├── database.py              # DB 설정
├── models.py                # DB 모델
└── requirements.txt         # Python 의존성
```

**API 엔드포인트**:
- `POST /generate-objectives`: 학습 목표 제안
- `POST /generate-course`: 커리큘럼 생성
- `POST /generate-chapter-content`: 챕터 내용 생성
- `POST /grade-quiz`: 주관식 답안 채점
- `POST /feedback`: 피드백 저장
- `GET /courses`: 코스 목록 조회
- `GET /health`: 헬스체크

---

### 4. RAG Vector Database

**위치**: `standalone/vector_db/`

**역할**:
- 파이썬 교재 PDF 임베딩 저장
- 유사도 검색 (Similarity Search)
- 콘텐츠 생성 시 참고 자료 제공

**구조**:
```
vector_db/
└── python_textbook_gemini_db_semantic/
    ├── index.faiss        # FAISS 인덱스 (벡터 DB)
    ├── index.pkl          # 메타데이터
    └── docstore.json      # 문서 저장소
```

**검색 프로세스**:
1. 사용자 쿼리 입력 (예: \"리스트 자료구조\")
2. 쿼리를 임베딩으로 변환
3. FAISS에서 Top-K 유사 문서 검색 (K=3)
4. 검색된 문서를 컨텍스트로 사용
5. Gemini LLM에 전달하여 콘텐츠 생성

---

### 5. SQLite Database

**위치**: `standalone/history.db`

**역할**:
- 코스 및 챕터 데이터 저장
- 퀴즈 결과 저장
- 사용자 피드백 저장
- 학습 이력 추적

**주요 테이블**:
- `courses`: 코스 정보
- `chapters`: 챕터 정보
- `quiz_results`: 퀴즈 채점 결과
- `user_feedback`: 사용자 피드백
- `generation_logs`: 생성 이력

---

## 데이터 흐름

### 코스 생성 플로우

```
1. User Input (Topic, Difficulty)
         ↓
2. Frontend: POST /generate-objectives
         ↓
3. Backend: Generate 3 objectives (Gemini)
         ↓
4. Frontend: User selects objective
         ↓
5. Frontend: POST /generate-course
         ↓
6. Backend: Query RAG (related content)
         ↓
7. Backend: Generate course structure (Gemini)
         ↓
8. Backend: Save to DB (courses, chapters)
         ↓
9. Frontend: Display curriculum
```

### 챕터 콘텐츠 생성 플로우

```
1. User clicks chapter
         ↓
2. Frontend: POST /generate-chapter-content
         ↓
3. Backend: Parallel execution
         ├─→ generate_concept (RAG + Gemini)
         ├─→ generate_exercise (RAG + Gemini)
         ├─→ generate_quiz (MCQ, Gemini)
         └─→ generate_advanced_learning (Subjective, Gemini)
         ↓
4. Backend: Update chapter in DB
         ↓
5. Frontend: Display content in tabs
         - Concept
         - Exercise
         - Quiz (MCQ)
         - Advanced Learning
```

### 객관식 퀴즈 플로우

```
1. User answers 5 MCQ questions
         ↓
2. Frontend: Client-side grading
         ↓
3. Frontend: Display results immediately
         - Score (e.g., 4/5)
         - Explanations for each question
```

### 주관식 채점 플로우

```
1. User writes subjective answer
         ↓
2. Frontend: POST /grade-quiz
         ↓
3. Backend: Query RAG (reference material)
         ↓
4. Backend: Gemini grades answer
         - Score (0-100)
         - Feedback
         - Correct points
         - Improvements
         ↓
5. Backend: Save to quiz_results DB
         ↓
6. Frontend: Display grading results
```

---

## 보안 및 설정

### API 키 관리

- **환경 변수**: `standalone/.env` 파일에 저장
- **첫 실행**: 사용자에게 API 키 입력 요청 (향후 구현 예정)
- **보안**: `.env` 파일은 `.gitignore`에 포함

### 포트 설정

- **백엔드**: 8001 포트 (고정)
- **충돌 방지**: 앱 시작 시 포트 사용 여부 확인

---

## 배포 구조

### 최종 산출물

```
PopPins II.exe
  ├─ Tauri WebView (React)
  ├─ Embedded Python Runtime (선택)
  ├─ Backend Scripts (app/)
  └─ Vector DB (vector_db/)
```

### 실행 파일 크기

- **최소**: ~5MB (Python 별도 설치 필요)
- **권장**: ~50MB (Python 임베디드 포함)

---

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| **Desktop Framework** | Tauri 2.x |
| **Frontend** | React 19, TypeScript, Vite |
| **Styling** | TailwindCSS |
| **Backend** | FastAPI (Python 3.8+) |
| **AI Model** | Google Gemini 2.5 Flash |
| **Vector DB** | FAISS |
| **Embedding** | text-embedding-004 |
| **Database** | SQLite |

---

## 성능 최적화

### 1. Lazy Loading
- 챕터 콘텐츠는 사용자가 클릭할 때만 생성
- 초기 로딩 시간 단축

### 2. Caching
- 생성된 챕터는 DB에 저장
- 재방문 시 즉시 로드

### 3. Parallel Generation
- 개념, 실습, 퀴즈를 병렬로 생성
- 전체 생성 시간 ~50% 단축

---

## 확장성

### 다국어 지원
- 프롬프트 다국어화
- UI 언어 설정

### 오프라인 모드
- 로컬 LLM 통합 (예: Ollama)
- 캐시된 콘텐츠 활용

### 플러그인 시스템
- 커스텀 교재 추가
- 새로운 콘텐츠 타입 지원

---

**버전**: v2.1.0  
**최종 업데이트**: 2025-11-28
