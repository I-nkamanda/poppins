from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Any
import os
from pathlib import Path
from dotenv import load_dotenv
import asyncio
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
import json

# DB imports
from sqlalchemy.orm import Session
from app.database import engine, Base, get_db
from app.models import GenerationLog, QuizResult, UserFeedback, Course as DBCourse, Chapter as DBChapter, UserPreference

# Import ContentGenerator service
from app.services.generator import ContentGenerator

load_dotenv()

# 로깅 설정
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 로거 설정
logger = logging.getLogger("pop_pins_api")
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

# 콘솔 핸들러
console_handler = logging.StreamHandler()
console_handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
console_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# 파일 핸들러 (선택사항 - logs 디렉토리에 저장)
logs_dir = Path(__file__).parent.parent / "logs"
logs_dir.mkdir(exist_ok=True)
log_file = logs_dir / "app.log"

file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=5,
    encoding="utf-8"
)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

logger.info("로깅 시스템 초기화 완료")

app = FastAPI(title="자습 과제 생성 API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB 초기화
Base.metadata.create_all(bind=engine)

# Initialize ContentGenerator
try:
    generator = ContentGenerator()
    logger.info("ContentGenerator initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize ContentGenerator: {e}")
    generator = None

# 챕터 콘텐츠 캐시 (메모리 기반, DB 없이)
chapter_cache = {}


# 요청 모델
class StudyTopicRequest(BaseModel):
    topic: str
    difficulty: Optional[str] = "중급"
    max_chapters: Optional[int] = 3
    course_description: Optional[str] = None
    selected_objective: Optional[str] = None  # New field for selected learning objective
    language: Optional[str] = "ko"  # Language preference (ko/en)


class ChapterRequest(BaseModel):
    course_title: str
    course_description: str
    chapter_title: str
    chapter_description: str


# 응답 모델
class ConceptResponse(BaseModel):
    title: str
    description: str
    contents: str


class ExerciseResponse(BaseModel):
    title: str
    description: str
    contents: str
    contents: str


class QuizItem(BaseModel):
    quiz: str


class QuizResponse(BaseModel):
    quizes: List[QuizItem]


class Chapter(BaseModel):
    chapterId: int
    chapterTitle: str
    chapterDescription: str


class Course(BaseModel):
    id: int
    topic: Optional[str] = None
    description: Optional[str] = None
    level: Optional[str] = None
    chapters: List[Chapter]


class CourseResponse(BaseModel):
    course: Course


class ChapterContent(BaseModel):
    chapter: Chapter
    concept: ConceptResponse
    exercise: ExerciseResponse
    quiz: QuizResponse


class StudyMaterialResponse(BaseModel):
    course: Course
    chapters: List[ChapterContent]


class DownloadResponse(BaseModel):
    filename: str
    content: str


# History Response Model
class HistoryItem(BaseModel):
    id: int
    timestamp: str
    request_type: str
    topic: str
    model_name: str
    latency_ms: Optional[int]
    # prompt_context and generated_content are excluded for list view to keep it light


class HistoryDetail(HistoryItem):
    prompt_context: str
    generated_content: str


class ObjectiveItem(BaseModel):
    id: int
    title: str
    description: str
    target_audience: str


class ObjectivesResponse(BaseModel):
    objectives: List[ObjectiveItem]


class FeedbackRequest(BaseModel):
    chapter_title: str
    rating: int  # 1-5
    comment: Optional[str] = None


# 메인 API 엔드포인트

@app.post("/generate-objectives", response_model=ObjectivesResponse)
async def generate_objectives(request: StudyTopicRequest):
    """
    주제에 대한 3가지 다른 학습 목표/방향을 제안합니다.
    """
    if not generator:
        raise HTTPException(status_code=500, detail="ContentGenerator not initialized")

    try:
        result = await generator.generate_learning_objectives(request.topic, request.language)
        return ObjectivesResponse(**result)
    except Exception as e:
        logger.error(f"학습 목표 제안 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"학습 목표 제안 실패: {str(e)}")


@app.post("/generate-course", response_model=CourseResponse)
async def generate_course_only(request: StudyTopicRequest, db: Session = Depends(get_db)):
    """
    1단계: 커리큘럼(목차)만 먼저 생성합니다. (빠름)
    선택된 학습 목표가 있다면 반영합니다.
    """
    if not generator:
        raise HTTPException(status_code=500, detail="ContentGenerator not initialized")

    try:
        result = await generator.generate_course(
            topic=request.topic,
            description=request.course_description or request.topic,
            difficulty=request.difficulty,
            max_chapters=request.max_chapters,
            selected_objective=request.selected_objective,
            language=request.language
        )
        
        # Save to DB
        try:
            db_course = DBCourse(
                topic=request.topic,
                description=request.course_description or request.topic,
                level=request.difficulty
            )
            db.add(db_course)
            db.commit()
            db.refresh(db_course)
            
            # Save Chapters
            for ch in result["course"]["chapters"]:
                db_chapter = DBChapter(
                    course_id=db_course.id,
                    title=ch["chapterTitle"],
                    description=ch["chapterDescription"]
                )
                db.add(db_chapter)
            db.commit()
            
            # Update result with DB ID
            result["course"]["id"] = db_course.id
            
        except Exception as db_e:
            logger.error(f"Failed to save course to DB: {db_e}")
            # Continue even if DB save fails, but log it
            
        return CourseResponse(**result)
    except Exception as e:
        logger.error(f"커리큘럼 생성 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"커리큘럼 생성 실패: {str(e)}")


@app.post("/generate-chapter-content", response_model=ChapterContent)
async def generate_chapter_content_only(request: ChapterRequest, db: Session = Depends(get_db)):
    """
    2단계: 특정 챕터의 상세 내용(개념, 실습, 퀴즈)을 생성합니다. (챕터 클릭 시 호출)
    캐시에 있으면 재사용, 없으면 생성 후 캐시에 저장
    """
    if not generator:
        raise HTTPException(status_code=500, detail="ContentGenerator not initialized")

    # 캐시 키 생성
    cache_key = (
        request.course_title,
        request.chapter_title,
        request.chapter_description,
    )

    # 1. 메모리 캐시 확인
    if cache_key in chapter_cache:
        logger.info(f"캐시에서 로드: {request.chapter_title}")
        return chapter_cache[cache_key]

    # 2. DB 확인 (이미 생성된 콘텐츠가 있는지)
    # Note: This requires searching by title/course which might be ambiguous if multiple courses have same title.
    # Ideally we should pass chapter_id, but the current frontend request doesn't send it.
    # We will skip DB read for now and rely on generation/cache, but we WILL save to DB.
    # Future improvement: Pass chapter_id in request.

    logger.info(f"챕터 콘텐츠 생성 시작: {request.chapter_title}")
    try:
        # Fetch learning context (adaptive learning)
        learning_context = generator.get_learning_context(request.course_title)
        if learning_context:
            logger.info(f"학습 컨텍스트 적용: {len(learning_context)} chars")

        # 병렬로 생성 (개념, 실습, 퀴즈)
        results = await asyncio.gather(
            generator.generate_concept(
                course_title=request.course_title,
                course_desc=request.course_description,
                chapter_title=request.chapter_title,
                chapter_desc=request.chapter_description,
                learning_context=learning_context
            ),
            generator.generate_exercise(
                course_title=request.course_title,
                course_desc=request.course_description,
                chapter_title=request.chapter_title,
                chapter_desc=request.chapter_description,
                learning_context=learning_context
            ),
            generator.generate_quiz(
                course_title=request.course_title,
                chapter_title=request.chapter_title,
                chapter_desc=request.chapter_description,
                course_prompt=request.course_title,
                learning_context=learning_context
            ),
            return_exceptions=True,
        )

        # 각 결과 확인 및 에러 처리
        concept_data, exercise_data, quiz_data = results

        if isinstance(concept_data, Exception):
            logger.error(f"개념 생성 실패: {request.chapter_title} - {concept_data}")
            raise HTTPException(status_code=500, detail=f"개념 정리 생성 실패: {str(concept_data)}")
        if isinstance(exercise_data, Exception):
            logger.error(f"실습 생성 실패: {request.chapter_title} - {exercise_data}")
            raise HTTPException(status_code=500, detail=f"실습 과제 생성 실패: {str(exercise_data)}")
        if isinstance(quiz_data, Exception):
            logger.error(f"퀴즈 생성 실패: {request.chapter_title} - {quiz_data}")
            raise HTTPException(status_code=500, detail=f"퀴즈 생성 실패: {str(quiz_data)}")

        logger.info(f"챕터 콘텐츠 생성 완료: {request.chapter_title}")

        # Chapter 객체 생성
        chapter_info = Chapter(
            chapterId=0,  # ID는 프론트엔드 컨텍스트에 있음
            chapterTitle=request.chapter_title,
            chapterDescription=request.chapter_description,
        )

        result = ChapterContent(
            chapter=chapter_info,
            concept=ConceptResponse(**concept_data),
            exercise=ExerciseResponse(**exercise_data),
            quiz=QuizResponse(**quiz_data)
        )

        # 캐시에 저장
        chapter_cache[cache_key] = result
        logger.debug(f"캐시에 저장: {request.chapter_title}")
        
        # DB에 저장
        try:
            # Find the chapter in DB to update it
            # We need to find the course first, then the chapter.
            # Since we don't have IDs, this is a best-effort lookup.
            # We assume the course exists.
            db_course = db.query(DBCourse).filter(DBCourse.topic == request.course_title).order_by(DBCourse.created_at.desc()).first()
            if db_course:
                db_chapter = db.query(DBChapter).filter(
                    DBChapter.course_id == db_course.id,
                    DBChapter.title == request.chapter_title
                ).first()
                
                if db_chapter:
                    # Update content
                    content_json = json.dumps({
                        "concept": concept_data,
                        "exercise": exercise_data,
                        "quiz": quiz_data
                    }, ensure_ascii=False)
                    db_chapter.content = content_json
                    db_chapter.is_completed = 1
                    db.commit()
                    logger.info(f"DB에 챕터 콘텐츠 저장 완료: {request.chapter_title}")
        except Exception as db_e:
             logger.error(f"Failed to save chapter content to DB: {db_e}")

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"챕터 콘텐츠 생성 중 예상치 못한 오류: {request.chapter_title} - {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"챕터 콘텐츠 생성 실패: {str(e)}")


# 기존 엔드포인트 (하위 호환성 유지)
@app.post("/generate-study-material", response_model=StudyMaterialResponse)
async def generate_study_material(request: StudyTopicRequest):
    """
    공부 주제를 입력받아 자습 과제를 생성합니다. (일괄 생성 - 느림)
    """
    try:
        # 1. 강의 커리큘럼 생성
        course_response = await generate_course_only(request)
        course = course_response.course

        # 2. 각 챕터별 콘텐츠 생성
        chapters_content = []
        for chapter in course.chapters:
            chapter_request = ChapterRequest(
                course_title=request.topic,
                course_description=request.course_description or request.topic,
                chapter_title=chapter.chapterTitle,
                chapter_description=chapter.chapterDescription,
            )

            content = await generate_chapter_content_only(chapter_request)
            chapters_content.append(content)

        return StudyMaterialResponse(course=course, chapters=chapters_content)
    except Exception as e:
        logger.error(f"자습 과제 생성 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"자습 과제 생성 실패: {str(e)}")


@app.get("/")
async def root():
    return {
        "message": "자습 과제 생성 API",
        "version": "1.0.0",
        "endpoints": {
            "POST /generate-study-material": "공부 주제를 입력받아 자습 과제 생성"
        },
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


# 챕터 다운로드 엔드포인트
@app.post("/download-chapter", response_model=DownloadResponse)
async def download_chapter(request: ChapterRequest):
    """
    챕터 콘텐츠를 Markdown 형식으로 반환합니다.
    """
    # 캐시에서 가져오거나 생성
    cache_key = (
        request.course_title,
        request.chapter_title,
        request.chapter_description,
    )

    if cache_key in chapter_cache:
        content = chapter_cache[cache_key]
    else:
        # 없으면 생성
        content = await generate_chapter_content_only(request)

    # Markdown 형식으로 변환
    markdown = f"""# {content.chapter.chapterTitle}

{content.chapter.chapterDescription}

---

## 📚 개념 학습

### {content.concept.title}

{content.concept.description}

{content.concept.contents}

---

## 💻 실습 과제

### {content.exercise.title}

{content.exercise.description}

{content.exercise.contents}

---

## ❓ 퀴즈

"""

    for idx, quiz_item in enumerate(content.quiz.quizes, 1):
        markdown += f"### 문제 {idx}\n\n{quiz_item.quiz}\n\n---\n\n"

    # 파일명 생성: 특수문자 제거 및 공백을 언더스코어로 변경
    import re
    safe_filename = re.sub(r'[<>:"/\\|?*]', '', content.chapter.chapterTitle)
    safe_filename = safe_filename.replace(' ', '_')
    
    return DownloadResponse(
        filename=f"{safe_filename}.md",
        content=markdown
    )


# 퀴즈 채점 엔드포인트
class QuizGradingRequest(BaseModel):
    question: str
    answer: str
    chapter_title: str
    chapter_description: str


@app.post("/grade-quiz")
async def grade_quiz(request: QuizGradingRequest, db: Session = Depends(get_db)):
    """
    퀴즈 답안을 AI로 채점하고 결과를 저장합니다.
    """
    if not generator:
        raise HTTPException(status_code=500, detail="ContentGenerator not initialized")

    try:
        result = await generator.grade_quiz(
            question=request.question,
            answer=request.answer,
            chapter_title=request.chapter_title,
            chapter_desc=request.chapter_description
        )

        # Save result to DB
        try:
            quiz_result = QuizResult(
                chapter_title=request.chapter_title,
                score=result.get("score", 0),
                weak_points=json.dumps(result.get("improvements", []), ensure_ascii=False),
                timestamp=datetime.utcnow()
            )
            db.add(quiz_result)
            db.commit()
        except Exception as db_e:
            logger.error(f"Failed to save quiz result: {db_e}")

        return result
    except Exception as e:
        logger.error(f"퀴즈 채점 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"퀴즈 채점 실패: {str(e)}")


@app.post("/feedback")
def submit_feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    """
    사용자 피드백을 저장합니다.
    """
    try:
        feedback = UserFeedback(
            chapter_title=request.chapter_title,
            rating=request.rating,
            comment=request.comment,
            timestamp=datetime.utcnow()
        )
        db.add(feedback)
        db.commit()
        return {"status": "success", "message": "Feedback saved"}
    except Exception as e:
        logger.error(f"피드백 저장 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"피드백 저장 실패: {str(e)}")


# History Endpoints
@app.get("/history", response_model=List[HistoryItem])
def get_history(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """
    생성 이력을 조회합니다.
    """
    logs = db.query(GenerationLog).order_by(GenerationLog.timestamp.desc()).offset(skip).limit(limit).all()
    return [
        HistoryItem(
            id=log.id,
            timestamp=log.timestamp.isoformat(),
            request_type=log.request_type,
            topic=log.topic,
            model_name=log.model_name,
            latency_ms=log.latency_ms
        ) for log in logs
    ]

@app.get("/history/{log_id}", response_model=HistoryDetail)
def get_history_detail(log_id: int, db: Session = Depends(get_db)):
    """
    특정 생성 이력의 상세 내용을 조회합니다.
    """
    log = db.query(GenerationLog).filter(GenerationLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    
    return HistoryDetail(
        id=log.id,
        timestamp=log.timestamp.isoformat(),
        request_type=log.request_type,
        topic=log.topic,
        model_name=log.model_name,
        latency_ms=log.latency_ms,
        prompt_context=log.prompt_context,
        generated_content=log.generated_content
    )


# User Preference Endpoints

class UserPreferenceRequest(BaseModel):
    learning_goal: str
    learning_style: str
    desired_depth: str

@app.post("/user/preferences")
def save_user_preference(request: UserPreferenceRequest, db: Session = Depends(get_db)):
    """
    사용자의 학습 선호도 설문 결과를 저장합니다.
    """
    try:
        pref = UserPreference(
            learning_goal=request.learning_goal,
            learning_style=request.learning_style,
            desired_depth=request.desired_depth
        )
        db.add(pref)
        db.commit()
        return {"status": "success", "message": "Preferences saved"}
    except Exception as e:
        logger.error(f"Failed to save preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to save preferences")


# Dashboard Endpoints

class CourseListItem(BaseModel):
    id: int
    topic: str
    description: str
    level: str
    created_at: str
    chapter_count: int
    completed_chapters: int
    progress: int

@app.get("/courses", response_model=List[CourseListItem])
def get_courses(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """
    저장된 코스 목록을 조회합니다.
    """
    courses = db.query(DBCourse).order_by(DBCourse.created_at.desc()).offset(skip).limit(limit).all()
    result = []
    for c in courses:
        total = len(c.chapters)
        completed = sum(1 for ch in c.chapters if ch.is_completed)
        progress = int((completed / total * 100) if total > 0 else 0)
        
        result.append(CourseListItem(
            id=c.id,
            topic=c.topic,
            description=c.description,
            level=c.level or "Unknown",
            created_at=c.created_at.isoformat(),
            chapter_count=total,
            completed_chapters=completed,
            progress=progress
        ))
    return result

@app.get("/courses/{course_id}", response_model=CourseResponse)
def get_course_detail(course_id: int, db: Session = Depends(get_db)):
    """
    특정 코스의 상세 정보를 조회합니다.
    """
    db_course = db.query(DBCourse).filter(DBCourse.id == course_id).first()
    if not db_course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    chapters = []
    for ch in db_course.chapters:
        chapters.append(Chapter(
            chapterId=ch.id,
            chapterTitle=ch.title,
            chapterDescription=ch.description
        ))
        
    return CourseResponse(
        course=Course(
            id=db_course.id,
            topic=db_course.topic,
            description=db_course.description,
            level=db_course.level,
            chapters=chapters
        )
    )


@app.delete("/courses/{course_id}")
def delete_course(course_id: int, db: Session = Depends(get_db)):
    """
    코스를 삭제합니다. (관련 챕터도 함께 삭제됨 - Cascade 설정 필요하지만 여기선 수동 삭제)
    """
    db_course = db.query(DBCourse).filter(DBCourse.id == course_id).first()
    if not db_course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Delete chapters first (if cascade not set in DB)
    db.query(DBChapter).filter(DBChapter.course_id == course_id).delete()
    
    # Delete course
    db.delete(db_course)
    db.commit()
    
    return {"status": "success", "message": f"Course {course_id} deleted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
