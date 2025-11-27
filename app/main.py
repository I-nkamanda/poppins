"""
PopPins II - 메인 FastAPI 애플리케이션

이 모듈은 PopPins II의 백엔드 API 서버를 구성합니다.
주요 기능:
- AI 기반 교육 콘텐츠 생성 (커리큘럼, 개념, 실습, 퀴즈)
- RAG(Retrieval-Augmented Generation)를 통한 참고 자료 활용
- 사용자 학습 이력 및 피드백 관리
- 대시보드 데이터 제공

API 엔드포인트:
- POST /generate-objectives: 학습 목표 제안
- POST /generate-course: 커리큘럼 생성
- POST /generate-chapter-content: 챕터 상세 콘텐츠 생성
- POST /grade-quiz: 퀴즈 채점
- GET /courses: 코스 목록 조회
- 기타 관리 엔드포인트들

작성자: PopPins II 개발팀
버전: 1.0.0
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Any
import os
from pathlib import Path
from dotenv import load_dotenv
import asyncio
from datetime import datetime, timezone
import logging
from logging.handlers import RotatingFileHandler
import json

# DB imports
from sqlalchemy.orm import Session
from app.database import engine, Base, get_db
from app.models import GenerationLog, QuizResult, UserFeedback, Course as DBCourse, Chapter as DBChapter, UserPreference

# Import ContentGenerator service
from app.services.generator import ContentGenerator

# Import utility functions
from app.utils.cache import create_chapter_cache_key
from app.utils.errors import validate_generator_initialized, handle_generation_error, validate_async_results
from app.utils.db_helpers import save_course_to_db, save_chapter_content_to_db, calculate_course_progress

# 환경 변수 로드 (.env 파일에서)
load_dotenv()

# ============================================================================
# 로깅 설정
# ============================================================================
# 로그 레벨: 환경 변수에서 가져오거나 기본값 "INFO" 사용
# 가능한 값: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 로거 인스턴스 생성 및 설정
logger = logging.getLogger("pop_pins_api")
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

# 콘솔 핸들러: 개발 중 실시간 로그 확인용
console_handler = logging.StreamHandler()
console_handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
console_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# 파일 핸들러: 로그 파일 저장용 (RotatingFileHandler로 용량 관리)
# - 최대 10MB까지 저장, 5개 파일까지 보관
logs_dir = Path(__file__).parent.parent / "logs"
logs_dir.mkdir(exist_ok=True)  # logs 디렉토리가 없으면 생성
log_file = logs_dir / "app.log"

file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10 * 1024 * 1024,  # 10MB - 파일이 이 크기를 넘으면 새 파일 생성
    backupCount=5,  # 최대 5개의 백업 파일 보관 (app.log, app.log.1, ..., app.log.5)
    encoding="utf-8"  # 한글 로그를 위해 UTF-8 인코딩 사용
)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

logger.info("로깅 시스템 초기화 완료")

# ============================================================================
# FastAPI 애플리케이션 초기화
# ============================================================================
app = FastAPI(title="자습 과제 생성 API", version="1.0.0")

# CORS (Cross-Origin Resource Sharing) 설정
# 프론트엔드에서 백엔드 API를 호출할 수 있도록 허용
# 주의: 프로덕션 환경에서는 allow_origins를 특정 도메인으로 제한해야 함
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 출처 허용 (개발용)
    allow_credentials=True,  # 쿠키/인증 정보 허용
    allow_methods=["*"],  # 모든 HTTP 메서드 허용 (GET, POST, DELETE 등)
    allow_headers=["*"],  # 모든 헤더 허용
)

# ============================================================================
# 데이터베이스 초기화
# ============================================================================
# SQLAlchemy 모델을 기반으로 데이터베이스 테이블 생성
# 이미 테이블이 존재하면 무시됨
Base.metadata.create_all(bind=engine)

# ============================================================================
# ContentGenerator 초기화
# ============================================================================
# AI 콘텐츠 생성을 담당하는 서비스 클래스
# 초기화 실패 시에도 서버는 실행되지만, 생성 기능은 사용 불가
try:
    # API 키 사전 검증
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        logger.error("GEMINI_API_KEY is not set or is set to default value")
        logger.error("Please set GEMINI_API_KEY in .env file")
        raise ValueError("GEMINI_API_KEY environment variable is not set or invalid")
    
    generator = ContentGenerator()
    logger.info("ContentGenerator initialized successfully")
    logger.info(f"Gemini API Key: {api_key[:5]}...{api_key[-5:]} (masked)")
except ValueError as ve:
    # API 키 관련 에러는 명확하게 로깅
    logger.error(f"ContentGenerator initialization failed - Configuration Error: {ve}")
    logger.error("Please check your .env file and ensure GEMINI_API_KEY is set correctly")
    generator = None
except ImportError as ie:
    # Import 에러는 의존성 문제일 가능성
    logger.error(f"ContentGenerator initialization failed - Import Error: {ie}")
    logger.error("Please check if all required packages are installed (pip install -r requirements.txt)")
    generator = None
except Exception as e:
    # 기타 모든 에러는 상세히 로깅
    logger.error(f"Failed to initialize ContentGenerator: {e}", exc_info=True)
    logger.error("This may be due to:")
    logger.error("  1. Missing or invalid GEMINI_API_KEY")
    logger.error("  2. RAG Vector DB path issue (if USE_RAG=true)")
    logger.error("  3. Network connectivity issues")
    generator = None  # None으로 설정하여 초기화 실패 상태 표시

# ============================================================================
# 메모리 캐시
# ============================================================================
# 챕터 콘텐츠를 메모리에 캐시하여 동일한 요청 시 재생성 방지
# 키: 문자열 (create_chapter_cache_key로 생성)
# 값: ChapterContent 객체
# 주의: 서버 재시작 시 캐시는 초기화됨 (영구 저장을 원하면 Redis 등 사용)
# 변경 이유: 튜플 키 대신 문자열 키 사용으로 해시 계산 비용 절감
# 타입 힌트는 나중에 정의되는 ChapterContent를 참조하므로 문자열로 처리
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.main import ChapterContent
chapter_cache: dict[str, 'ChapterContent'] = {}


# ============================================================================
# Pydantic 요청 모델 (Request Models)
# ============================================================================
# 클라이언트로부터 받는 데이터의 구조와 유효성을 정의
# FastAPI가 자동으로 JSON 검증 및 직렬화 처리

class StudyTopicRequest(BaseModel):
    """
    학습 주제 생성 요청 모델
    
    Attributes:
        topic (str): 학습하고 싶은 주제 (필수)
            예: "파이썬 리스트", "React 기초"
        difficulty (Optional[str]): 난이도 레벨, 기본값 "중급"
            가능한 값: "초급", "중급", "고급"
        max_chapters (Optional[int]): 생성할 최대 챕터 수, 기본값 3
            범위: 1-10 권장
        course_description (Optional[str]): 코스에 대한 추가 설명
            주제를 더 구체화하거나 특정 방향을 제시할 때 사용
        selected_objective (Optional[str]): 사용자가 선택한 학습 목표
            generate-objectives 엔드포인트에서 받은 목표 중 하나
        language (Optional[str]): 출력 언어, 기본값 "ko"
            가능한 값: "ko" (한국어), "en" (영어)
    """
    topic: str
    difficulty: Optional[str] = "중급"
    max_chapters: Optional[int] = 3
    course_description: Optional[str] = None
    selected_objective: Optional[str] = None  # 선택된 학습 목표
    language: Optional[str] = "ko"  # 언어 설정 (ko/en)


class ChapterRequest(BaseModel):
    """
    챕터 콘텐츠 생성 요청 모델
    
    특정 챕터의 상세 콘텐츠(개념, 실습, 퀴즈)를 생성할 때 사용됩니다.
    
    Attributes:
        course_title (str): 코스 제목 (필수)
            예: "파이썬 기초"
        course_description (str): 코스 설명 (필수)
            전체 코스의 맥락을 제공하여 챕터 콘텐츠의 일관성 유지
        chapter_title (str): 챕터 제목 (필수)
            예: "리스트 기초"
        chapter_description (str): 챕터 설명 (필수)
            이 챕터에서 다룰 내용에 대한 간단한 설명
    """
    course_title: str
    course_description: str
    chapter_title: str
    chapter_description: str


# ============================================================================
# Pydantic 응답 모델 (Response Models)
# ============================================================================
# API 응답의 구조를 정의하여 클라이언트가 예상할 수 있는 형태 보장

class ConceptResponse(BaseModel):
    """
    개념 학습 콘텐츠 응답 모델
    
    Attributes:
        title (str): 개념의 제목
            예: "리스트란?"
        description (str): 개념에 대한 간단한 설명
        contents (str): 상세 개념 설명 (Markdown 형식)
            1000-1200 단어 분량의 교육 콘텐츠
    """
    title: str
    description: str
    contents: str


class ExerciseResponse(BaseModel):
    """
    실습 과제 응답 모델
    
    Attributes:
        title (str): 실습 과제의 제목
            예: "리스트 조작 실습"
        description (str): 실습 과제에 대한 간단한 설명
        contents (str): 실습 과제 상세 내용 (Markdown 형식)
            약 3개의 실습 문제 포함
    """
    title: str
    description: str
    contents: str


class QuizItem(BaseModel):
    """
    개별 퀴즈 문제 모델 (주관식 - 심화 학습용)
    """
    quiz: str

class MultipleChoiceQuizItem(BaseModel):
    """
    객관식 퀴즈 문제 모델
    """
    question: str
    options: List[str]
    answer: str
    explanation: str

class QuizResponse(BaseModel):
    """
    객관식 퀴즈 응답 모델
    """
    quizes: List[MultipleChoiceQuizItem]

class AdvancedLearningResponse(BaseModel):
    """
    심화 학습(주관식 퀴즈) 응답 모델
    """
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
    advanced_learning: AdvancedLearningResponse


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


class QuizResultItem(BaseModel):
    id: int
    chapter_title: str
    score: int
    weak_points: str  # JSON string
    correct_points: Optional[str] = None # JSON string
    feedback: Optional[str] = None
    user_answer: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class QuizResultListResponse(BaseModel):
    results: List[QuizResultItem]


# 메인 API 엔드포인트

@app.post("/generate-objectives", response_model=ObjectivesResponse)
async def generate_objectives(request: StudyTopicRequest):
    """
    학습 주제에 대한 3가지 다른 학습 목표/방향을 제안합니다.
    
    사용자가 주제를 입력하면, AI가 3가지 다른 학습 경로를 제안합니다:
    1. 기초/기본: 기본 개념과 핵심 원리 중심
    2. 실무/프로젝트: 실전 활용과 프로젝트 중심
    3. 고급/이론: 심화 이론과 내부 동작 원리 중심
    
    Args:
        request (StudyTopicRequest): 학습 주제 요청 정보
            - topic: 학습하고 싶은 주제 (필수)
            - language: 출력 언어 (ko/en), 기본값 "ko"
    
    Returns:
        ObjectivesResponse: 3개의 학습 목표 목록
            - objectives: List[ObjectiveItem]
                - id: 목표 ID (1, 2, 3)
                - title: 목표 제목
                - description: 목표 설명
                - target_audience: 대상 학습자
    
    Raises:
        HTTPException:
            - 500: ContentGenerator가 초기화되지 않음
            - 500: AI 생성 실패 (API 오류, 네트워크 오류 등)
    
    Example:
        Request:
        {
            "topic": "파이썬 리스트",
            "language": "ko"
        }
        
        Response:
        {
            "objectives": [
                {
                    "id": 1,
                    "title": "파이썬 리스트 기초",
                    "description": "리스트의 기본 문법과 사용법",
                    "target_audience": "초보자"
                },
                ...
            ]
        }
    """
    # ContentGenerator 초기화 확인
    validate_generator_initialized(generator)

    try:
        logger.info(f"Received request to generate objectives for topic: '{request.topic}' (language: {request.language})")
        
        # AI를 통한 학습 목표 생성 (비동기)
        result = await generator.generate_learning_objectives(request.topic, request.language)
        
        # 응답 검증
        if not result or "objectives" not in result:
            logger.error("Invalid response format from generate_learning_objectives")
            raise HTTPException(
                status_code=500,
                detail="학습 목표 생성 응답 형식이 올바르지 않습니다"
            )
        
        return ObjectivesResponse(**result)
        
    except HTTPException:
        # HTTPException은 그대로 전파
        raise
    except ValueError as ve:
        # 검증 에러는 사용자 친화적인 메시지로 변환
        logger.error(f"Validation error in generate_objectives: {ve}")
        raise HTTPException(
            status_code=500,
            detail=f"학습 목표 생성 중 검증 오류가 발생했습니다: {str(ve)}"
        )
    except Exception as error:
        # 기타 모든 에러는 에러 처리 헬퍼 함수 사용
        error_type = type(error).__name__
        logger.error(f"Unexpected error in generate_objectives ({error_type}): {error}", exc_info=True)
        raise handle_generation_error("학습 목표 제안", error)


@app.post("/generate-course", response_model=CourseResponse)
async def generate_course_only(request: StudyTopicRequest, db: Session = Depends(get_db)):
    """
    1단계: 커리큘럼(목차)만 먼저 생성합니다.
    
    전체 콘텐츠를 한 번에 생성하는 것보다 빠르게 커리큘럼만 먼저 생성하여
    사용자가 구조를 확인하고 선택할 수 있도록 합니다.
    
    프로세스:
    1. AI를 통해 커리큘럼 생성 (챕터 목록)
    2. 데이터베이스에 코스 및 챕터 정보 저장
    3. 생성된 커리큘럼 반환
    
    Args:
        request (StudyTopicRequest): 학습 주제 요청 정보
            - topic: 학습 주제 (필수)
            - difficulty: 난이도 (초급/중급/고급)
            - max_chapters: 최대 챕터 수
            - selected_objective: 선택된 학습 목표 (선택사항)
            - language: 출력 언어
        db (Session): 데이터베이스 세션 (FastAPI 의존성 주입)
    
    Returns:
        CourseResponse: 생성된 커리큘럼 정보
            - course:
                - id: 데이터베이스에 저장된 코스 ID
                - topic: 코스 제목
                - description: 코스 설명
                - level: 난이도
                - chapters: 챕터 목록
                    - chapterId: 챕터 ID
                    - chapterTitle: 챕터 제목
                    - chapterDescription: 챕터 설명
    
    Raises:
        HTTPException:
            - 500: ContentGenerator 초기화 실패
            - 500: AI 생성 실패
            - 500: 데이터베이스 저장 실패 (경고만 로깅, 응답은 계속 진행)
    
    Note:
        - 데이터베이스 저장 실패 시에도 응답은 반환됩니다 (로깅만 수행)
        - 실제 챕터 콘텐츠는 /generate-chapter-content 엔드포인트에서 생성됩니다
    
    Example:
        Request:
        {
            "topic": "파이썬 리스트",
            "difficulty": "중급",
            "max_chapters": 3,
            "selected_objective": "실무 응용"
        }
        
        Response:
        {
            "course": {
                "id": 1,
                "topic": "파이썬 리스트",
                "chapters": [
                    {
                        "chapterId": 1,
                        "chapterTitle": "리스트 기초",
                        "chapterDescription": "리스트 생성과 기본 연산"
                    },
                    ...
                ]
            }
        }
    """
    # ContentGenerator 초기화 확인
    validate_generator_initialized(generator)

    try:
        # 설명이 없으면 주제를 설명으로 사용
        course_description = request.course_description or request.topic
        
        # AI를 통한 커리큘럼 생성
        result = await generator.generate_course(
            topic=request.topic,
            description=course_description,
            difficulty=request.difficulty,
            max_chapters=request.max_chapters,
            selected_objective=request.selected_objective,
            language=request.language
        )
        
        # 데이터베이스에 저장 (헬퍼 함수 사용 - 중복 제거)
        course_id = save_course_to_db(
            db=db,
            topic=request.topic,
            description=course_description,
            difficulty=request.difficulty,
            chapters_data=result["course"]["chapters"]
        )
        
        # 저장 성공 시 ID 반영 (실패해도 응답은 반환)
        if course_id:
            result["course"]["id"] = course_id
            
        return CourseResponse(**result)
    except HTTPException:
        raise
    except Exception as error:
        raise handle_generation_error("커리큘럼 생성", error)


@app.post("/generate-chapter-content", response_model=ChapterContent)
async def generate_chapter_content_only(request: ChapterRequest, db: Session = Depends(get_db)):
    """
    2단계: 특정 챕터의 상세 내용(개념, 실습, 퀴즈)을 생성합니다.
    
    사용자가 챕터를 클릭했을 때 호출되는 엔드포인트입니다.
    개념 설명, 실습 과제, 퀴즈 문제를 병렬로 생성하여 성능을 최적화합니다.
    
    캐싱 전략:
    1. 메모리 캐시 확인 (가장 빠름)
    2. 없으면 AI 생성 (개념, 실습, 퀴즈 병렬 처리)
    3. 생성 후 메모리 캐시 및 데이터베이스에 저장
    
    Args:
        request (ChapterRequest): 챕터 콘텐츠 생성 요청
            - course_title: 코스 제목
            - course_description: 코스 설명
            - chapter_title: 챕터 제목
            - chapter_description: 챕터 설명
        db (Session): 데이터베이스 세션
    
    Returns:
        ChapterContent: 챕터의 전체 콘텐츠
            - chapter: 챕터 기본 정보
            - concept: 개념 설명 (Markdown)
            - exercise: 실습 과제 (Markdown)
            - quiz: 퀴즈 문제 목록
    
    Raises:
        HTTPException:
            - 500: ContentGenerator 초기화 실패
            - 500: 개념/실습/퀴즈 생성 중 하나라도 실패
    
    Performance:
        - 개념, 실습, 퀴즈를 asyncio.gather로 병렬 생성
        - 캐시 히트 시 즉시 반환 (AI 호출 없음)
        - 학습 컨텍스트(최근 퀴즈 결과, 피드백)를 활용한 개인화
    
    Example:
        Request:
        {
            "course_title": "파이썬 리스트",
            "course_description": "파이썬 리스트 마스터하기",
            "chapter_title": "리스트 기초",
            "chapter_description": "리스트 생성과 기본 연산"
        }
        
        Response:
        {
            "chapter": {...},
            "concept": {
                "title": "리스트란?",
                "description": "...",
                "contents": "# 리스트란?\n\n..."
            },
            "exercise": {...},
            "quiz": {
                "quizes": [
                    {"quiz": "리스트와 튜플의 차이점은?"},
                    ...
                ]
            }
        }
    """
    # ContentGenerator 초기화 확인
    validate_generator_initialized(generator)

    # 캐시 키 생성 (유틸리티 함수 사용 - 중복 제거)
    cache_key = create_chapter_cache_key(
        course_title=request.course_title,
        chapter_title=request.chapter_title,
        chapter_description=request.chapter_description
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

        # 4. 콘텐츠 생성 (병렬 실행)
        concept_task = generator.generate_concept(
            request.course_title, request.course_description,
            request.chapter_title, request.chapter_description,
            learning_context
        )
        exercise_task = generator.generate_exercise(
            request.course_title, request.course_description,
            request.chapter_title, request.chapter_description,
            learning_context
        )
        quiz_task = generator.generate_quiz(
            request.course_title, request.chapter_title,
            request.chapter_description, request.course_description,
            learning_context
        )
        advanced_task = generator.generate_advanced_learning(
            request.course_title, request.chapter_title,
            request.chapter_description, request.course_description,
            learning_context
        )

        # 모든 태스크 병렬 실행
        results = await asyncio.gather(concept_task, exercise_task, quiz_task, advanced_task, return_exceptions=True)

        concept_data, exercise_data, quiz_data, advanced_data = results

        # 에러 처리
        if isinstance(concept_data, Exception):
            logger.error(f"Concept generation failed: {concept_data}")
            concept_data = {"title": "Error", "description": "Failed to generate concept", "contents": "Error occurred."}
        
        if isinstance(exercise_data, Exception):
            logger.error(f"Exercise generation failed: {exercise_data}")
            exercise_data = {"title": "Error", "description": "Failed to generate exercise", "contents": "Error occurred."}
            
        if isinstance(quiz_data, Exception):
            logger.error(f"Quiz generation failed: {quiz_data}")
            quiz_data = {"quizes": []}

        if isinstance(advanced_data, Exception):
            logger.error(f"Advanced learning generation failed: {advanced_data}")
            advanced_data = {"title": "Error", "description": "Failed to generate advanced learning", "contents": "Error occurred."}

        logger.info(f"챕터 콘텐츠 생성 완료: {request.chapter_title}")

        # 5. 응답 생성
        result = ChapterContent(
            chapter=Chapter(
                chapterId=0,  # 임시 ID (실제 DB 연동 시 변경)
                chapterTitle=request.chapter_title,
                chapterDescription=request.chapter_description
            ),
            concept=ConceptResponse(**concept_data),
            exercise=ExerciseResponse(**exercise_data),
            quiz=QuizResponse(**quiz_data),
            advanced_learning=AdvancedLearningResponse(**advanced_data)
        )

        # 캐시에 저장
        chapter_cache[cache_key] = result
        logger.debug(f"캐시에 저장: {request.chapter_title}")
        
        # DB에 저장 (헬퍼 함수 사용 - 중복 제거 및 가독성 향상)
        save_chapter_content_to_db(
            db=db,
            course_title=request.course_title,
            chapter_title=request.chapter_title,
            concept_data=concept_data,
            exercise_data=exercise_data,
            quiz_data=quiz_data
        )

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

## ❓ 퀴즈 (객관식)

"""

    for idx, quiz_item in enumerate(content.quiz.quizes, 1):
        markdown += f"### 문제 {idx}. {quiz_item.question}\n\n"
        for opt in quiz_item.options:
            markdown += f"- {opt}\n"
        markdown += f"\n**정답:** {quiz_item.answer}\n\n"
        markdown += f"**해설:** {quiz_item.explanation}\n\n---\n\n"

    markdown += "## 📝 심화 학습 (주관식)\n\n"
    for idx, adv_item in enumerate(content.advanced_learning.quizes, 1):
        markdown += f"### 심화 문제 {idx}\n\n{adv_item.quiz}\n\n---\n\n"

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
    
    사용자가 작성한 주관식 답안을 AI가 평가하여 점수와 피드백을 제공합니다.
    채점 결과는 데이터베이스에 저장되어 학습 컨텍스트로 활용됩니다.
    """
    # ContentGenerator 초기화 확인
    validate_generator_initialized(generator)

    try:
        # AI 채점 수행
        grading_result = await generator.grade_quiz(
            question=request.question,
            answer=request.answer,
            chapter_title=request.chapter_title,
            chapter_desc=request.chapter_description
        )

        # 채점 결과를 DB에 저장 (에러 발생해도 응답은 반환)
        try:
            quiz_result = QuizResult(
                chapter_title=request.chapter_title,
                score=grading_result.get("score", 0),
                weak_points=json.dumps(grading_result.get("improvements", []), ensure_ascii=False),
                correct_points=json.dumps(grading_result.get("correct_points", []), ensure_ascii=False),
                feedback=grading_result.get("feedback", ""),
                user_answer=request.answer,
                timestamp=datetime.now(timezone.utc)
            )
            db.add(quiz_result)
            db.commit()
            logger.info(f"퀴즈 채점 결과 저장 완료: {request.chapter_title}")
        except Exception as db_error:
            logger.error(f"퀴즈 채점 결과 저장 실패: {db_error}", exc_info=True)
            db.rollback()

        return grading_result
    except HTTPException:
        raise
    except Exception as error:
        raise handle_generation_error("퀴즈 채점", error)


@app.post("/feedback")
def submit_feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    """
    사용자 피드백을 저장합니다.
    
    사용자가 챕터에 대한 평가(평점, 코멘트)를 제출하면 데이터베이스에 저장합니다.
    저장된 피드백은 향후 학습 컨텍스트로 활용되어 개인화된 콘텐츠 생성에 사용됩니다.
    
    Args:
        request (FeedbackRequest): 피드백 요청
            - chapter_title: 챕터 제목
            - rating: 평점 (1-5)
            - comment: 코멘트 (선택사항)
        db (Session): 데이터베이스 세션
    
    Returns:
        dict: 저장 결과
            - status: "success"
            - message: "Feedback saved"
    
    Raises:
        HTTPException:
            - 500: 데이터베이스 저장 실패
    
    Example:
        Request:
        {
            "chapter_title": "리스트 기초",
            "rating": 5,
            "comment": "매우 유용했습니다!"
        }
        
        Response:
        {
            "status": "success",
            "message": "Feedback saved"
        }
    """
    try:
        feedback = UserFeedback(
            chapter_title=request.chapter_title,
            rating=request.rating,
            comment=request.comment,
            timestamp=datetime.now(timezone.utc)
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
    
@app.get("/quiz-results", response_model=QuizResultListResponse)
def get_quiz_results(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """
    사용자의 퀴즈 채점 결과 목록을 조회합니다.
    """
    results = db.query(QuizResult).order_by(QuizResult.timestamp.desc()).offset(skip).limit(limit).all()
    return {"results": results}
    created_at: str
    chapter_count: int
    completed_chapters: int
    progress: int

@app.get("/courses", response_model=List[CourseListItem])
def get_courses(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """
    저장된 코스 목록을 조회합니다.
    
    대시보드에서 사용자의 모든 코스를 표시하기 위해 호출됩니다.
    각 코스의 진행률, 완료된 챕터 수 등 통계 정보도 함께 제공합니다.
    
    Args:
        skip (int): 건너뛸 레코드 수 (페이지네이션용), 기본값 0
        limit (int): 반환할 최대 레코드 수, 기본값 20
        db (Session): 데이터베이스 세션
    
    Returns:
        List[CourseListItem]: 코스 목록
            각 항목은 다음 정보 포함:
            - id: 코스 ID
            - topic: 코스 제목
            - description: 코스 설명
            - level: 난이도 (초급/중급/고급)
            - created_at: 생성일시 (ISO 형식)
            - chapter_count: 전체 챕터 수
            - completed_chapters: 완료된 챕터 수
            - progress: 진행률 (0-100)
    
    Raises:
        HTTPException: 없음 (빈 리스트 반환 가능)
    
    Note:
        - 진행률은 (완료된 챕터 수 / 전체 챕터 수) * 100으로 계산됩니다
        - 챕터가 하나도 없으면 진행률은 0입니다
    
    Example:
        Response:
        [
            {
                "id": 1,
                "topic": "파이썬 리스트",
                "description": "...",
                "level": "중급",
                "created_at": "2025-11-26T10:00:00",
                "chapter_count": 3,
                "completed_chapters": 1,
                "progress": 33
            },
            ...
        ]
    """
    # 코스 목록 조회
    courses = (
        db.query(DBCourse)
        .order_by(DBCourse.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    # 진행률 계산 및 응답 생성 (헬퍼 함수 사용 - 시간복잡도 개선)
    result = []
    for course in courses:
        total_chapters, completed_chapters, progress = calculate_course_progress(course.chapters)
        
        result.append(CourseListItem(
            id=course.id,
            topic=course.topic,
            description=course.description,
            level=course.level or "Unknown",
            created_at=course.created_at.isoformat(),
            chapter_count=total_chapters,
            completed_chapters=completed_chapters,
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
    
    # 챕터 리스트 생성 (리스트 컴프리헨션 사용 - 가독성 향상)
    chapters = [
        Chapter(
            chapterId=chapter.id,
            chapterTitle=chapter.title,
            chapterDescription=chapter.description
        )
        for chapter in db_course.chapters
    ]
        
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
    # 포트는 환경 변수 PORT에서 가져오며, 설정되지 않은 경우 기본값 8001 사용
    # 프로덕션 환경에서는 환경 변수로 포트를 관리하는 것을 권장합니다
    port = int(os.getenv("PORT", "8001"))
    host = os.getenv("HOST", "0.0.0.0")
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
