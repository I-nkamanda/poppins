import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app
from app.models import Course, Chapter
import json
from unittest.mock import AsyncMock, patch

# Setup Test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_improvements.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def mock_generator():
    with patch("app.main.generator") as mock:
        # Mock generate_course
        mock.generate_course = AsyncMock(return_value={
            "course": {
                "id": 1,
                "chapters": [
                    {"chapterId": 1, "chapterTitle": "Chapter 1", "chapterDescription": "Desc 1"},
                    {"chapterId": 2, "chapterTitle": "Chapter 2", "chapterDescription": "Desc 2"}
                ]
            }
        })
        # Mock generate_chapter_content
        mock.generate_concept = AsyncMock(return_value={"title": "T", "description": "D", "contents": "C"})
        mock.generate_exercise = AsyncMock(return_value={"title": "T", "description": "D", "contents": "C"})
        mock.generate_quiz = AsyncMock(return_value={"quizes": [{"quiz": "Q1"}]})
        mock.get_learning_context = lambda x: ""
        yield mock

def test_progress_and_delete_flow(client, mock_generator):
    # 1. Create Course
    response = client.post("/generate-course", json={
        "topic": "Test Topic",
        "difficulty": "Beginner",
        "max_chapters": 2
    })
    assert response.status_code == 200
    course_id = response.json()["course"]["id"]

    # 2. Check Initial Progress
    response = client.get("/courses")
    assert response.status_code == 200
    courses = response.json()
    my_course = next(c for c in courses if c["id"] == course_id)
    assert my_course["progress"] == 0
    assert my_course["completed_chapters"] == 0
    assert my_course["chapter_count"] == 2

    # 3. Generate Chapter Content (Complete Chapter 1)
    # We need to call generate-chapter-content
    # Note: The API expects ChapterRequest which uses titles, not IDs.
    response = client.post("/generate-chapter-content", json={
        "course_title": "Test Topic",
        "course_description": "Test Topic",
        "chapter_title": "Chapter 1",
        "chapter_description": "Desc 1"
    })
    assert response.status_code == 200

    # 4. Check Progress (Should be 50%)
    response = client.get("/courses")
    courses = response.json()
    my_course = next(c for c in courses if c["id"] == course_id)
    assert my_course["progress"] == 50
    assert my_course["completed_chapters"] == 1

    # 5. Delete Course
    response = client.delete(f"/courses/{course_id}")
    assert response.status_code == 200

    # 6. Verify Deletion
    response = client.get(f"/courses/{course_id}")
    assert response.status_code == 404
    
    response = client.get("/courses")
    courses = response.json()
    assert not any(c["id"] == course_id for c in courses)
