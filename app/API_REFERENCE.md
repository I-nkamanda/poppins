# API 참조 문서

## 개요

자습 과제 생성 API의 상세한 API 명세서입니다.

## Base URL

```
http://localhost:8001
```

**참고**: 포트는 환경 변수 `PORT`로 설정할 수 있으며, 기본값은 8001입니다.

## 인증

현재 인증이 필요하지 않습니다. 향후 버전에서 추가될 수 있습니다.

## 엔드포인트

### POST /generate-study-material

학습 주제를 입력받아 자습 과제를 생성합니다.

#### 요청

**Content-Type:** `application/json`

**Request Body:**

```json
{
  "topic": "string (필수)",
  "difficulty": "string (선택, 기본값: '중급')",
  "max_chapters": "integer (선택, 기본값: 3)",
  "course_description": "string (선택)",
  "selected_objective": "string (선택, 학습 목표 설명)"
}
```

**필드 설명:**

| 필드 | 타입 | 필수 | 설명 | 예시 |
|------|------|------|------|------|
| `topic` | string | ✅ | 학습 주제 | "파이썬 리스트와 튜플" |
| `difficulty` | string | ❌ | 난이도 | "초급", "중급", "고급" |
| `max_chapters` | integer | ❌ | 최대 챕터 수 | 3 |
| `course_description` | string | ❌ | 강의 설명 | "파이썬 기초 자료구조 학습" |
| `selected_objective` | string | ❌ | 선택된 학습 목표 | "실무 중심의 프로젝트 기반 학습" |

#### 응답

**성공 응답 (200 OK):**

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
          },
          {
            "quiz": "리스트의 주요 메서드들을 나열하고 설명하세요."
          },
          {
            "quiz": "리스트 컴프리헨션의 장점은 무엇인가요?"
          }
        ]
      }
    }
  ]
}
```

**에러 응답 (500 Internal Server Error):**

```json
{
  "detail": "자습 과제 생성 실패: [에러 메시지]"
}
```

#### 예제

**cURL:**

```bash
curl -X POST "http://localhost:8000/generate-study-material" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "파이썬 리스트와 튜플",
    "difficulty": "초급",
    "max_chapters": 2
  }'
```

**Python:**

```python
import requests

url = "http://localhost:8000/generate-study-material"
payload = {
    "topic": "파이썬 리스트와 튜플",
    "difficulty": "초급",
    "max_chapters": 2
}

response = requests.post(url, json=payload)
data = response.json()
print(data)
```

**JavaScript:**

```javascript
fetch('http://localhost:8000/generate-study-material', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    topic: '파이썬 리스트와 튜플',
    difficulty: '초급',
    max_chapters: 2
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

### GET /

API 정보를 반환합니다.

#### 응답

  "status": "healthy"
}
```

### GET /history

생성 이력 목록을 조회합니다.

#### 요청

**Query Parameters:**

| 파라미터 | 타입 | 필수 | 설명 | 기본값 |
|---|---|---|---|---|
| `skip` | integer | ❌ | 건너뛸 개수 | 0 |
| `limit` | integer | ❌ | 가져올 개수 | 20 |

#### 응답

```json
[
  {
    "id": 1,
    "timestamp": "2023-11-25T10:00:00.000000",
    "request_type": "course",
    "topic": "파이썬 기초",
    "model_name": "gemini-2.5-flash",
    "latency_ms": 1500
  }
]
```

### GET /history/{log_id}

특정 생성 이력의 상세 내용을 조회합니다.

#### 요청

**Path Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `log_id` | integer | ✅ | 로그 ID |

#### 응답

```json
{
  "id": 1,
  "timestamp": "2023-11-25T10:00:00.000000",
  "request_type": "course",
  "topic": "파이썬 기초",
{
  "chapter_title": "string (필수)",
  "rating": "integer (필수, 1-5)",
  "comment": "string (선택)"
}
```

#### 응답

```json
{
  "status": "success",
  "message": "Feedback saved"
}
```

### POST /generate-objectives

주제에 대한 3가지 다른 학습 목표/방향을 제안합니다.

#### 요청

**Content-Type:** `application/json`

**Request Body:**

```json
{
  "topic": "string (필수)"
}
```

#### 응답

```json
{
  "objectives": [
    {
      "id": 1,
      "title": "기초 다지기",
      "description": "파이썬의 기본 문법과 핵심 개념을 탄탄하게 학습합니다.",
      "target_audience": "프로그래밍 입문자"
    },
    {
      "id": 2,
      "title": "실전 프로젝트",
      "description": "웹 크롤러 만들기 등 실습 위주로 학습합니다.",
      "target_audience": "실무 경험을 원하는 학습자"
    },
    {
      "id": 3,
      "title": "심화 이론",
      "description": "메모리 관리, 비동기 프로그래밍 등 고급 주제를 다룹니다.",
      "target_audience": "숙련된 개발자"
    }
  ]
}
```

## 데이터 모델

### StudyTopicRequest

```python
{
  "topic": str,
  "difficulty": Optional[str] = "중급",
  "max_chapters": Optional[int] = 3,
  "course_description": Optional[str] = None
}
```

### StudyMaterialResponse

```python
{
  "course": Course,
  "chapters": List[ChapterContent]
}
```

### Course

```python
{
  "id": int,
  "chapters": List[Chapter]
}
```

### Chapter

```python
{
  "chapterId": int,
  "chapterTitle": str,
  "chapterDescription": str
}
```

### ChapterContent

```python
{
  "chapter": Chapter,
  "concept": ConceptResponse,
  "exercise": ExerciseResponse,
  "quiz": QuizResponse
}
```

### ConceptResponse

```python
{
  "title": str,
  "description": str,
  "contents": str  # Markdown 형식
}
```

### ExerciseResponse

```python
{
  "title": str,
  "description": str,
  "contents": str  # Markdown 형식, 3개의 실습 문제 포함
}
```

### QuizResponse

```python
{
  "quizes": List[QuizItem]
}
```

### QuizItem

```python
{
  "quiz": str  # 주관식 퀴즈 문제
}
```

## 에러 처리

### HTTP 상태 코드

| 코드 | 설명 |
|------|------|
| 200 | 성공 |
| 422 | 요청 데이터 검증 실패 |
| 500 | 서버 내부 오류 |

### 에러 응답 형식

```json
{
  "detail": "에러 메시지"
}
```

## 제한사항

- 최대 챕터 수: 권장 5개 이하
- 응답 시간: 챕터당 약 10-30초 (Gemini API 응답 시간에 따라 다름)
- 토큰 제한: Gemini API의 토큰 제한에 따름

## 버전 정보

- API 버전: 1.9.0
- FastAPI 버전: 0.104.0+
- Gemini 모델: gemini-2.5-flash

## 추가 리소스

- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [API 문서 (Swagger UI)](http://localhost:8000/docs)
- [ReDoc](http://localhost:8000/redoc)

