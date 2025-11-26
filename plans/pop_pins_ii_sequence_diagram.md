# PopPins II - Sequence Diagram

**프로젝트**: PopPins II  
**문서 타입**: System Sequence Diagrams  
**버전**: 1.9.0  
**작성일**: 2025-11-22  
**작성자**: 이진걸  
**최종 업데이트**: 2025-11-26

---

## 1. 전체 시스템 플로우

### 1.1 학습 자료 생성 플로우 (Adaptive Learning)

```mermaid
sequenceDiagram
    actor User as 👤 사용자
    participant UI as 🖥️ Frontend
    participant API as ⚙️ Backend
    participant RAG as 📚 RAG Engine
    participant AI as 🤖 Gemini
    
    User->>UI: 주제 입력 (예: "Pandas")
    UI->>API: POST /generate-objectives
    API->>AI: 학습 목표 3가지 생성 요청
    AI-->>API: Objectives JSON
    API-->>UI: ObjectivesResponse
    
    User->>UI: 목표 선택 (예: "실무 중심")
    UI->>API: POST /generate-course (selected_objective)
    
    API->>RAG: PDF 검색 (Top-3)
    RAG-->>API: 관련 문서
    API->>AI: 커리큘럼 생성 (목표 반영)
    AI-->>API: Course + Chapters
    
    loop 챕터별 (Lazy Loading)
        API->>RAG: 챕터 문서 검색
        RAG-->>API: 문서
        API->>AI: 개념/실습/퀴즈 생성
        AI-->>API: Content
    end
    
    API-->>UI: JSON 응답
    UI->>User: 결과 표시
```

---

## 2. 세부 플로우

### 2.1 RAG 문서 검색

```mermaid
sequenceDiagram
    participant API
    participant RAG as RAG Engine
    participant FAISS as FAISS DB
    participant Embed as Embedding
    
    API->>RAG: search_rag_context("파이썬 리스트", k=3)
    RAG->>Embed: 쿼리 임베딩
    Embed-->>RAG: Vector
    RAG->>FAISS: similarity_search(Vector, k=3)
    FAISS-->>RAG: Top-3 Documents
    RAG->>RAG: 컨텍스트 포맷팅
    RAG-->>API: "참고 자료 1: ...\n참고 자료 2: ..."
```

### 2.2 AI 콘텐츠 생성

```mermaid
sequenceDiagram
    participant API
    participant AI as Gemini AI
    
    API->>AI: generate_concept(query + RAG context)
    Note over AI: Prompt:<br/>1. RAG 컨텍스트<br/>2. 학습자 레벨<br/>3. 출력 형식
    AI->>AI: 개념 정리 생성 (1000~1200자)
    AI-->>API: JSON (title, description, contents)
    
    API->>AI: generate_exercise(query + RAG context)
    AI->>AI: 실습 3개 생성
    AI-->>API: JSON (title, description, contents)
    
    API->>AI: generate_quiz(query + RAG context)
    AI->>AI: 퀴즈 3개 생성
    AI-->>API: JSON (quizes: [...])
```

---

## 3. 사용자 시나리오별 플로우

### 3.1 적응형 학습 (수진의 사례)

```mermaid
sequenceDiagram
    actor 수진
    participant System
    
    수진->>System: "확률과 통계 기초" 입력
    System->>수진: 3가지 목표 제안 (기초/실무/심화)
    수진->>System: "기초 개념 위주" 선택
    
    System->>수진: 맞춤형 커리큘럼 생성
    
    Note over 수진,System: 챕터 1 학습
    수진->>System: 개념 읽기 & 실습
    수진->>System: 피드백 제출 (별점 5, "설명 굿")
    System->>System: 피드백 저장 (DB)
    
    Note over 수진,System: 챕터 2 학습
    수진->>System: 다음 챕터 진행
```

### 3.2 팀 학습 (민수의 사례)

