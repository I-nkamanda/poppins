import requests
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import QuizResult, UserFeedback

BASE_URL = "http://localhost:8001"
DB_URL = "sqlite:///./history.db"

def test_feedback_flow():
    print("1. Submitting Quiz Grade Request...")
    quiz_payload = {
        "question": "파이썬 리스트의 특징은?",
        "answer": "순서가 있고 변경 가능합니다.",
        "chapter_title": "Python List Test",
        "chapter_description": "Test Description"
    }
    try:
        response = requests.post(f"{BASE_URL}/grade-quiz", json=quiz_payload)
        response.raise_for_status()
        print("   Quiz grading successful.")
    except Exception as e:
        print(f"   Quiz grading failed: {e}")
        return

    print("\n2. Submitting User Feedback...")
    feedback_payload = {
        "chapter_title": "Python List Test",
        "rating": 5,
        "comment": "Great explanation!"
    }
    try:
        response = requests.post(f"{BASE_URL}/feedback", json=feedback_payload)
        response.raise_for_status()
        print("   Feedback submission successful.")
    except Exception as e:
        print(f"   Feedback submission failed: {e}")
        return

    print("\n3. Verifying DB Records...")
    try:
        engine = create_engine(DB_URL)
        Session = sessionmaker(bind=engine)
        session = Session()

        # Check QuizResult
        quiz_result = session.query(QuizResult).filter_by(chapter_title="Python List Test").order_by(QuizResult.id.desc()).first()
        if quiz_result:
            print(f"   SUCCESS: Found QuizResult. Score: {quiz_result.score}")
        else:
            print("   FAILURE: QuizResult not found.")

        # Check UserFeedback
        feedback = session.query(UserFeedback).filter_by(chapter_title="Python List Test").order_by(UserFeedback.id.desc()).first()
        if feedback:
            print(f"   SUCCESS: Found UserFeedback. Rating: {feedback.rating}, Comment: {feedback.comment}")
        else:
            print("   FAILURE: UserFeedback not found.")
        
        session.close()

    except Exception as e:
        print(f"   DB verification failed: {e}")

if __name__ == "__main__":
    test_feedback_flow()
