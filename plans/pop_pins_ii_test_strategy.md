# PopPins II - 테스트 전략 (Test Strategy)

**프로젝트**: PopPins II (어딧세이 가제)  
**문서 타입**: Test Strategy & Quality Assurance  
**버전**: 1.9.0  
**작성일**: 2025-11-22  
**작성자**: 이진걸  
**최종 업데이트**: 2025-11-26

---

## 📌 개요

PopPins II의 품질 보증(QA) 및 테스트 전략 문서입니다. **Backend API**, **AI 생성 품질**, **RAG 정확성**을 중심으로 단위 테스트, 통합 테스트, E2E 테스트 전략을 정의합니다.

---

## 🎯 테스트 목표

### Primary Goals

1. **기능 정확성**: API가 명세대로 동작
2. **AI 품질**: 생성된 학습 자료의 정확성 및 일관성
3. **RAG 신뢰성**: PDF 기반 컨텍스트 검색 정확도
4. **성능**: 응답 시간 1분 이내
5. **안정성**: 에러 없이 동작 (Retry Logic 검증)

### Quality Metrics

| 지표 | 목표 | 측정 방법 |
|------|------|----------|
| 단위 테스트 커버리지 | 80% 이상 | pytest-cov |
| API 응답 시간 | 60초 이내 | Locust 부하 테스트 |
| RAG 정확도 | 90% 이상 | 수동 검증 |
| JSON 파싱 성공률 | 95% 이상 | 로그 분석 |
| 크래시율 | 0% | 모니터링 |

---

## 🧪 테스트 피라미드

```
           ┌─────────────┐
           │   E2E (5%)  │  Frontend + Backend 통합
           ├─────────────┤
           │ Integration │  API + AI + RAG
           │   (25%)     │
           ├─────────────┤
           │   Unit      │  개별 함수 테스트
           │   (70%)     │
           └─────────────┘
```

---

## 1️⃣ Unit Tests (단위 테스트)

### 1.1 대상 함수

| 함수명 | 목적 | 테스트 케이스 수 |
|--------|------|-----------------|
| `initialize_rag_vector_db()` | FAISS DB 초기화 | 3 |
| `search_rag_context()` | RAG 검색 | 5 |
| `clean_json_response()` | JSON 파싱 | 7 |
| `generate_learning_objectives()` | 학습 목표 생성 (Retry) | 3 |
| `generate_course()` | 커리큘럼 생성 | 4 |
| `generate_concept()` | 개념 정리 생성 | 4 |
| `generate_exercise()` | 실습 생성 | 4 |
| `generate_quiz()` | 퀴즈 생성 | 4 |

### 1.2 테스트 케이스 예시

#### `generate_learning_objectives()` Retry Logic 테스트

```python
@patch("google.generativeai.GenerativeModel.generate_content")
def test_generate_objectives_retry(mock_generate):
    """3번 실패 후 예외 발생 검증"""
    mock_generate.side_effect = Exception("API Error")
    
    with pytest.raises(Exception):
        await generator.generate_learning_objectives("test")
        
    assert mock_generate.call_count == 3
```

#### `clean_json_response()` 테스트

```python
import pytest
from app.services.generator import ContentGenerator

def test_clean_json_basic():
    """기본 JSON 파싱"""
    text = '```json\n{"key": "value"}\n```'
    # ... (기존 테스트 코드)
```

### 1.3 Coverage Target

- **목표**: 80% 이상
- **도구**: pytest-cov

```bash
pytest --cov=app --cov-report=html
```

---

## 2️⃣ Integration Tests (통합 테스트)

### 2.1 API 엔드포인트 테스트

#### POST /generate-objectives (New)

```python
def test_generate_objectives_success():
    """학습 목표 생성 성공"""
    response = client.post("/generate-objectives", json={
        "topic": "파이썬 리스트"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["objectives"]) == 3
    assert data["objectives"][0]["target_audience"] is not None
```

#### POST /generate-course

```python
def test_generate_course_with_objective():
    """목표 선택 후 커리큘럼 생성"""
    response = client.post("/generate-course", json={
        "topic": "파이썬 리스트",
        "selected_objective": "실무 중심 데이터 처리"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["chapters"]) > 0
```

#### POST /feedback (New)

```python
def test_submit_feedback():
    """피드백 제출"""
    response = client.post("/feedback", json={
        "chapter_title": "리스트 기초",
        "rating": 5,
        "comment": "좋아요"
    })
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
```

### 2.2 RAG + AI 통합 테스트

