import requests
import json

url = "http://localhost:8001/download-chapter"
data = {
    "course_title": "Python 리스트와 딕셔너리 마스터하기",
    "course_description": "Python 리스트와 딕셔너리 마스터하기",
    "chapter_title": "Python 리스트의 기초 이해 및 활용",
    "chapter_description": "Python의 핵심 자료구조인 리스트의 정의와 생성 방법을 학습합니다..."
}

print("Sending request to /download-chapter...")
print(f"Data: {json.dumps(data, ensure_ascii=False)}")

try:
    response = requests.post(url, json=data, timeout=60)
    print(f"\nStatus Code: {response.status_code}")
    
    result = response.json()
    print(f"\nFilename: {result.get('filename')}")
    print(f"\nContent (first 500 chars):")
    print(result.get('content', '')[:500])
except Exception as e:
    print(f"Error: {e}")
