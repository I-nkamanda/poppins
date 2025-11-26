"""
pytest 설정 및 공통 fixtures
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "app"))

# 환경 변수 설정 (import 전에 설정해야 함)
os.environ["GEMINI_API_KEY"] = "test-api-key"
os.environ["USE_RAG"] = "false"

from main_with_RAG import app
from app.services.generator import ContentGenerator

@pytest.fixture
def mock_genai():
    """Google Generative AI 모킹"""
    with patch("app.services.generator.genai") as mock:
        # Mock GenerativeModel
        mock_model = Mock()
        mock.GenerativeModel.return_value = mock_model
        
        # Mock generate_content (sync)
        mock_response = Mock()
        mock_response.text = '{"title": "Test Title", "description": "Test Desc", "contents": "Test Content"}'
        mock_model.generate_content.return_value = mock_response
        
        # Mock generate_content_async (async)
        async_mock_response = Mock()
        async_mock_response.text = '{"objectives": [{"id": 1, "title": "Obj 1", "description": "Desc 1", "target_audience": "Beginner"}]}'
        mock_model.generate_content_async = AsyncMock(return_value=async_mock_response)
        
        yield mock

@pytest.fixture
def mock_content_generator(mock_genai):
    """ContentGenerator 모킹"""
    with patch("main_with_RAG.generator") as mock_generator:
        # Async methods need AsyncMock
        mock_generator.generate_learning_objectives = AsyncMock(return_value={
            "objectives": [
                {"id": 1, "title": "Test Objective", "description": "Test Desc", "target_audience": "Beginner"}
            ]
        })
        mock_generator.generate_course = AsyncMock(return_value={
            "course": {
                "id": 1,
                "chapters": [
                    {"chapterId": 1, "chapterTitle": "Chapter 1", "chapterDescription": "Desc 1"}
                ]
            }
        })
        mock_generator.generate_concept = AsyncMock(return_value={
            "title": "Concept 1", "description": "Desc 1", "contents": "Content 1"
        })
        mock_generator.generate_exercise = AsyncMock(return_value={
            "title": "Exercise 1", "description": "Desc 1", "contents": "Content 1"
        })
        mock_generator.generate_quiz = AsyncMock(return_value={
            "quizes": [{"quiz": "Quiz 1"}]
        })
        mock_generator.grade_quiz = AsyncMock(return_value={
            "score": 85, "feedback": "Good", "correct_points": ["Point 1"], "improvements": ["Imp 1"]
        })
        mock_generator.get_learning_context.return_value = "Test Context"
        
        yield mock_generator

@pytest.fixture
def client(mock_content_generator):
    """FastAPI 테스트 클라이언트 (Mocked Generator 주입)"""
    return TestClient(app)

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

