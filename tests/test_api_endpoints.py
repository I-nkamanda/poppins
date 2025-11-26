import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

def test_generate_objectives(client, mock_content_generator):
    """학습 목표 생성 엔드포인트 테스트"""
    # Mock setup
    mock_content_generator.generate_learning_objectives.return_value = {
        "objectives": [
            {"id": 1, "title": "Test Obj", "description": "Desc", "target_audience": "Beginner"}
        ]
    }

    response = client.post("/generate-objectives", json={"topic": "Python"})
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["objectives"]) == 1
    assert data["objectives"][0]["title"] == "Test Obj"

def test_generate_course(client, mock_content_generator):
    """커리큘럼 생성 엔드포인트 테스트"""
    # Mock setup
    mock_content_generator.generate_course.return_value = {
        "course": {
            "id": 1,
            "chapters": [
                {"chapterId": 1, "chapterTitle": "Chapter 1", "chapterDescription": "Desc 1"}
            ]
        }
    }

    response = client.post("/generate-course", json={"topic": "Python"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["course"]["id"] == 1
    assert len(data["course"]["chapters"]) == 1

def test_generate_chapter_content(client, mock_content_generator):
    """챕터 콘텐츠 생성 엔드포인트 테스트"""
    # Mock setup
    # generate_chapter_content calls generate_concept, generate_exercise, generate_quiz in parallel
    mock_content_generator.generate_concept.return_value = {
        "title": "Concept", "description": "Desc", "contents": "Content"
    }
    mock_content_generator.generate_exercise.return_value = {
        "title": "Exercise", "description": "Desc", "contents": "Content"
    }
    mock_content_generator.generate_quiz.return_value = {
        "quizes": [{"quiz": "Quiz 1"}]
    }

    response = client.post("/generate-chapter-content", json={
        "course_title": "Python",
        "course_description": "Python Course",
        "chapter_title": "Chapter 1",
        "chapter_description": "Chapter Desc"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["concept"]["title"] == "Concept"
    assert data["exercise"]["title"] == "Exercise"
    assert len(data["quiz"]["quizes"]) == 1

def test_submit_feedback(client):
    """피드백 제출 엔드포인트 테스트"""
    from main_with_RAG import app, get_db
    from unittest.mock import MagicMock
    
    # Mock DB Session
    mock_db = MagicMock()
    
    # Override dependency
    def override_get_db():
        yield mock_db
        
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        response = client.post("/feedback", json={
            "chapter_title": "Chapter 1",
            "rating": 5,
            "comment": "Great!"
        })
        
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        
        # Verify DB add/commit called
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        
    finally:
        # Clean up override
        app.dependency_overrides = {}
