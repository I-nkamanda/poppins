import requests
import json
import time

BASE_URL = "http://localhost:8001"

def test_adaptive_flow():
    course_title = "Adaptive Python Course"
    chapter_1 = "Chapter 1: Basics"
    chapter_2 = "Chapter 2: Advanced"

    print(f"1. Submitting Low Score for '{chapter_1}'...")
    quiz_payload = {
        "question": "What is a list?",
        "answer": "I don't know.",
        "chapter_title": chapter_1,
        "chapter_description": "Basic concepts"
    }
    try:
        # We use grade-quiz to simulate a result being saved
        # Note: In a real scenario, the score comes from the AI grading.
        # Here we rely on the AI grading "I don't know" as a low score.
        response = requests.post(f"{BASE_URL}/grade-quiz", json=quiz_payload)
        response.raise_for_status()
        result = response.json()
        print(f"   Graded Score: {result.get('score')}")
    except Exception as e:
        print(f"   Quiz submission failed: {e}")
        return

    print(f"\n2. Submitting Feedback for '{chapter_1}'...")
    feedback_payload = {
        "chapter_title": chapter_1,
        "rating": 1,
        "comment": "It was too hard and confusing."
    }
    try:
        requests.post(f"{BASE_URL}/feedback", json=feedback_payload)
        print("   Feedback submitted.")
    except Exception as e:
        print(f"   Feedback submission failed: {e}")
        return

    print(f"\n3. Generating '{chapter_2}' (Should use context)...")
    chapter_req = {
        "course_title": course_title,
        "course_description": "Learn Python",
        "chapter_title": chapter_2,
        "chapter_description": "Advanced concepts"
    }
    try:
        requests.post(f"{BASE_URL}/generate-chapter-content", json=chapter_req)
        print("   Generation successful.")
    except Exception as e:
        print(f"   Generation failed: {e}")
        return

    # Wait for logging
    time.sleep(2)

    print("\n4. Verifying Context Usage in History...")
    try:
        response = requests.get(f"{BASE_URL}/history?limit=5")
        history = response.json()
        
        found_context = False
        for item in history:
            if item["topic"] == chapter_2:
                # Get detail
                detail = requests.get(f"{BASE_URL}/history/{item['id']}").json()
                prompt = detail.get("prompt_context", "")
                
                if "[User Learning Context]" in prompt:
                    print("   SUCCESS: Found '[User Learning Context]' in prompt.")
                    print("   Context Snippet:")
                    start = prompt.find("[User Learning Context]")
                    print(prompt[start:start+200] + "...")
                    found_context = True
                    break
        
        if not found_context:
            print("   FAILURE: Did not find usage of learning context in recent logs.")

    except Exception as e:
        print(f"   Verification failed: {e}")

if __name__ == "__main__":
    test_adaptive_flow()
