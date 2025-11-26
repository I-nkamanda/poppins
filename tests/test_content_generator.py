import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from app.services.generator import ContentGenerator

@pytest.fixture
def generator(mock_genai):
    """ContentGenerator 인스턴스 (Mocked GenAI 사용)"""
    return ContentGenerator()

def test_init(generator):
    """초기화 테스트"""
    assert generator.model is not None
    assert generator.model_name == "gemini-2.5-flash"

def test_clean_json_valid(generator):
    """유효한 JSON 파싱 테스트"""
    valid_json = '{"key": "value"}'
    result = generator._clean_json(valid_json)
    assert result == {"key": "value"}

def test_clean_json_with_markdown(generator):
    """Markdown 코드 블록이 포함된 JSON 파싱 테스트"""
    markdown_json = '```json\n{"key": "value"}\n```'
    result = generator._clean_json(markdown_json)
    assert result == {"key": "value"}

def test_clean_json_malformed_but_recoverable(generator):
    """약간 깨진 JSON 복구 테스트"""
    # 앞뒤에 잡다한 텍스트가 있는 경우
    dirty_json = 'Here is the json: {"key": "value"} hope it helps.'
    result = generator._clean_json(dirty_json)
    assert result == {"key": "value"}

def test_clean_json_invalid(generator):
    """복구 불가능한 JSON 테스트"""
    invalid_json = 'Not a json'
    with pytest.raises(ValueError):
        generator._clean_json(invalid_json)

@pytest.mark.asyncio
async def test_generate_course_success(generator, mock_genai):
    """커리큘럼 생성 성공 테스트"""
    # Mock response setup
    mock_response = Mock()
    mock_response.text = json.dumps({
        "course": {
            "id": 1,
            "chapters": [
                {"chapterId": 1, "chapterTitle": "Test Chapter", "chapterDescription": "Test Desc"}
            ]
        }
    })
    generator.model.generate_content.return_value = mock_response

    # Call method
    result = await generator.generate_course(
        topic="Test Topic",
        description="Test Desc",
        difficulty="Beginner",
        max_chapters=3
    )

    # Assertions
    assert result["course"]["id"] == 1
    assert len(result["course"]["chapters"]) == 1
    assert result["course"]["chapters"][0]["chapterTitle"] == "Test Chapter"
    
    # Verify API call
    generator.model.generate_content.assert_called_once()

@pytest.mark.asyncio
async def test_generate_learning_objectives_retry_logic(generator):
    """학습 목표 생성 재시도 로직 테스트"""
    # 첫 2번은 실패, 3번째 성공 시나리오
    mock_response = Mock()
    mock_response.text = '{"objectives": []}'
    
    # generate_content_async가 AsyncMock이므로 side_effect를 설정할 때 주의
    # AsyncMock의 side_effect는 예외를 발생시키거나, 이터러블을 반환하여 매 호출마다 다른 값을 줄 수 있음
    
    # 2 failures then success
    generator.model.generate_content_async.side_effect = [
        Exception("API Error 1"),
        Exception("API Error 2"),
        mock_response
    ]
    
    # Call method
    result = await generator.generate_learning_objectives("Test Topic")
    
    # Assertions
    assert result == {"objectives": []}
    assert generator.model.generate_content_async.call_count == 3
