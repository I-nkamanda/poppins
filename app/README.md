# 자습 과제 생성 API

FastAPI 기반의 자습 과제 자동 생성 API입니다. Gemini 2.5를 사용하여 학습 주제에 맞는 커리큘럼, 개념 정리, 실습 과제, 퀴즈를 자동으로 생성합니다.

## 📋 개요

이 API는 학습 주제를 입력받아 다음과 같은 학습 자료를 자동으로 생성합니다:

- **커리큘럼**: 학습 주제에 맞는 챕터 구성
- **개념 정리**: 각 챕터에 대한 상세한 개념 설명 (1000~1200자)
- **실습 과제**: 3개의 개인화된 실습 문제
- **퀴즈**: 3개의 주관식 퀴즈 문제

## 🚀 빠른 시작

### 1. 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 다음을 설정하세요:

```env
GEMINI_API_KEY=your-gemini-api-key
```

API 키는 [Google AI Studio](https://makersuite.google.com/app/apikey)에서 발급받을 수 있습니다.

### 3. 서버 실행

#### 기본 버전 (RAG 없음)

```bash
python app/main.py
```

또는:

```bash
uvicorn app.main:app --reload
```

#### RAG 통합 버전 (교재 PDF 참고)

```bash
python app/main_with_RAG.py
```

또는:

```bash
uvicorn app.main_with_RAG:app --reload
```

RAG 버전 사용 시 추가 설정이 필요합니다. 자세한 내용은 [RAG_INTEGRATION_GUIDE.md](./RAG_INTEGRATION_GUIDE.md)를 참고하세요.

### 4. API 테스트

서버가 실행되면 `http://localhost:8000`에서 API를 사용할 수 있습니다.

```bash
# API 문서 확인
# 브라우저에서 http://localhost:8000/docs 접속

# Health check
curl http://localhost:8000/health
```

## 📁 파일 구조

```
app/
├── main.py                    # 원본 버전 (RAG 없음)
├── main_with_RAG.py          # RAG 통합 버전
├── requirements.txt           # 패키지 의존성
├── README.md                  # 이 파일
└── RAG_INTEGRATION_GUIDE.md  # RAG 통합 가이드
```

## 🔌 API 엔드포인트

### POST /generate-study-material

학습 주제를 입력받아 자습 과제를 생성합니다.

**Request Body:**

```json
{
  "topic": "파이썬 리스트와 튜플",
  "difficulty": "초급",
  "max_chapters": 3,
  "course_description": "파이썬 기초 자료구조 학습"
}
```

**Parameters:**
- `topic` (필수): 학습 주제
- `difficulty` (선택): 난이도 (기본값: "중급")
- `max_chapters` (선택): 최대 챕터 수 (기본값: 3)
- `course_description` (선택): 강의 설명

**Response:**

```json
{
  "course": {
    "id": 1,
    "chapters": [
      {
        "chapterId": 1,
        "chapterTitle": "리스트 기초",
        "chapterDescription": "리스트의 생성과 기본 연산"
      }
    ]
  },
  "chapters": [
    {
      "chapter": {
        "chapterId": 1,
        "chapterTitle": "리스트 기초",
        "chapterDescription": "리스트의 생성과 기본 연산"
      },
      "concept": {
        "title": "리스트 기초 개념",
        "description": "파이썬 리스트의 기본 개념과 사용법",
        "contents": "# 리스트란?\n\n리스트는..."
      },
      "exercise": {
        "title": "리스트 실습",
        "description": "리스트를 활용한 실습 문제",
        "contents": "## 문제 1\n\n..."
      },
      "quiz": {
        "quizes": [
          {
            "quiz": "리스트와 튜플의 차이점을 설명하세요."
          }
        ]
      }
    }
  ]
}
```

### GET /

API 정보를 반환합니다.

### GET /health

서버 상태를 확인합니다.

## 🔄 두 가지 버전 비교

### main.py (원본)

- RAG 기능 없음
- Gemini 2.5만 사용하여 생성
- 빠른 응답 속도
- 일반적인 학습 자료 생성

### main_with_RAG.py (RAG 통합)

- 파이썬 교재 PDF를 벡터 DB로 저장
- 생성 시 관련 교재 내용을 참고
- 더 정확하고 교재 기반의 학습 자료 생성
- 벡터 DB 설정 필요

## 📦 의존성

### 필수 패키지

- `fastapi`: 웹 프레임워크
- `uvicorn`: ASGI 서버
- `pydantic`: 데이터 검증
- `google-generativeai`: Gemini API 클라이언트
- `python-dotenv`: 환경 변수 관리

### RAG 버전 추가 패키지

- `langchain`: LLM 프레임워크
- `langchain-community`: LangChain 커뮤니티 통합
- `langchain-google-genai`: Gemini 임베딩 모델
- `faiss-cpu`: 벡터 데이터베이스

## 🛠️ 개발

### 코드 구조

- **요청/응답 모델**: Pydantic BaseModel로 정의
- **생성 함수**: 각각 `generate_concept`, `generate_exercise`, `generate_quiz`, `generate_course`
- **JSON 파싱**: Gemini 응답을 안전하게 파싱하는 헬퍼 함수

### 환경 변수

| 변수명                      | 설명                     | 필수 | 기본값                                      |
| --------------------------- | ------------------------ | ---- | ------------------------------------------- |
| `GEMINI_API_KEY`            | Gemini API 키            | ✅    | -                                           |
| `VECTOR_DB_PATH`            | 벡터 DB 경로 (RAG 버전)  | ❌    | `../vector_db/python_textbook_gemini_db`    |
| `VECTOR_DB_EMBEDDING_MODEL` | 임베딩 모델 (RAG 버전)   | ❌    | `gemini` (text-embedding-004 사용)          |
| `USE_RAG`                   | RAG 사용 여부 (RAG 버전) | ❌    | `true`                                      |

## 🐛 문제 해결

### API 키 오류

```
ValueError: GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.
```

**해결**: `.env` 파일에 `GEMINI_API_KEY`를 설정하세요.

### JSON 파싱 오류

Gemini 응답이 JSON 형식이 아닐 수 있습니다. 이 경우 자동으로 재시도하거나 프롬프트를 조정해야 합니다.

### RAG 관련 오류

RAG 버전 사용 시 문제가 발생하면 [RAG_INTEGRATION_GUIDE.md](./RAG_INTEGRATION_GUIDE.md)의 문제 해결 섹션을 참고하세요.

## 📚 참고 자료

- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [Google Gemini API 문서](https://ai.google.dev/docs)
- [RAG 통합 가이드](./RAG_INTEGRATION_GUIDE.md)
- [RAG 벡터 생성기](../cursor%20만들어보기%20버전/RAG%20vector%20generator/README.md)

## 📝 라이선스

이 프로젝트는 교육 목적으로 자유롭게 사용할 수 있습니다.