```mermaid
sequenceDiagram
    actor 민수
    participant System
    actor 팀원
    
    민수->>System: "Delphi 기초" 입력
    System->>민수: 목표 제안 -> "실무 프로젝트 중심" 선택
    System->>민수: 커리큘럼 생성
    
    민수->>팀원: 학습 자료 공유
    
    par 병렬 학습
        팀원->>System: 챕터 1-2 학습
    and
        민수->>System: 챕터 3-5 학습
    end
```

---

## 4. 에러 처리 플로우

### 4.1 생성 실패 처리 (Retry Logic)

```mermaid
sequenceDiagram
    actor User
    participant UI
    participant API
    participant AI
    
    User->>UI: 주제 입력
    UI->>API: POST /generate-objectives
    
    loop Retry (Max 3 times)
        API->>AI: generate_content()
        alt AI 응답 실패 / JSON 에러
            AI-->>API: Exception
            API->>API: Wait 1s
        else 성공
            AI-->>API: Valid JSON
            break
        end
    end
    
    alt 최종 실패
        API-->>UI: 500 Error
        UI->>User: "일시적인 오류입니다. 다시 시도해주세요."
    else 성공
        API-->>UI: 정상 응답
    end
```

---

## 5. 데이터 플로우

### 5.1 PDF → 벡터 DB

```mermaid
graph LR
    A[PDF 파일] --> B[PyPDFLoader]
    B --> C[텍스트 추출]
    C --> D[RecursiveTextSplitter]
    D --> E[Chunks<br/>1000자×200 overlap]
    E --> F[Gemini Embedding<br/>text-embedding-004]
    F --> G[FAISS 벡터 DB]
    G --> H[메타데이터<br/>file_name, source]
```

### 5.2 사용자 입력 → 학습 자료

```mermaid
graph TD
    A[사용자 입력] --> B{파싱}
    B --> C[topic]
    B --> D[selected_objective]
    
    C --> F[RAG 검색]
    D --> G[Gemini AI]
    F --> G
    
    G --> H[Objectives]
    G --> I[Course]
    G --> J[Chapter Content]
    
    J --> K[JSON 응답]
```

---

## 6. 상태 다이어그램

### 6.1 학습 진행 상태

```mermaid
stateDiagram-v2
    [*] --> 주제입력
    주제입력 --> 목표선택
    목표선택 --> 커리큘럼생성
    커리큘럼생성 --> 챕터학습
    
    챕터학습 --> 개념읽기
    개념읽기 --> 실습풀기
    실습풀기 --> 퀴즈풀기
    퀴즈풀기 --> 피드백제출
    
    피드백제출 --> 다음챕터: 챕터 남음
    피드백제출 --> 학습완료: 모든 챕터 완료
    학습완료 --> [*]
```

---

## 7. 시스템 컨텍스트

```mermaid
C4Context
    title PopPins II System Context
    
    Person(user, "학습자", "파이썬 초~중급")
    System(poppins, "PopPins II", "AI 기반 PBL 생성")
    System_Ext(gemini, "Gemini AI", "LLM & Embedding")
    SystemDb(faiss, "FAISS DB", "벡터 저장소")
    SystemDb(sqlite, "SQLite DB", "히스토리/피드백")
    
    Rel(user, poppins, "학습 주제 입력")
    Rel(poppins, gemini, "콘텐츠 생성 요청")
    Rel(poppins, faiss, "유사 문서 검색")
    Rel(poppins, sqlite, "로그 저장")
```

---

## 📚 참고 문서

- [통합 기획 문서](./pop_pins_ii_planning_document.md)
- [PRD](./pop_pins_ii_prd.md)
- [User Diagram](./pop_pins_ii_user_diagram.md)
- [Wireframe](./pop_pins_ii_wireframe.md)

---

**문서 버전**: 1.5.0  
**최종 수정일**: 2025-11-25  
**작성자**: 이진걸  
**상태**: 작성 완료
