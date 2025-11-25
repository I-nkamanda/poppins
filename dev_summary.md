# Development Summary (dev_summary.md)

## 프로젝트 개요
- **PopPins II**는 AI 기반 PBL(Problem‑Based Learning) 학습 자료를 자동 생성하는 웹 애플리케이션입니다.
- 백엔드는 **FastAPI + Gemini** 를 이용해 커리큘럼, 개념 정리, 실습 과제, 퀴즈를 생성하고, **RAG**(Retrieval‑Augmented Generation) 를 통해 교재 문서를 활용합니다.
- 프론트엔드는 **React 19 + TypeScript + Vite** 로 구현했으며, Tailwind CSS 로 스타일링했습니다.

## 주요 작업 흐름
1. **Lazy‑Loading 구현**
   - `main_with_RAG.py`에 두 개의 새로운 엔드포인트 추가
     - `POST /generate-course` – 커리큘럼(목차)만 빠르게 생성
     - `POST /generate-chapter-content` – 선택된 챕터의 상세 내용(Concept, Exercise, Quiz) 생성
   - 기존 `POST /generate-study-material` 은 호환성을 위해 그대로 유지.
   - 각 엔드포인트에서 `asyncio.gather` 로 개념·실습·퀴즈를 병렬 처리하고, 오류 발생 시 `print(e)` 로 로그 출력.

2. **프론트엔드 API 업데이트 (`src/services/api.ts`)**
   - `generateCourse` 와 `generateChapterContent` 함수 구현.
   - 기존 `generateStudyMaterial` 은 그대로 유지.

3. **UI 리팩터링**
   - **HomePage**: 입력 폼 → `generateCourse` 호출, 난이도 드롭다운 가독성 개선 (`text-gray-900`, `bg-white`).
   - **ResultPage**: 커리큘럼(목차)만 표시, 챕터 클릭 시 `ChapterPage` 로 라우팅.
   - **ChapterPage**: 마운트 시 `generateChapterContent` 호출, 로딩 스피너 표시, 개념·실습·퀴즈 내용 렌더링.

4. **스타일 및 UX 개선**
   - 난이도 선택 박스 텍스트 색상 진하게, 배경 흰색 적용으로 가독성 향상.
   - 로딩 중 스피너와 “생성 중...” 텍스트 추가.

5. **문서·버전 관리**
   - `CHANGELOG.md`에 **v1.3.0**(Lazy‑Loading 추가) 및 기존 버전 기록 업데이트.
   - `dev_summary.md`(현재 파일) 에 전체 작업 흐름과 주요 변경점 요약.
   - `README.md`, `RAG_INTEGRATION_GUIDE.md` 등 문서 최신화.

## 현재 상태 & 다음 단계
- **백엔드**: 새 엔드포인트가 코드에 포함되어 있지만, 현재 실행 중인 uvicorn 프로세스를 재시작해야 적용됩니다.
- **프론트엔드**: `npm run dev` 로 개발 서버 실행 중이며, HomePage → ResultPage → ChapterPage 흐름이 정상 동작합니다(백엔드 재시작 후).
- **테스트**: 404 오류 해결 후 전체 흐름을 검증하고, 필요 시 추가 UI polish 진행.

---

## [v1.6.0] - 2025-11-25 코드 리팩토링

### 주요 변경 사항

1. **서비스 계층 분리 (Refactoring)**
   - `app/services/generator.py`에 `ContentGenerator` 클래스 구현
   - `main_with_RAG.py`의 비즈니스 로직을 서비스 모듈로 이동
   - Gemini API 및 RAG 로직을 캡슐화하여 유지보수성 향상

2. **프롬프트 관리 개선**
   - 모든 생성 프롬프트를 `ContentGenerator` 클래스 내에서 통합 관리
   - 향후 프롬프트 버전 관리 및 A/B 테스트 용이성 확보

---

## [v1.5.0] - 2025-11-24 Semantic Chunking 구현

### 주요 변경 사항

1. **Semantic Chunking 도입**
   - 기존 고정 크기 청킹을 의미 기반 청킹으로 대체
   - `langchain-experimental` 패키지의 `SemanticChunker` 사용
   - 문서를 의미적 경계에서 분할하여 문맥 보존 향상
   - 평균 5% 검색 정확도 개선 (특정 쿼리에서 최대 12.7%)

2. **메타데이터 강화**
   - 섹션 헤더 자동 추출 기능 추가
   - 청크 메타데이터에 섹션 정보 저장
   - 검색 결과의 문맥 파악 용이성 향상

