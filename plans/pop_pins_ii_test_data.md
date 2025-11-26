# PopPins II - 테스트 데이터 설계 (Test Data Design)

**프로젝트**: PopPins II (어딧세이 가제)  
**문서 타입**: Test Data Design & Mock Data Strategy  
**버전**: 1.9.0  
**작성일**: 2025-11-22  
**최종 업데이트**: 2025-11-26  
**작성자**: 이진걸

---

## 📌 개요

PopPins II의 테스트용 데이터 설계 문서입니다. **API 테스트**, **Frontend 개발**, **부하 테스트**에 사용할 샘플 데이터 및 Mock 데이터 전략을 정의합니다.

---

## 🎯 테스트 데이터 목적

1. **API 테스트**: 다양한 입력 시나리오 검증
2. **Frontend 개발**: 실제 데이터 없이도 UI 개발 가능
3. **부하 테스트**: 대량 데이터 시뮬레이션
4. **Edge Case 검증**: 경계값, 오류 상황 테스트
5. **Demo & Presentation**: 발표용 데모 데이터

---

## 📋 1. API Request 샘플 데이터

### 1.1 정상 케이스 (Normal Cases)

#### 초급 - 짧은 주제
```json
{
  "topic": "파이썬 리스트",
  "difficulty": "초급",
  "max_chapters": 2,
  "course_description": "파이썬 리스트 기초 학습"
}
```

#### 중급 - 표준 주제
```json
{
  "topic": "파이썬 객체지향 프로그래밍",
  "difficulty": "중급",
  "max_chapters": 3,
  "course_description": "클래스와 객체를 활용한 실전 프로그래밍"
}
```

#### 고급 - 복잡한 주제
```json
{
  "topic": "파이썬 데코레이터와 메타클래스",
  "difficulty": "고급",
  "max_chapters": 5,
  "course_description": "고급 파이썬 기법 마스터하기"
}
```

### 1.2 경계값 케이스 (Boundary Cases)

#### 최소 챕터 수
```json
{
  "topic": "파이썬 변수",
  "difficulty": "초급",
  "max_chapters": 1
}
```

#### 최대 챕터 수
```json
{
  "topic": "파이썬 풀스택 웹 개발",
  "difficulty": "고급",
  "max_chapters": 10
}
```

#### 매우 짧은 주제
```json
{
  "topic": "if문",
  "difficulty": "초급",
  "max_chapters": 1
}
```

#### 매우 긴 주제
```json
{
  "topic": "파이썬을 활용한 머신러닝 모델 개발 및 배포 전체 파이프라인 구축하기",
  "difficulty": "고급",
  "max_chapters": 8
}
```

### 1.3 오류 케이스 (Error Cases)

#### 빈 주제
```json
{
  "topic": "",
  "difficulty": "초급",
  "max_chapters": 3
}
```
**예상 결과**: 422 Validation Error

#### 잘못된 난이도
```json
{
  "topic": "파이썬 함수",
  "difficulty": "매우어려움",
  "max_chapters": 3
}
```
**예상 결과**: 422 Validation Error (허용값: "초급", "중급", "고급")

#### 음수 챕터 수
```json
{
  "topic": "파이썬 루프",
  "difficulty": "초급",
  "max_chapters": -1
}
```
**예상 결과**: 422 Validation Error

#### 챕터 수 0
```json
{
  "topic": "파이썬 문자열",
  "difficulty": "초급",
  "max_chapters": 0
}
```
**예상 결과**: 422 Validation Error

---

## 📦 2. API Response Mock 데이터

### 2.1 Complete Response Example

