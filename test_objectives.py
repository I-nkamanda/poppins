import requests
import json
import time

BASE_URL = "http://localhost:8001"

def test_objectives_flow():
    topic = "Python Asyncio"
    
    print(f"1. Generating Learning Objectives for '{topic}'...")
    try:
        response = requests.post(f"{BASE_URL}/generate-objectives", json={"topic": topic})
        response.raise_for_status()
        data = response.json()
        objectives = data.get("objectives", [])
        
        if not objectives:
            print("   FAILURE: No objectives returned.")
            return

        print(f"   SUCCESS: Received {len(objectives)} objectives.")
        for obj in objectives:
            print(f"   - [{obj['id']}] {obj['title']}: {obj['description'][:50]}...")
            
    except Exception as e:
        print(f"   Objectives generation failed: {e}")
        return

    # Select the 2nd objective (Practical/Project-based usually)
    selected_obj = objectives[1]
    print(f"\n2. Generating Course with Selected Objective: '{selected_obj['title']}'...")
    
    course_payload = {
        "topic": topic,
        "difficulty": "중급",
        "max_chapters": 2,
        "selected_objective": selected_obj['description'] # Passing description as context
    }
    
    try:
        response = requests.post(f"{BASE_URL}/generate-course", json=course_payload)
        response.raise_for_status()
        course_data = response.json()
        
        print("   SUCCESS: Course generated.")
        print(f"   Course Title: {course_data['course']['chapters'][0]['chapterTitle']}")
        
    except Exception as e:
        print(f"   Course generation failed: {e}")

if __name__ == "__main__":
    test_objectives_flow()
