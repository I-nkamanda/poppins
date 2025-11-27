import requests
import json

url = "http://localhost:8001/generate-course"
data = {
    "topic": "Python 기초",
    "difficulty": "초급",
    "max_chapters": 2
}

print("Sending request to /generate-course...")
print(f"Data: {json.dumps(data, ensure_ascii=False)}")

try:
    response = requests.post(url, json=data, timeout=60)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
except requests.exceptions.Timeout:
    print("Request timed out after 60 seconds")
except Exception as e:
    print(f"Error: {e}")
    if hasattr(e, 'response'):
        print(f"Response text: {e.response.text}")
