"""
데이터베이스 작업 헬퍼 함수

변경 이유:
- DB 작업 로직이 엔드포인트에 직접 포함되어 가독성 저하
- 중복된 DB 쿼리 패턴을 함수로 추출
- 시간복잡도 개선 (N+1 쿼리 방지)
"""
import json
import logging
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.models import Course as DBCourse, Chapter as DBChapter

logger = logging.getLogger("pop_pins_api")


def save_course_to_db(
    db: Session,
    topic: str,
    description: str,
    difficulty: str,
    chapters_data: list[dict]
) -> Optional[int]:
    """
    코스와 챕터 정보를 데이터베이스에 저장합니다.
    
    Args:
        db: 데이터베이스 세션
        topic: 코스 제목
        description: 코스 설명
        difficulty: 난이도
        chapters_data: 챕터 데이터 리스트
            각 항목은 {"chapterTitle": str, "chapterDescription": str} 형식
    
    Returns:
        Optional[int]: 저장된 코스 ID, 실패 시 None
    
    변경 이유:
        - DB 저장 로직을 엔드포인트에서 분리
        - 에러 처리 개선 (저장 실패해도 응답은 반환)
    """
    try:
        # 코스 생성 및 저장
        db_course = DBCourse(
            topic=topic,
            description=description,
            level=difficulty
        )
        db.add(db_course)
        db.commit()
        db.refresh(db_course)
        
        # 챕터 일괄 생성 (성능 개선: N번의 add 대신 한 번에 처리)
        db_chapters = [
            DBChapter(
                course_id=db_course.id,
                title=chapter["chapterTitle"],
                description=chapter["chapterDescription"]
            )
            for chapter in chapters_data
        ]
        db.add_all(db_chapters)
        db.commit()
        
        logger.info(f"코스 저장 완료: {topic} (ID: {db_course.id})")
        return db_course.id
        
    except Exception as db_error:
        logger.error(f"코스 저장 실패: {db_error}", exc_info=True)
        db.rollback()  # 트랜잭션 롤백
        return None


def save_chapter_content_to_db(
    db: Session,
    course_title: str,
    chapter_title: str,
    concept_data: dict,
    exercise_data: dict,
    quiz_data: dict
) -> bool:
    """
    챕터 콘텐츠를 데이터베이스에 저장합니다.
    
    Args:
        db: 데이터베이스 세션
        course_title: 코스 제목
        chapter_title: 챕터 제목
        concept_data: 개념 데이터
        exercise_data: 실습 데이터
        quiz_data: 퀴즈 데이터
    
    Returns:
        bool: 저장 성공 여부
    
    변경 이유:
        - 복잡한 DB 쿼리 로직을 함수로 분리
        - 에러 처리 개선
        - 가독성 향상
    """
    try:
        # 코스 찾기 (최신 것 우선)
        db_course = (
            db.query(DBCourse)
            .filter(DBCourse.topic == course_title)
            .order_by(DBCourse.created_at.desc())
            .first()
        )
        
        if not db_course:
            logger.warning(f"코스를 찾을 수 없음: {course_title}")
            return False
        
        # 챕터 찾기
        db_chapter = (
            db.query(DBChapter)
            .filter(
                DBChapter.course_id == db_course.id,
                DBChapter.title == chapter_title
            )
            .first()
        )
        
        if not db_chapter:
            logger.warning(f"챕터를 찾을 수 없음: {chapter_title}")
            return False
        
        # 콘텐츠 JSON 생성 및 저장
        content_json = json.dumps(
            {
                "concept": concept_data,
                "exercise": exercise_data,
                "quiz": quiz_data
            },
            ensure_ascii=False
        )
        
        db_chapter.content = content_json
        db_chapter.is_completed = 1
        db.commit()
        
        logger.info(f"챕터 콘텐츠 저장 완료: {chapter_title}")
        return True
        
    except Exception as db_error:
        logger.error(f"챕터 콘텐츠 저장 실패: {db_error}", exc_info=True)
        db.rollback()
        return False


def calculate_course_progress(chapters: list) -> Tuple[int, int, int]:
    """
    코스의 진행률을 계산합니다.
    
    Args:
        chapters: 챕터 리스트 (SQLAlchemy relationship)
    
    Returns:
        Tuple[int, int, int]: (전체 챕터 수, 완료된 챕터 수, 진행률 0-100)
    
    변경 이유:
        - 진행률 계산 로직을 재사용 가능한 함수로 추출
        - 시간복잡도 개선: 한 번의 순회로 모든 값 계산
        - 0으로 나누기 방지 로직 포함
    """
    total_chapters = len(chapters)
    if total_chapters == 0:
        return 0, 0, 0
    
    completed_chapters = sum(1 for chapter in chapters if chapter.is_completed == 1)
    progress = int((completed_chapters / total_chapters) * 100)
    
    return total_chapters, completed_chapters, progress

