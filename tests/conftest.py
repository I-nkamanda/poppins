"""
pytest 설정 및 공통 fixtures
"""
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "app"))


@pytest.fixture
def client():
    """FastAPI 테스트 클라이언트"""
    # 환경 변수 모킹
    with patch.dict("os.environ", {
        "GEMINI_API_KEY": "test-api-key",
        "USE_RAG": "false"
    }):
        from main_with_RAG import app
        return TestClient(app)


@pytest.fixture
def mock_gemini_response():
    """Gemini API 응답 모킹"""
    mock_response = Mock()
    mock_response.text = '{"title": "테스트", "description": "설명", "contents": "내용"}'
    return mock_response


@pytest.fixture
def sample_chapter_request():
    """샘플 ChapterRequest 데이터"""
    return {
        "course_title": "파이썬 기초",
        "course_description": "파이썬 프로그래밍 기초",
        "chapter_title": "리스트",
        "chapter_description": "파이썬 리스트의 기본 개념"
    }


@pytest.fixture
def sample_study_topic_request():
    """샘플 StudyTopicRequest 데이터"""
    return {
        "topic": "파이썬 기초",
        "difficulty": "초급",
        "max_chapters": 2,
        "course_description": "파이썬 프로그래밍 기초"
    }

