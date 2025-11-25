"""
간단한 테스트 실행 스크립트
환경 변수 모킹을 사용하여 테스트를 실행합니다.
"""
import os
import sys
from pathlib import Path
from unittest.mock import patch

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "app"))

# 환경 변수 모킹
with patch.dict(os.environ, {
    "GEMINI_API_KEY": "test-api-key-for-testing",
    "USE_RAG": "false",
    "LOG_LEVEL": "WARNING"
}):
    from main_with_RAG import clean_json_response, extract_contents_from_json
    
    print("=" * 60)
    print("JSON 파싱 함수 테스트 시작")
    print("=" * 60)
    
    # Test 1: 기본 JSON 파싱
    print("\n[Test 1] 기본 JSON 파싱")
    try:
        text = '```json\n{"key": "value"}\n```'
        result = clean_json_response(text)
        assert result == {"key": "value"}, f"Expected {{'key': 'value'}}, got {result}"
        print("✅ 통과")
    except Exception as e:
        print(f"❌ 실패: {e}")
    
    # Test 2: 마커 없는 JSON
    print("\n[Test 2] 마커 없는 JSON")
    try:
        text = '{"key": "value"}'
        result = clean_json_response(text)
        assert result == {"key": "value"}, f"Expected {{'key': 'value'}}, got {result}"
        print("✅ 통과")
    except Exception as e:
        print(f"❌ 실패: {e}")
    
    # Test 3: quizes 배열 포함
    print("\n[Test 3] quizes 배열 포함 JSON")
    try:
        text = '{"quizes": [{"quiz": "문제1"}, {"quiz": "문제2"}]}'
        result = clean_json_response(text)
        assert "quizes" in result, "quizes 키가 없습니다"
        assert len(result["quizes"]) == 2, f"Expected 2 items, got {len(result['quizes'])}"
        print("✅ 통과")
    except Exception as e:
        print(f"❌ 실패: {e}")
    
    # Test 4: 빈 문자열 처리
    print("\n[Test 4] 빈 문자열 처리")
    try:
        text = ''
        try:
            result = clean_json_response(text)
            print(f"❌ 실패: ValueError가 발생해야 합니다. 결과: {result}")
        except ValueError:
            print("✅ 통과 (예상된 ValueError 발생)")
    except Exception as e:
        print(f"❌ 실패: {e}")
    
    # Test 5: extract_contents_from_json 기본 테스트
    print("\n[Test 5] extract_contents_from_json 기본 테스트")
    try:
        text = '{"title": "제목", "description": "설명", "contents": "내용입니다"}'
        result = extract_contents_from_json(text)
        assert result["title"] == "제목", f"Expected '제목', got {result['title']}"
        assert result["description"] == "설명", f"Expected '설명', got {result['description']}"
        assert result["contents"] == "내용입니다", f"Expected '내용입니다', got {result['contents']}"
        print("✅ 통과")
    except Exception as e:
        print(f"❌ 실패: {e}")
    
    # Test 6: extract_contents_from_json 이스케이프 문자
    print("\n[Test 6] extract_contents_from_json 이스케이프 문자")
    try:
        text = '{"title": "제목", "description": "설명", "contents": "줄바꿈\\n탭\\t"}'
        result = extract_contents_from_json(text)
        assert "\n" in result["contents"], "줄바꿈 문자가 변환되지 않았습니다"
        assert "\t" in result["contents"], "탭 문자가 변환되지 않았습니다"
        print("✅ 통과")
    except Exception as e:
        print(f"❌ 실패: {e}")
    
    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)