```json
{
  "course": {
    "id": 1,
    "chapters": [
      {
        "chapterId": 1,
        "chapterTitle": "리스트의 기본 개념",
        "chapterDescription": "파이썬 리스트의 정의, 생성, 인덱싱"
      },
      {
        "chapterId": 2,
        "chapterTitle": "리스트 메서드 활용",
        "chapterDescription": "append, extend, insert 등 주요 메서드"
      }
    ]
  },
  "chapters": [
    {
      "chapter": {
        "chapterId": 1,
        "chapterTitle": "리스트의 기본 개념",
        "chapterDescription": "파이썬 리스트의 정의, 생성, 인덱싱"
      },
      "concept": {
        "title": "리스트의 기본 개념",
        "description": "파이썬 리스트 기초",
        "contents": "## 리스트란?\n\n파이썬에서 리스트(List)는 여러 개의 값을 순서대로 저장할 수 있는 **가변(mutable)** 자료형입니다...\n\n```python\nfruits = ['사과', '바나나', '체리']\nprint(fruits[0])  # 사과\n```\n\n..."
      },
      "exercise": {
        "title": "리스트 기본 실습",
        "description": "리스트 생성 및 조작 연습",
        "contents": "## 실습 문제\n\n### 문제 1: 리스트 생성\n좋아하는 과일 5개를 담은 리스트를 만들어보세요.\n\n### 문제 2: 인덱싱\n위에서 만든 리스트의 세 번째 과일을 출력하세요.\n\n### 문제 3: 슬라이싱\n리스트의 처음 3개 항목만 출력하세요."
      },
      "quiz": {
        "quizes": [
          {
            "quiz": "파이썬 리스트의 인덱스는 몇 번부터 시작하나요?"
          },
          {
            "quiz": "리스트의 마지막 요소에 접근하려면 어떤 인덱스를 사용하나요?"
          },
          {
            "quiz": "빈 리스트를 만드는 두 가지 방법을 작성하세요."
          }
        ]
      }
    }
  ]
}
```

### 2.2 Minimal Response (1 Chapter)

```json
{
  "course": {
    "id": 2,
    "chapters": [
      {
        "chapterId": 1,
        "chapterTitle": "변수의 기초",
        "chapterDescription": "변수 선언 및 사용법"
      }
    ]
  },
  "chapters": [
    {
      "chapter": {
        "chapterId": 1,
        "chapterTitle": "변수의 기초",
        "chapterDescription": "변수 선언 및 사용법"
      },
      "concept": {
        "title": "변수란 무엇인가?",
        "description": "프로그래밍의 기본 개념",
        "contents": "## 변수의 정의\n\n변수는 데이터를 저장하는 공간입니다..."
      },
      "exercise": {
        "title": "변수 연습",
        "description": "변수 선언 및 활용",
        "contents": "### 문제 1\n자신의 이름을 저장하는 변수를 만드세요..."
      },
      "quiz": {
        "quizes": [
          {
            "quiz": "변수명 규칙 3가지를 설명하세요."
          },
          {
            "quiz": "파이썬에서 변수 타입을 선언해야 하나요?"
          },
          {
            "quiz": "변수에 저장된 값을 어떻게 출력하나요?"
          }
        ]
      }
    }
  ]
}
```

---

## 🧪 3. 테스트 시나리오별 데이터

### 3.1 페르소나 기반 테스트 데이터

#### 수진 (대학생, 비전공자)
```json
{
  "topic": "파이썬 확률과 통계 기초",
  "difficulty": "초급",
  "max_chapters": 2,
  "course_description": "중간고사 대비 3일 집중 학습"
}
```

**예상 결과**:
- 챕터 수: 2개
- 개념 정리: 비전공자 눈높이
- 실습: 기본 개념 중심
- 퀴즈: 이해도 확인 수준

#### 민수 (직장인, 리스킬링)
```json
{
  "topic": "Delphi 레거시 코드 분석 및 유지보수",
  "difficulty": "중급",
  "max_chapters": 5,
  "course_description": "팀 교육용 Delphi 실무 과정"
}
```

**예상 결과**:
- 챕터 수: 5개
- 개념 정리: 실무 중심
- 실습: 프로젝트형 과제
- 퀴즈: 실무 적용 점검

#### 윤지 (교사, 방과후 수업)
```json
{
  "topic": "파이썬 AI 윤리 교육",
  "difficulty": "초급",
  "max_chapters": 8,
  "course_description": "한 학기 분량 AI 윤리 커리큘럼"
}
```

**예상 결과**:
- 챕터 수: 8개 (주차별)
- 개념 정리: 중학생 눈높이
- 실습: 토론 주제 중심
- 퀴즈: 윤리적 사고 확인

#### 준호 (중학생, 코딩 독학)
```json
{
  "topic": "파이썬 게임 만들기 입문",
  "difficulty": "초급",
  "max_chapters": 4,
  "course_description": "재미있게 배우는 파이썬"
}
```

**예상 결과**:
- 챕터 수: 4개
- 개념 정리: 쉬운 설명
- 실습: 게임 프로젝트
- 퀴즈: 흥미 유발형

---

## 🔢 4. Edge Case 데이터

### 4.1 특수 문자 포함

```json
{
  "topic": "Python's \"특수\" 문자 처리 (& 유니코드)",
  "difficulty": "중급",
  "max_chapters": 2
}
```

### 4.2 영어 주제

```json
{
  "topic": "Python Data Structures and Algorithms",
  "difficulty": "advanced",
  "max_chapters": 5
}
```

### 4.3 혼합 언어

```json
{
  "topic": "Python으로 배우는 Machine Learning 기초",
  "difficulty": "중급",
  "max_chapters": 6
}
```

### 4.4 매우 전문적인 주제

```json
{
  "topic": "파이썬 asyncio와 concurrent.futures를 활용한 비동기 프로그래밍",
  "difficulty": "고급",
  "max_chapters": 7
}
```

---

## 🎭 5. Mock 서버 응답 (Frontend 개발용)

### 5.1 Loading State Mock

```json
{
  "status": "generating",
  "progress": 50,
  "current_chapter": 2,
  "total_chapters": 3,
  "message": "챕터 2 생성 중..."
}
```

### 5.2 Error Response Mock

```json
{
  "detail": "주제를 입력해주세요."
}
```

```json
{
  "detail": "AI 생성 중 오류가 발생했습니다. 다시 시도해주세요."
}
```

### 5.3 Empty Result Mock

```json
{
  "course": {
    "id": 0,
    "chapters": []
  },
  "chapters": []
}
```

---

## 📊 6. 부하 테스트 데이터

### 6.1 동시 요청 시나리오

**User 1**:
```json
{"topic": "파이썬 리스트", "difficulty": "초급", "max_chapters": 2}
```

**User 2**:
```json
{"topic": "파이썬 딕셔너리", "difficulty": "초급", "max_chapters": 2}
```

**User 3**:
```json
{"topic": "파이썬 함수", "difficulty": "중급", "max_chapters": 3}
```

**User 4**:
```json
{"topic": "파이썬 클래스", "difficulty": "중급", "max_chapters": 3}
```

**User 5**:
```json
{"topic": "파이썬 예외 처리", "difficulty": "초급", "max_chapters": 2}
```

### 6.2 대량 데이터 생성

**Heavy Request** (10 챕터):
```json
{
  "topic": "파이썬 웹 프레임워크 Django 완전 정복",
  "difficulty": "고급",
  "max_chapters": 10,
  "course_description": "Django를 활용한 실전 웹 개발 전체 과정"
}
```

---

## 🗂️ 7. 데이터 파일 구조

### 7.1 테스트 데이터 디렉토리

```
tests/
├── data/
│   ├── requests/
│   │   ├── normal_cases.json       # 정상 케이스
│   │   ├── boundary_cases.json     # 경계값
│   │   ├── error_cases.json        # 오류 케이스
│   │   └── persona_cases.json      # 페르소나별
│   │
│   ├── responses/
│   │   ├── sample_course_2ch.json  # 2챕터 샘플
│   │   ├── sample_course_5ch.json  # 5챕터 샘플
│   │   └── error_responses.json    # 오류 응답
│   │
│   └── mock/
│       ├── rag_contexts.json       # Mock RAG 검색 결과
│       └── gemini_responses.json   # Mock Gemini 응답
```

### 7.2 샘플 데이터 파일

**tests/data/requests/normal_cases.json**:
```json
[
  {
    "name": "beginner_list",
    "request": {
      "topic": "파이썬 리스트",
      "difficulty": "초급",
      "max_chapters": 2
    }
  },
  {
    "name": "intermediate_oop",
    "request": {
      "topic": "파이썬 객체지향",
      "difficulty": "중급",
      "max_chapters": 3
    }
  }
]
```

**tests/data/mock/rag_contexts.json**:
```json
{
  "파이썬 리스트": [
    "리스트는 파이썬의 기본 자료구조입니다. []를 사용하여 생성합니다.",
    "리스트는 인덱싱, 슬라이싱이 가능하며 가변(mutable) 객체입니다.",
    "append(), extend(), insert() 등의 메서드를 제공합니다."
  ],
  "파이썬 함수": [
    "함수는 def 키워드로 정의합니다.",
    "매개변수와 반환값을 가질 수 있습니다.",
    "람다 함수로 간단한 익명 함수를 만들 수 있습니다."
  ]
}
```

---

## 🧩 8. Fixtures (pytest)

### 8.1 Sample Request Fixtures

```python
# tests/conftest.py
import pytest
import json

