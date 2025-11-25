import requests
import json
import time

BASE_URL = "http://localhost:8001"

def test_history_logging():
    print("1. Generating course (this should be logged)...")
    course_payload = {
        "topic": "Python History Test",
        "difficulty": "초급",
        "max_chapters": 1
    }
    try:
        response = requests.post(f"{BASE_URL}/generate-course", json=course_payload)
        response.raise_for_status()
        print("   Course generation successful.")
    except Exception as e:
        print(f"   Course generation failed: {e}")
        return

    # Wait a bit for async logging (though it's synchronous in current impl)
    time.sleep(1)

    print("\n2. Checking history...")
    try:
        response = requests.get(f"{BASE_URL}/history")
        response.raise_for_status()
        history = response.json()
        
        print(f"   Found {len(history)} history items.")
        
        found = False
        for item in history:
            if item["topic"] == "Python History Test" and item["request_type"] == "course":
                print(f"   SUCCESS: Found log entry! ID: {item['id']}, Timestamp: {item['timestamp']}")
                found = True
                
                # Check detail
                print(f"   Checking detail for ID {item['id']}...")
                detail_resp = requests.get(f"{BASE_URL}/history/{item['id']}")
                detail_resp.raise_for_status()
                detail = detail_resp.json()
                if "prompt_context" in detail and "generated_content" in detail:
                     print("   SUCCESS: Detail view contains prompt and content.")
                else:
                     print("   FAILURE: Detail view missing fields.")
                break
        
        if not found:
            print("   FAILURE: Could not find the generated course in history.")
            print("   Recent items:", json.dumps(history[:2], indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"   History check failed: {e}")

if __name__ == "__main__":
    test_history_logging()
