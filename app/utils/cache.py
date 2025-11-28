"""
캐시 관련 유틸리티 함수

변경 이유:
- 캐시 키 생성 로직이 여러 곳에서 중복됨
- 문자열 기반 키로 변경하여 튜플 해시 계산 비용 절감
- 향후 Redis 등 외부 캐시로 전환 시 용이
"""
from typing import Tuple


def create_chapter_cache_key(course_title: str, chapter_title: str, chapter_description: str) -> str:
    """
    챕터 콘텐츠 캐시 키를 생성합니다.
    
    Args:
        course_title: 코스 제목
        chapter_title: 챕터 제목
        chapter_description: 챕터 설명
    
    Returns:
        str: 캐시 키 (형식: "course:chapter:description")
    
    변경 이유:
        - 튜플 대신 문자열 사용으로 해시 계산 비용 절감
        - 외부 캐시 시스템과 호환성 향상
    """
    return f"{course_title}:{chapter_title}:{chapter_description}"