3. **Checkpointing 시스템**
   - 파일 단위 중간 저장 기능 추가
   - 장시간 실행 중 중단되어도 진행 상황 보존
   - 재실행 시 처리된 파일 자동 건너뛰기

4. **Rate Limiting 개선**
   - `RateLimitedEmbeddings` 래퍼 클래스 구현
   - 모든 임베딩 API 호출에 대한 전역 속도 제한
   - API quota 초과 방지

### 성능 검증

- **3가지 버전 비교 완료**:
  - Legacy (v1.0): Simple Chunking
  - Filtered (v1.4): Page Filtering + Cleaning
  - Semantic (v1.5): Semantic Chunking + Metadata
  
- **벡터 DB 생성**:
  - 총 38개 PDF 파일, 1090개 청크 생성
  - 소요 시간: 약 4시간 (2025-11-24)
  - 위치: `RAG vector generator/vector_db/python_textbook_gemini_db_semantic`

- **애플리케이션 통합**:
  - `main_with_RAG.py`가 Semantic Vector DB 사용하도록 업데이트
  - 환경 변수로 DB 경로 변경 가능

### 문서 업데이트

- `CHANGELOG.md`: v1.5.0 엔트리 추가
- `README.md`: Semantic Chunking 반영
- `RAG_UPDATE_LOG.md`: 상세 업데이트 로그 작성
- `rag_comparison_analysis.md`: 성능 비교 분석 보고서 작성

### 향후 개선 계획

- Query Rewriting 구현 예정
- Reranking 기능 추가 예정 (Cohere API 또는 로컬 모델)
- Hybrid Search 고려 중

---
## [v1.4.0] - 2025-11-22 추가 기능

### 추가된 기능

1. **챕터 캐싱 시스템 (메모리 기반)**
   - DB 없이 메모리 기반 캐싱 구현
   - 한 번 생성된 챕터는 재방문 시 즉시 로드 (재생성 없음)
   - 캐시 키: `(course_title, chapter_title, chapter_description)` 튜플 (공백 정규화)
   - 백엔드 로그에 `📦 캐시에서 로드` 메시지 표시
   - 프론트엔드에서 중복 요청 방지 (이미 로드된 콘텐츠 체크)

2. **챕터 다운로드 기능**
   - 헤더에 "📥 다운로드" 버튼 추가
   - 챕터 전체를 Markdown(.md) 파일로 다운로드
   - 개념, 실습, 퀴즈가 모두 포함된 완전한 문서
   - 백엔드 엔드포인트: `POST /download-chapter`

3. **퀴즈 AI 채점 기능**
   - 각 퀴즈 문제에 "✓ 채점하기" 버튼 추가
   - Gemini AI를 활용한 자동 채점 (0-100점)
   - 상세 피드백 제공:
     - 점수 (0-100)
     - 전체 피드백
     - 잘한 점 (correct_points)
     - 개선할 점 (improvements)
   - "다시 답변하기" 버튼으로 재시도 가능
   - 백엔드 엔드포인트: `POST /grade-quiz`

### 개선 사항

1. **JSON 파싱 에러 수정**
   - 퀴즈 생성 시 `max_output_tokens`를 2048 → 4096으로 증가
   - 퀴즈 채점 시 `max_output_tokens`를 2048 → 4096으로 증가
   - 불완전한 JSON 처리 로직 개선 (잘린 경우 복구 시도)
   - `clean_json_response` 함수 개선
   - 퀴즈 채점 응답에 필수 필드 기본값 설정

2. **안전 필터 처리 개선**
   - Gemini API의 안전 필터 차단 시 자동 재시도
   - 더 안전한 프롬프트로 재시도 로직 추가
   - 각 생성 함수(개념, 실습, 퀴즈, 채점)에 적용
   - 재시도 시 temperature 조정 (0.5 또는 0.2)

3. **에러 처리 및 로깅 강화**
   - 각 생성 단계별 상세 로그 추가 (`📚`, `💻`, `❓` 이모지)
   - `asyncio.gather`에 `return_exceptions=True` 추가로 개별 에러 처리
   - 프론트엔드에서 상세한 에러 메시지 표시
   - 백엔드에서 traceback 출력으로 디버깅 용이

