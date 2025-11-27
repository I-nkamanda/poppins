## [1.10.0] - 2025-11-27

### 기능 추가 (Feature)
- **SCORM 1.2 모범 답안**: 심화 학습(주관식 퀴즈)에 AI 생성 모범 답안 포함
  - `QuizItem` 모델에 `model_answer` 필드 추가
  - AI가 각 심화 문제에 대해 200-300단어 분량의 모범 답안 생성
  - SCORM `advanced.html`에서 "📖 모범 답안 확인하기" 드롭다운으로 표시
  - 학습자가 스스로 답변 후 모범 답안과 비교 가능
- **콘텐츠 재생성 버튼**: 생성 실패 시 강제 재생성 기능
  - `ChapterRequest`에 `force_refresh` 파라미터 추가
  - 개념/실습 탭에서 에러 발생 시 "🔄 콘텐츠 재생성" 버튼 표시
  - 캐시를 무시하고 AI에게 다시 생성 요청 가능

### 버그 수정 (Bug Fix)
- **에러 응답 캐싱 방지**: 생성 실패 시 에러 응답이 캐시에 저장되지 않도록 수정
- **AdvancedLearningResponse 검증 오류**: 에러 처리 시 올바른 Pydantic 모델 구조 반환
- **SCORM 심화 학습 누락**: `download-chapter-scorm` 엔드포인트에서 `advanced_learning` 데이터 누락 수정
- **Markdown 다운로드 개선**: 챕터 번호를 포함한 파일명 생성 (예: `1_챕터제목.md`)

### 개선 (Enhancement)
- **에러 처리 강화**: `generate_chapter_content_only`에서 개별 생성 태스크 실패 시 부분 성공 가능
- **로깅 개선**: 각 생성 단계별 자세한 로그 출력
- **타입 안정성**: Frontend TypeScript 타입에 `model_answer` 추가

## [1.9.0] - 2025-11-26

### 기능 추가 (Feature)
- **대시보드 (Dashboard)**:
  - `GET /`: 최근 학습한 코스 목록을 보여주는 대시보드 페이지 추가.
  - `/courses/new`: 새로운 코스 생성 페이지 분리.
- **데이터 영속성 (Persistence)**:
  - `Course` 및 `Chapter` 모델 추가 (SQLite).
  - 생성된 모든 코스와 챕터 콘텐츠가 DB에 저장되어 재방문 시 유지됨.
- **라우팅 개선**:
  - `/courses/:id`: 특정 코스로 직접 접근 가능.
  - `/courses/:courseId/chapters/:chapterId`: 챕터별 고유 URL 제공.

## [1.8.0] - 2025-11-25

### 기능 추가 (Feature)
- **적응형 학습 시스템 (Adaptive Learning)**: 사용자의 퀴즈 성적과 피드백을 기반으로 다음 콘텐츠를 개인화하여 생성.
- **피드백 루프 (Feedback Loop)**:
  - `POST /feedback`: 챕터별 사용자 평점(1-5) 및 코멘트 저장.
  - `QuizResult`: 퀴즈 점수 및 취약점 분석 결과 저장.
- **컨텍스트 주입**: `ContentGenerator`가 이전 학습 이력을 조회하여 프롬프트에 반영 (`[User Learning Context]`).
- **학습 목표 제안 (Learning Objectives)**:
  - `POST /generate-objectives`: 주제에 대해 3가지 다른 학습 방향(기초, 실무, 심화)을 제안.
  - `POST /generate-course`: 선택된 학습 목표를 반영하여 맞춤형 커리큘럼 생성.

## [1.7.0] - 2025-11-25

### 기능 추가 (Feature)
- **생성 이력 관리 (History)**: SQLite 데이터베이스를 도입하여 모든 콘텐츠 생성 요청과 결과를 저장.
- **API 엔드포인트 추가**:
  - `GET /history`: 생성 이력 목록 조회.
  - `GET /history/{log_id}`: 특정 이력의 상세 내용(프롬프트, 결과 JSON) 조회.
- **데이터베이스 연동**: SQLAlchemy를 사용한 ORM 기반 DB 구조 설계 (`GenerationLog` 모델).

## [1.6.0] - 2025-11-25

### 리팩토링 (Refactoring)
- **서비스 계층 분리**: `app/services/generator.py`에 `ContentGenerator` 클래스 구현.
- **모듈화**: `main.py`의 비즈니스 로직을 서비스 모듈로 이동하여 코드 구조 개선.
- **유지보수성 향상**: API 엔드포인트와 비즈니스 로직의 분리로 향후 기능 확장(DB 연동, 피드백 루프 등) 용이.
- **프롬프트 관리**: 모든 생성 프롬프트를 `ContentGenerator` 클래스 내에서 통합 관리.

## [1.5.1] - 2025-11-25

### 주요 개선 사항
- `sanitize_markdown` 함수 추가로 코드 블록 보존.
- 응답 모델 복구 및 확장 (`ConceptResponse`, `ExerciseResponse`, `QuizResponse`, `DownloadResponse`).
- 다운로드 엔드포인트 파일명 정규화 및 `.md` 확장자 보장.
- 프론트엔드 다운로드 로직에서 Data URL 사용.
- JSON 파싱 로직 강화 및 오류 처리 개선.

## [1.5.0] - 2025-11-24