@pytest.fixture
def sample_request_beginner():
    return {
        "topic": "파이썬 변수",
        "difficulty": "초급",
        "max_chapters": 1
    }

@pytest.fixture
def sample_request_intermediate():
    return {
        "topic": "파이썬 클래스",
        "difficulty": "중급",
        "max_chapters": 3
    }

@pytest.fixture
def sample_requests_all():
    with open("tests/data/requests/normal_cases.json") as f:
        return json.load(f)

@pytest.fixture
def mock_rag_context():
    return [
        "파이썬 변수는 값을 저장하는 공간입니다.",
        "변수명은 알파벳, 숫자, 밑줄(_)로 구성됩니다.",
        "변수명은 숫자로 시작할 수 없습니다."
    ]

@pytest.fixture
def mock_course_response():
    return {
        "id": 1,
        "chapters": [
            {
                "chapterId": 1,
                "chapterTitle": "테스트 챕터",
                "chapterDescription": "테스트용 설명"
            }
        ]
    }
```

---

## 🎯 9. 데이터 검증 규칙

### 9.1 Request Validation

| 필드 | 타입 | 필수 | 제약 조건 |
|------|------|------|----------|
| topic | string | ✅ | 1~500자 |
| difficulty | string | ❌ | "초급", "중급", "고급" 중 하나 (기본값: "중급") |
| max_chapters | integer | ❌ | 1~10 (기본값: 3) |
| course_description | string | ❌ | 최대 1000자 |

### 9.2 Response Validation

```python
# 응답 구조 검증 함수
def validate_study_material_response(response):
    assert "course" in response
    assert "id" in response["course"]
    assert "chapters" in response["course"]
    
    assert "chapters" in response
    assert len(response["chapters"]) > 0
    
    for chapter_content in response["chapters"]:
        assert "chapter" in chapter_content
        assert "concept" in chapter_content
        assert "exercise" in chapter_content
        assert "quiz" in chapter_content
        
        concept = chapter_content["concept"]
        assert len(concept["contents"]) >= 1000  # 최소 1000자
        
        quiz = chapter_content["quiz"]
        assert len(quiz["quizes"]) == 3  # 정확히 3개