4. **UI/UX 개선**
   - 퀴즈 텍스트 입력 필드 가독성 개선 (`text-gray-900`, `bg-white` 명시)
   - "다시 답변하기" 버튼 스타일 개선 (명확한 버튼 형태)
   - 개념 학습 문장 잘림 문제 해결 (`break-words`, `whitespace-pre-wrap`)
   - 코드 블록 가독성 개선:
     - 배경색: `gray-800` → `gray-900`
     - 테두리 및 그림자 추가
     - 패딩 증가 및 라인 높이 개선
     - 언어 배지 스타일 개선 (우측 상단 배치)

5. **Markdown 렌더링 개선**
   - 코드 블록 커스텀 컴포넌트 구현
   - 언어 지정자("python" 등)를 코드 내부에서 제거하고 배지로 표시
   - 인라인 코드와 블록 코드 구분 처리
   - 문단에 word-break 적용으로 긴 단어 자동 줄바꿈

6. **중복 요청 방지**
   - 프론트엔드 `useEffect` dependency 최적화 (`chapterId`만)
   - 이미 로드된 콘텐츠 체크로 불필요한 요청 방지
   - 로딩 중일 때 추가 요청 차단
   - 백엔드 캐시 키 정규화 (공백 제거)

### 기술적 세부사항

- **캐싱**: Python 딕셔너리 기반 인메모리 캐시 (`chapter_cache`)
- **다운로드**: Blob API를 사용한 클라이언트 사이드 파일 다운로드
- **채점**: Gemini API를 활용한 주관식 답안 평가 (temperature=0.3으로 일관성 확보)
- **Markdown**: react-markdown + remark-gfm 사용, 커스텀 컴포넌트로 코드 블록 처리

---

## [v1.4.1] - 2025-11-22 RAG 벡터 생성기 개선 및 프로젝트 정리

### 변경 사항

1. **RAG 벡터 생성기 경로 수정**
   - 벡터 DB 저장 경로를 `RAG vector generator/vector_db` → `Pop-pins2/vector_db`로 변경
   - 프로젝트 루트의 `vector_db` 폴더에 통합 저장
   - `python_textbook_rag_generator.py`의 `default_output_dir` 수정

2. **문서 업데이트**
   - `README.md`에 RAG 벡터 DB 생성 방법 추가
   - `manual.md`에 "RAG 벡터 DB 생성하기" 섹션 추가 (고급 사용자용)
   - 벡터 DB 생성 단계별 가이드 제공

3. **벡터 DB 정리 및 Git 포함**
   - 사용하지 않는 `python_textbook_db` 제거 (gemini 버전만 유지)
   - 벡터 DB 파일 크기가 100MB 미만이므로 Git에 포함
   - `.gitignore`에서 벡터 DB 무시 규칙 제거

### 기술적 세부사항

- **벡터 DB 경로**: `script_dir.parent / "vector_db"` (Pop-pins2 폴더 기준)
- **기본 DB 이름**: `python_textbook_gemini_db` (Gemini 임베딩 사용 시)
- **메타데이터 관리**: 처리된 파일의 해시값과 메타데이터를 JSON으로 저장하여 중복 처리 방지

---

## [v1.4.2] - 2025-11-22 프로젝트 정리 및 벡터 DB Git 포함

### 변경 사항

1. **불필요한 파일 제거**
   - 사용하지 않는 `python_textbook_db` 벡터 DB 제거 (gemini 버전만 유지)
   - `app/main_with_RAG_openai.py` 제거 (현재 Gemini 사용 중)
   - `app/some.zip` 임시 파일 제거
   - `UNUSED_FILES.md` 정리 문서 제거

2. **벡터 DB Git 포함**
   - 벡터 DB 파일 크기가 100MB 미만이므로 Git 저장소에 포함
   - `.gitignore`에서 벡터 DB 무시 규칙 제거
   - `vector_db/python_textbook_gemini_db/` 폴더 전체를 Git에 포함

3. **문서 업데이트**
   - `README.md` 프로젝트 구조에서 `main.py` 제거 (사용하지 않음)
   - `dev_summary.md`에 정리 작업 기록

### 기술적 세부사항

- **벡터 DB 관리**: Git에 포함하여 클론 시 즉시 사용 가능
- **프로젝트 구조 단순화**: 사용하지 않는 파일 제거로 프로젝트 구조 명확화

---
*이 문서는 개발 진행 상황을 한눈에 파악할 수 있도록 요약했습니다. 필요에 따라 세부 내용은 각 파일 및 커밋 로그를 참고하세요.*