### 주요 기능 추가
- **Semantic Chunking 도입**: 의미 기반 문서 분할로 RAG 검색 정확도 향상
  - `langchain-experimental` 패키지 추가
  - `SemanticChunker`를 사용한 의미 기반 청크 분할 
  - 섹션 헤더 메타데이터 자동 추출 및 저장
  
### RAG Vector DB 개선
- **3가지 Vector DB 버전 비교 완료**:
  - Legacy (v1.0): Simple Chunking
  - Filtered (v1.4): Page Filtering + Cleaning
  - Semantic (v1.5): Semantic Chunking + Metadata
- **성능 개선 검증**:
  - 평균 5% 유사도 개선 (특정 쿼리에서 최대 12.7%)
  - "딥러닝 과적합 방지" 쿼리에서 의미적으로 더 정확한 문서 검색 확인
- **Checkpointing 기능 추가**: 파일 단위 중간 저장으로 안정성 향상

### 적용
- `main.py`가 Semantic Vector DB (`python_textbook_gemini_db_semantic`) 사용하도록 업데이트
- 총 38개 PDF 파일, 1090개 청크 생성 (2025-11-24)

### 문서
- 상세 비교 분석 보고서 작성
- 향후 RAG 개선 방안 문서화 (Query Rewriting, Reranking)

## [1.4.0] - 2025-11-23

### 개선
- RAG 벡터 DB 생성기 성능 개선 (`python_textbook_rag_generator.py`)
- **Rate Limiting 기능 추가**: `--rpm-limit` 옵션으로 분당 API 요청 수 제한 (기본값: 1000)
- **Batch Processing 추가**: `--batch-size` 옵션으로 청크 배치 처리 (기본값: 100)
- PDF 페이지 필터링 로직 추가 (목차, 색인, 저작권 페이지 등 제외)
- 텍스트 클리닝 로직 추가 (헤더/푸터 제거, 공백 정리)
- 벡터 DB 재생성 및 검증 스크립트 추가

### 검증 완료
- ✅ 38개 PDF 파일로 벡터 DB 성공적으로 생성 (2025-11-23)
- ✅ 총 25,872개 청크 생성, 약 50분 소요
- ✅ Rate limiting으로 API quota 제한 없이 완료
- ✅ 기술적 쿼리(예외 처리, 파일 입출력, 반복문)에 대한 검색 품질 향상 확인


## [1.3.0] - 2025-11-22

### 추가
- Lazy‑Loading을 위한 새로운 백엔드 엔드포인트 `/generate-course`와 `/generate-chapter-content` 추가
- 프론트엔드 API(`src/services/api.ts`)에 `generateCourse`와 `generateChapterContent` 함수 구현
- `HomePage`에서 커리큘럼만 먼저 생성하도록 로직 변경 및 난이도 선택 박스 가독성 개선
- `ResultPage`에서 커리큘럼(목차) 표시 및 챕터 클릭 시 `ChapterPage` 로 라우팅 구현
- `ChapterPage`에서 선택된 챕터의 상세 내용(개념·실습·퀴즈) 로드 및 로딩 스피너 표시
- `dev_summary.md` 파일 추가 (작업 요약)

### 개선
- 초기 페이지 로드 시간 단축 및 API 요청 페이로드 감소
- 오류 로그 출력 강화 (`print(e)` 로 서버 콘솔에 상세 오류 기록)
- CORS 설정 유지, `/health` 엔드포인트 확인 가능

### 버그 수정
- `generateCourse` 호출 시 404 오류 방지를 위해 백엔드 재시작 안내 추가

## [1.2.0] - 2025-11-22

### 변경
- Gemini 임베딩 모델을 `models/embedding-001`에서 `models/text-embedding-004`로 업데이트
- 벡터 DB 경로를 `python_textbook_gemini_db`로 변경 (성능 향상 및 최신 모델 사용)
- `.env` 파일에 RAG 관련 설정 명시적 추가
- 디렉토리 구조 단순화 (`../vector_db/python_textbook_gemini_db`)

### 개선
- 더 정확한 한국어 및 코드 이해도 (text-embedding-004 모델)
- 속도 제한 (Rate Limiting) 기능 추가로 안정적인 벡터 DB 생성
- 문서화 업데이트 (README.md, RAG_INTEGRATION_GUIDE.md)

## [1.1.0] - 2025-01-XX

### 추가
- RAG 벡터 DB 통합 기능 추가 (`main_with_RAG.py`)
- 파이썬 교재 PDF를 벡터 DB로 저장하여 참고하는 기능
- `RAG_INTEGRATION_GUIDE.md` 문서 추가
- `README.md` 문서 추가

### 변경
- 원본 `main.py`는 RAG 기능 없이 유지
- RAG 통합 버전은 별도 파일(`main_with_RAG.py`)로 분리 (2.0.0 이후 `main.py`가 RAG 버전이 됨)

### 기능
- `generate_course()`: 커리큘럼 생성 시 교재 내용 참고
- `generate_concept()`: 개념 정리 생성 시 관련 교재 검색
- `generate_exercise()`: 실습 과제 생성 시 관련 예제 검색
- `generate_quiz()`: 퀴즈 생성 시 관련 내용 검색

## [1.0.0] - 2025-01-XX

### 초기 릴리스
- 기본 자습 과제 생성 API
- Gemini 2.5를 사용한 학습 자료 생성
- 커리큘럼, 개념 정리, 실습 과제, 퀴즈 자동 생성