```

---

## 📝 10. 데이터 시딩 스크립트

### 10.1 DB 시드 데이터 (향후)

```python
# scripts/seed_data.py
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Member, Course, Chapter

def seed_test_data():
    db = SessionLocal()
    
    # 테스트 사용자 생성
    test_user = Member(
        email="test@example.com",
        password="hashed_password",
        nickname="테스트유저"
    )
    db.add(test_user)
    db.commit()
    
    # 테스트 강좌 생성
    test_course = Course(
        member_id=test_user.id,
        title="파이썬 기초",
        description="테스트용 강좌",
        prompt="파이썬 기초를 배우고 싶어요",
        max_chapters=3,
        difficulty="초급"
    )
    db.add(test_course)
    db.commit()
    
    # 테스트 챕터 생성
    for i in range(1, 4):
        chapter = Chapter(
            course_id=test_course.id,
            member_id=test_user.id,
            description=f"챕터 {i}",
            is_created=True,
            is_studying=False,
            index=i
        )
        db.add(chapter)
    
    db.commit()
    db.close()

if __name__ == "__main__":
    seed_test_data()
    print("✅ 테스트 데이터 시딩 완료")
```

---

## 🎬 11. 발표용 데모 데이터

### 11.1 Demo Scenario 1: "빠른 학습"

```json
{
  "topic": "파이썬 리스트와 튜플",
  "difficulty": "초급",
  "max_chapters": 2,
  "course_description": "데이터 구조 기초 2시간 완성"
}
```

**특징**:
- 짧은 생성 시간 (~30초)
- 명확한 결과물
- 초보자 친화적

### 11.2 Demo Scenario 2: "실전 프로젝트"

```json
{
  "topic": "Flask로 만드는 간단한 투두 리스트 웹앱",
  "difficulty": "중급",
  "max_chapters": 4,
  "course_description": "실습 중심 Flask 웹 개발"
}
```

**특징**:
- 실전 프로젝트형
- 단계별 학습
- 완성도 높은 실습

---

## 📋 Summary

### 준비된 테스트 데이터

- ✅ 정상 케이스 (초급/중급/고급)
- ✅ 경계값 케이스 (min/max 챕터)
- ✅ 오류 케이스 (빈 값, 잘못된 타입)
- ✅ 페르소나 기반 시나리오 (4종)
- ✅ Edge Cases (특수문자, 영어, 긴 주제)
- ✅ Mock 데이터 (RAG, Gemini 응답)
- ✅ 발표용 데모 데이터 (2종)

### 다음 단계

1. `tests/data/` 디렉토리 생성
2. JSON 파일로 테스트 데이터 저장
3. pytest fixtures 작성
4. 테스트 스크립트 실행

---

**문서 버전**: 1.4.2  
**최종 수정일**: 2025-11-22  
**상태**: 설계 완료, 파일 생성 대기  
**다음 단계**: 테스트 데이터 파일 생성 및 fixtures 구현
