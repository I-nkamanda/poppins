import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_dashboard_flow(client, mock_content_generator):
    # 1. Generate a Course
    response = client.post("/generate-course", json={
        "topic": "Dashboard Test",
        "difficulty": "초급",
        "max_chapters": 2
    })
    assert response.status_code == 200
    course_data = response.json()
    assert "course" in course_data
    course_id = course_data["course"]["id"]
    assert course_id is not None
    assert len(course_data["course"]["chapters"]) == 1

    # 2. List Courses
    response = client.get("/courses")
    assert response.status_code == 200
    courses = response.json()
    assert len(courses) >= 1
    # Find our course
    my_course = next((c for c in courses if c["id"] == course_id), None)
    assert my_course is not None
    assert my_course["topic"] == "Dashboard Test"
    assert my_course["chapter_count"] == 1

    # 3. Get Course Detail
    response = client.get(f"/courses/{course_id}")
    assert response.status_code == 200
    detail_data = response.json()
    assert detail_data["course"]["id"] == course_id
    assert len(detail_data["course"]["chapters"]) == 1
    assert detail_data["course"]["topic"] == "Dashboard Test"

    # 4. Generate Chapter Content (to trigger DB save)
    # We need chapter titles from the generated course
    chapter = course_data["course"]["chapters"][0]
    response = client.post("/generate-chapter-content", json={
        "course_title": "Dashboard Test",
        "course_description": "Dashboard Test Description",
        "chapter_title": chapter["chapterTitle"],
        "chapter_description": chapter["chapterDescription"]
    })
    assert response.status_code == 200
    content_data = response.json()
    assert content_data["concept"]["title"] is not None
    
    # Note: We can't easily verify DB content persistence via API yet as read is not implemented,
    # but we verified the endpoint returns success.
