import requests
import json

# Test the RAG-enabled API
url = "http://127.0.0.1:8001/generate-study-material"
payload = {
    "topic": "파이썬 리스트",
    "difficulty": "초급",
    "max_chapters": 1
}

print("Sending test request to API...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}\n")

try:
    response = requests.post(url, json=payload, timeout=60)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Request successful!")
        result = response.json()
        
        # Print a summary
        print(f"\nGenerated Course ID: {result['course']['id']}")
        print(f"Number of Chapters: {len(result['chapters'])}")
        
        if result['chapters']:
            chapter = result['chapters'][0]
            print(f"\nFirst Chapter:")
            print(f"  Title: {chapter['chapter']['chapterTitle']}")
            print(f"  Concept Title: {chapter['concept']['title']}")
            print(f"  Concept Preview: {chapter['concept']['contents'][:200]}...")
            
            # Check if RAG context was likely used (very long or detailed content)
            if len(chapter['concept']['contents']) > 800:
                print("\n✅ RAG context likely used (detailed content generated)")
    else:
        print(f"❌ Request failed")
        print(f"Response: {response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"❌ Request error: {e}")
