"""
에러 처리 유틸리티 함수

변경 이유:
- 에러 처리 패턴이 여러 엔드포인트에서 중복됨
- 일관된 에러 메시지 형식 제공
- 로깅과 HTTP 예외 처리를 통합
"""
import logging
from fastapi import HTTPException
from typing import Optional

logger = logging.getLogger("pop_pins_api")


def validate_generator_initialized(generator) -> None:
    """
    ContentGenerator가 초기화되었는지 확인합니다.
    
    Args:
        generator: ContentGenerator 인스턴스 또는 None
    
    Raises:
        HTTPException: generator가 None인 경우 500 에러
    
    변경 이유:
        - 중복된 검증 로직을 한 곳으로 통합
        - 일관된 에러 메시지 제공
        - 더 자세한 에러 정보 제공 (사용자 친화적)
    """
    if generator is None:
        logger.error("ContentGenerator is not initialized - API request rejected")
        logger.error("This usually means:")
        logger.error("  1. GEMINI_API_KEY is missing or invalid")
        logger.error("  2. ContentGenerator failed to initialize at startup")
        logger.error("  3. Check server logs for initialization errors")
        raise HTTPException(
            status_code=500,
            detail="ContentGenerator가 초기화되지 않았습니다. 서버 로그를 확인하거나 관리자에게 문의하세요."
        )


def handle_generation_error(
    operation_name: str,
    error: Exception,
    context: Optional[str] = None
) -> HTTPException:
    """
    AI 생성 작업의 에러를 처리하고 HTTPException을 반환합니다.
    
    Args:
        operation_name: 작업 이름 (예: "커리큘럼 생성", "개념 생성")
        error: 발생한 예외
        context: 추가 컨텍스트 정보 (선택사항)
    
    Returns:
        HTTPException: 사용자에게 반환할 HTTP 예외
    
    변경 이유:
        - 에러 로깅과 HTTP 예외 생성을 통합
        - 일관된 에러 처리 패턴 제공
    """
    error_message = f"{operation_name} 실패"
    if context:
        error_message += f": {context}"
    error_message += f" - {str(error)}"
    
    logger.error(error_message, exc_info=True)
    return HTTPException(
        status_code=500,
        detail=error_message
    )


def validate_async_results(results: tuple, operation_names: list) -> None:
    """
    asyncio.gather의 결과를 검증하고 예외가 있으면 HTTPException을 발생시킵니다.
    
    Args:
        results: asyncio.gather의 반환값 튜플
        operation_names: 각 작업의 이름 리스트
    
    Raises:
        HTTPException: 결과 중 예외가 있는 경우
    
    변경 이유:
        - 반복적인 예외 체크 로직을 함수로 추출
        - 코드 가독성 향상
    """
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            operation_name = operation_names[i] if i < len(operation_names) else f"작업 {i+1}"
            raise handle_generation_error(operation_name, result)

