# 테스트 가이드

## 테스트 실행 방법

### 1. 의존성 설치

```bash
cd app
pip install -r requirements.txt
```

### 2. 테스트 실행

```bash
# 모든 테스트 실행
pytest

# 상세 출력
pytest -v

# 특정 테스트 파일만 실행
pytest tests/test_json_parsing.py

# 특정 테스트 함수만 실행
pytest tests/test_json_parsing.py::TestCleanJsonResponse::test_clean_json_basic

# 커버리지 포함
pytest --cov=app/main --cov-report=html
```

### 3. 테스트 구조

```
tests/
├── __init__.py
├── conftest.py              # 공통 fixtures
├── test_json_parsing.py     # JSON 파싱 함수 테스트
└── test_api_endpoints.py    # API 엔드포인트 테스트
```

## 테스트 작성 가이드

### 단위 테스트 작성 예시

```python
import pytest
from main import clean_json_response

def test_clean_json_basic():
    """기본 JSON 파싱 테스트"""
    text = '```json\n{"key": "value"}\n```'
    result = clean_json_response(text)
    assert result == {"key": "value"}
```

### API 테스트 작성 예시

```python
def test_health_check(client):
    """헬스 체크 엔드포인트 테스트"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
```

## 주의사항

- 실제 Gemini API를 호출하는 테스트는 모킹을 사용하세요
- 환경 변수는 `conftest.py`에서 모킹됩니다
- RAG 기능은 기본적으로 비활성화됩니다 (`USE_RAG=false`)