```python
def test_rag_integration_with_gemini():
    """RAG 검색 + Gemini 생성"""
    query = "파이썬 함수"
    rag_docs = search_rag_context(query, k=3)
    
    # Gemini에 컨텍스트 전달
    prompt = f"다음 자료를 참고하여 개념을 설명:\n{rag_docs}"
    # ... Gemini 호출
    
    # 응답 검증
    assert len(rag_docs) > 0
```

---

## 3️⃣ E2E Tests (End-to-End 테스트)

### 3.1 시나리오 기반 테스트

#### 시나리오 1: "수진의 단기 학습" (기존)
- 주제 입력 -> 커리큘럼 생성 -> 학습

#### 시나리오 3: "적응형 학습" (New)

```python
def test_e2e_adaptive_learning():
    """
    사용자: 학습 목표 선택 및 피드백 루프
    """
    # Step 1: 목표 제안 요청
    resp1 = client.post("/generate-objectives", json={"topic": "Pandas"})
    objectives = resp1.json()["objectives"]
    selected_obj = objectives[1]["title"] # 실무형 선택
    
    # Step 2: 커리큘럼 생성
    resp2 = client.post("/generate-course", json={
        "topic": "Pandas",
        "selected_objective": selected_obj
    })
    chapter_title = resp2.json()["chapters"][0]["chapterTitle"]
    
    # Step 3: 챕터 학습 및 피드백
    resp3 = client.post("/feedback", json={
        "chapter_title": chapter_title,
        "rating": 4,
        "comment": "실습이 조금 더 많았으면 좋겠어요"
    })
    assert resp3.status_code == 200
```

---

## 4️⃣ AI Quality Tests (AI 품질 테스트)

### 4.1 생성 품질 검증

```python
def test_concept_quality():
    """개념 정리 품질 검증"""
    # ... (기존 코드)
```

### 4.2 RAG 정확성 테스트

```python
def test_rag_accuracy():
    """RAG로 검색된 문서가 관련성 있는지 수동 검증"""
    topic = "파이썬 리스트"
    docs = search_rag_context(topic, k=3)
    
    # 검색된 문서에 키워드 포함 여부
    combined_text = " ".join(docs)
    assert "리스트" in combined_text or "list" in combined_text
```

---

## 5️⃣ Regression Tests (회귀 테스트)

### 5.1 Golden Master Testing

**목적**: AI 출력 일관성 검증

```python
import json

GOLDEN_MASTERS = {
    "파이썬 리스트_초급": "tests/golden/list_beginner.json",
    "파이썬 함수_중급": "tests/golden/function_intermediate.json"
}

def test_golden_master_list_beginner():
    """골든 마스터 테스트: 리스트 초급"""
    # ... (기존 코드)
```

---

## 6️⃣ Load Tests (부하 테스트)

### 6.1 Locust 부하 테스트

```python
# locustfile.py
from locust import HttpUser, task, between

class PopPinsUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def generate_objectives(self):
        self.client.post("/generate-objectives", json={
            "topic": "파이썬 기초"
        })
```

---

## 7️⃣ Security Tests (보안 테스트)

### 7.1 Input Validation

```python
def test_sql_injection_attempt():
    """SQL Injection 시도"""
    # ... (기존 코드)
```

---

## 8️⃣ Test Data Management

### 8.1 Fixtures

```python
# conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)
```

---

## 📊 Test Execution Plan

### Phase 1: MVP 테스트 (완료)

- ✅ 수동 API 테스트 (Postman/cURL)
- ✅ 기본 동작 검증
- ✅ Retry Logic 검증

### Phase 2: 자동화 테스트 구축 (진행 중)

**Week 1**:
- [ ] Unit Tests 작성 (70% coverage)
- [ ] Integration Tests (API 엔드포인트)
- [ ] CI/CD 파이프라인 설정

**Week 2**:
- [ ] E2E Tests (주요 시나리오 3개)
- [ ] AI Quality Tests
- [ ] Load Tests (Locust)

---

## 🎯 Success Criteria

### Definition of Done (테스트 통과 기준)

- [x] 모든 API 엔드포인트 정상 응답
- [ ] Unit Test Coverage 80% 이상
- [ ] Integration Tests 100% 통과
- [ ] E2E Tests (3개 시나리오) 100% 통과
- [ ] 부하 테스트 통과 (10명 동시 사용자)
- [ ] 보안 테스트 통과
- [ ] Regression Tests 100% 통과

---

**문서 버전**: 1.5.0  
**최종 수정일**: 2025-11-25  
**상태**: 전략 수립 완료, 자동화 테스트 구축 진행 중  
**다음 단계**: Unit Tests 작성 시작
