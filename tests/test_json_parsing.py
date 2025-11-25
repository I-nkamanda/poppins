"""
JSON 파싱 함수 테스트
"""
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "app"))


# 환경 변수 모킹 후 import
with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key", "USE_RAG": "false"}):
    from main_with_RAG import clean_json_response, extract_contents_from_json


class TestCleanJsonResponse:
    """clean_json_response 함수 테스트"""

    def test_clean_json_basic(self):
        """기본 JSON 파싱"""
        text = '```json\n{"key": "value"}\n```'
        result = clean_json_response(text)
        assert result == {"key": "value"}

    def test_clean_json_no_markers(self):
        """마커 없는 JSON"""
        text = '{"key": "value"}'
        result = clean_json_response(text)
        assert result == {"key": "value"}

    def test_clean_json_multiple_markers(self):
        """여러 마커 제거"""
        text = '```\n```json\n{"key": "value"}\n```\n```'
        result = clean_json_response(text)
        assert result == {"key": "value"}

    def test_clean_json_with_quizes(self):
        """quizes 배열 포함 JSON"""
        text = '{"quizes": [{"quiz": "문제1"}, {"quiz": "문제2"}]}'
        result = clean_json_response(text)
        assert "quizes" in result
        assert len(result["quizes"]) == 2

    def test_clean_json_incomplete_quizes(self):
        """불완전한 quizes 배열 처리"""
        # 잘린 JSON 시뮬레이션 - 함수가 자동으로 복구를 시도할 수 있음
        text = '{"quizes": [{"quiz": "문제1"}, {"quiz": "문제2"'
        # 함수가 복구를 시도하지만 완전히 실패할 수 있는 경우
        try:
            result = clean_json_response(text)
            # 복구가 성공한 경우 (빈 배열 또는 부분 배열)
            assert isinstance(result, dict)
        except (ValueError, KeyError):
            # 복구 실패 시 예외 발생 (이것도 정상)
            pass

    def test_clean_json_empty_string(self):
        """빈 문자열 처리"""
        text = ''
        with pytest.raises(ValueError):
            clean_json_response(text)

    def test_clean_json_invalid_json(self):
        """유효하지 않은 JSON"""
        text = 'not a json'
        with pytest.raises(ValueError):
            clean_json_response(text)


class TestExtractContentsFromJson:
    """extract_contents_from_json 함수 테스트"""

    def test_extract_contents_basic(self):
        """기본 contents 추출"""
        text = '{"title": "제목", "description": "설명", "contents": "내용입니다"}'
        result = extract_contents_from_json(text)
        assert result["title"] == "제목"
        assert result["description"] == "설명"
        assert result["contents"] == "내용입니다"

    def test_extract_contents_with_escape(self):
        """이스케이프 문자 포함"""
        text = '{"title": "제목", "description": "설명", "contents": "줄바꿈\\n탭\\t"}'
        result = extract_contents_from_json(text)
        assert "\n" in result["contents"]
        assert "\t" in result["contents"]

    def test_extract_contents_missing_fields(self):
        """필드가 없는 경우"""
        text = '{"title": "제목"}'
        result = extract_contents_from_json(text)
        assert result["title"] == "제목"
        assert result["description"] == ""
        assert result["contents"] == ""

    def test_extract_contents_empty_string(self):
        """빈 문자열"""
        text = ''
        result = extract_contents_from_json(text)
        assert result["title"] == ""
        assert result["description"] == ""
        assert result["contents"] == ""

