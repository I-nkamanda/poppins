from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
import json
import re
import asyncio
import logging
from logging.handlers import RotatingFileHandler

# RAG 벡터 DB 관련 import
try:
    from langchain_community.vectorstores import FAISS
    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    FAISS = None
    GoogleGenerativeAIEmbeddings = None

# OpenAI 임베딩 지원 추가
try:
    from langchain_openai import OpenAIEmbeddings

    OPENAI_EMBEDDINGS_AVAILABLE = True
except ImportError:
    OPENAI_EMBEDDINGS_AVAILABLE = False
    OpenAIEmbeddings = None

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

# Gemini API 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY or GEMINI_API_KEY == "your_api_key_here":
    raise ValueError(
        "GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.\n"
        ".env 파일을 열어서 실제 Gemini API 키를 설정해주세요.\n"
        "API 키는 https://makersuite.google.com/app/apikey 에서 발급받을 수 있습니다."
    )

genai.configure(api_key=GEMINI_API_KEY)
# Gemini 모델: gemini-1.5-flash, gemini-1.5-pro, gemini-2.0-flash-exp 등 사용 가능
# 사용자가 요청한 2.5 flash는 아직 공식적으로 없으므로 2.0-flash-exp 또는 1.5-flash 사용
model = genai.GenerativeModel("gemini-2.5-flash")  # 또는 'gemini-2.0-flash-exp'

# RAG 벡터 DB 설정
VECTOR_DB_PATH = os.getenv(
    "VECTOR_DB_PATH",
    str(Path(__file__).parent.parent / "python_textbook_gemini_db_semantic"),
)
VECTOR_DB_EMBEDDING_MODEL = os.getenv(
    "VECTOR_DB_EMBEDDING_MODEL", "gemini"
)  # 벡터 DB 생성 시 사용한 임베딩 모델
USE_RAG = os.getenv("USE_RAG", "true").lower() == "true"  # RAG 사용 여부 (기본값: true)

# 벡터 DB 전역 변수
vector_store = None

# 챕터 콘텐츠 캐시 (메모리 기반, DB 없이)
# 키: (course_title, chapter_title, chapter_description) 튜플
# 값: ChapterContent 객체
chapter_cache = {}


# 요청 모델
class StudyTopicRequest(BaseModel):
    topic: str
    difficulty: Optional[str] = "중급"
    max_chapters: Optional[int] = 3
    course_description: Optional[str] = None


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


# RAG 벡터 DB 초기화 함수
def initialize_rag_vector_db():
    """RAG 벡터 DB를 초기화합니다."""
    global vector_store

    if not USE_RAG or not RAG_AVAILABLE:
        return None

    try:
        db_path = Path(VECTOR_DB_PATH)
        if not db_path.exists():
            logger.warning(f"벡터 DB를 찾을 수 없습니다: {db_path}")
            logger.warning(
                "RAG 기능이 비활성화됩니다. USE_RAG=false로 설정하거나 벡터 DB를 생성해주세요."
            )
            return None

        # 임베딩 모델 초기화 (벡터 DB 생성 시 사용한 것과 동일해야 함)
        if VECTOR_DB_EMBEDDING_MODEL == "gemini":
            # GEMINI_API_KEY를 사용 (GOOGLE_API_KEY도 확인)
            api_key = GEMINI_API_KEY or os.getenv("GOOGLE_API_KEY")
            if not api_key:
                logger.warning("GEMINI_API_KEY 또는 GOOGLE_API_KEY가 설정되지 않았습니다.")
                return None

            embeddings = GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004", google_api_key=api_key
            )
        elif VECTOR_DB_EMBEDDING_MODEL == "openai":
            if not OPENAI_EMBEDDINGS_AVAILABLE:
                logger.warning("langchain-openai 패키지가 필요합니다.")
                return None

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning("OPENAI_API_KEY가 설정되지 않았습니다.")
                return None

            # text-embedding-3-small 사용 (생성 시 사용한 모델과 동일)
            embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=api_key,
                max_retries=10,
            )
        else:
            logger.warning(f"지원하지 않는 임베딩 모델: {VECTOR_DB_EMBEDDING_MODEL}")
            return None

        # 벡터 DB 로드
        vector_store = FAISS.load_local(
            str(db_path), embeddings, allow_dangerous_deserialization=True
        )
        logger.info(f"RAG 벡터 DB 로드 완료: {db_path}")
        return vector_store

    except Exception as e:
        logger.error(f"벡터 DB 로드 실패: {e}")
        logger.warning("RAG 기능이 비활성화됩니다.")
        return None


def search_rag_context(query: str, k: int = 3) -> str:
    """
    RAG 벡터 DB에서 관련 컨텍스트를 검색합니다.

    Args:
        query: 검색 쿼리
        k: 반환할 문서 수

    Returns:
        검색된 컨텍스트를 포맷팅한 문자열
    """
    global vector_store

    if not vector_store:
        return ""

    try:
        # 유사 문서 검색
        docs = vector_store.similarity_search(query, k=k)

        if not docs:
            return ""

        # 컨텍스트 포맷팅
        context_parts = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("file_name", "Unknown")
            content = doc.page_content[:500]  # 최대 500자만 사용
            context_parts.append(f"[참고 자료 {i} - 출처: {source}]\n{content}")

        return "\n\n".join(context_parts)

    except Exception as e:
        logger.error(f"RAG 검색 실패: {e}")
        return ""


# 애플리케이션 시작 시 벡터 DB 초기화
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    if USE_RAG:
        initialize_rag_vector_db()


# JSON 파싱 헬퍼 함수
def clean_json_response(raw: str) -> dict:
    """JSON 응답에서 코드블록과 불필요한 부분 제거"""
    cleaned = raw
    # 코드블록 제거
    cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    # JSON 파싱
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # 불완전한 JSON 처리 시도 (잘린 경우)
        # 먼저 정규식으로 JSON 객체 추출
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            json_str = match.group()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # 불완전한 JSON인 경우 - 마지막 불완전한 항목 제거 후 재시도
                # "quizes" 배열이 잘린 경우 처리
                if '"quizes"' in json_str:
                    # 마지막 불완전한 quiz 항목 제거
                    # "quiz": "..." 뒤에 닫히지 않은 부분 찾기
                    json_str = re.sub(
                        r',\s*"quiz":\s*"[^"]*$', "", json_str, flags=re.MULTILINE
                    )
                    json_str = re.sub(r",\s*\{[^}]*$", "", json_str, flags=re.MULTILINE)
                    # 배열과 객체 닫기
                    if json_str.count("[") > json_str.count("]"):
                        json_str += "]"
                    if json_str.count("{") > json_str.count("}"):
                        json_str += "}"
                    try:
                        return json.loads(json_str)
                    except:
                        pass
        raise ValueError(f"JSON 파싱 실패: {cleaned[:200]}")


def extract_contents_from_json(raw: str) -> dict:
    """ConceptMaker/ExerciseMaker 응답에서 contents 추출"""
    cleaned = raw.replace("```json", "").replace("```", "").strip()

    # title, description 추출
    title_match = re.search(r'"title"\s*:\s*"([^"]*)"', cleaned)
    description_match = re.search(r'"description"\s*:\s*"([^"]*)"', cleaned)

    title = title_match.group(1) if title_match else ""
    description = description_match.group(1) if description_match else ""

    # contents 추출 (더 복잡한 처리)
    contents_part = cleaned.split('"contents"')[1] if '"contents"' in cleaned else ""
    if contents_part:
        contents_part = contents_part.strip()
        if contents_part.startswith(":"):
            contents_part = contents_part[1:].strip()
        if contents_part.startswith('"'):
            contents_part = contents_part[1:]

        # 마지막 따옴표 찾기
        last_quote = contents_part.rfind('"')
        if last_quote > 0:
            contents_part = contents_part[:last_quote]

        # 이스케이프 문자 복원
        contents = (
            contents_part.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"')
        )
    else:
        contents = ""

    return {"title": title, "description": description, "contents": contents}


# ConceptMaker - 개념 정리 생성
async def generate_concept(request: ChapterRequest) -> ConceptResponse:
    logger.info(f"개념 정리 생성 시작: {request.chapter_title}")
    # RAG 컨텍스트 검색
    search_query = f"{request.chapter_title} {request.chapter_description} 개념 설명"
    rag_context = search_rag_context(search_query, k=3)

    # 프롬프트 구성
    prompt_parts = [
        f"Course Title: {request.course_title}",
        f"Course Description: {request.course_description}",
        f"Chapter Title: {request.chapter_title}",
        f"Chapter Description: {request.chapter_description}",
    ]

    # RAG 컨텍스트가 있으면 추가
    if rag_context:
        prompt_parts.append(f"\n[참고 교재 자료]\n{rag_context}")

    prompt = "\n".join(prompt_parts)

    system_message = """당신은 JSON 응답 전용 AI입니다.

입력 데이터는 다음 형식으로 주어집니다:

	"courseTitle": "string",
	"courseDescription": "string",
	"chapterTitle": "string",
	"chapterDescription": "string"

작업:
You are an experienced educational content creator, skilled at transforming course details and specific prompts into comprehensive and well-structured self-study materials. Your goal is to generate 1000~1200 words worth of high-quality educational content in a markdown format that is easy for self-learners to understand. Use headings, subheadings, bullet points, etc. for easier understanding.
If reference materials are provided, use them to create accurate and comprehensive content that aligns with the reference materials.
output language: ko

출력 형식 (반드시 JSON):
{
  "title": "string",
  "description": "string",
  "contents": "string"
}

⚠️ 규칙:
- 반드시 위 JSON 구조만 출력하세요.
- 절대로 {"output": {...}} 또는 문자열(JSON string) 형태로 감싸지 마세요.
- 대화형 멘트, 설명, 사족 없이 오직 JSON 데이터만 출력하세요.
- "contents" 필드는 markdown 문서 본문으로 채우세요 .
⚠️ 출력 시 절대로 Markdown 코드블록(```json`, ``` 등)을 포함하지 마세요.
⚠️ 절대로 {"output": {...}} 형태로 감싸지 말고, 
오직 {"title": "...", "description": "...", "contents": "..."} 구조로만 출력하세요."""

    try:
        response = model.generate_content(
            f"{system_message}\n\n{prompt}",
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=8192,
            ),
        )

        result = extract_contents_from_json(response.text)
        logger.info(f"개념 정리 생성 완료: {request.chapter_title}")
        return ConceptResponse(**result)
    except Exception as e:
        logger.error(f"개념 정리 생성 실패: {request.chapter_title} - {e}")
        raise HTTPException(status_code=500, detail=f"개념 정리 생성 실패: {str(e)}")


# ExerciseMaker - 실습 과제 생성
async def generate_exercise(request: ChapterRequest) -> ExerciseResponse:
    logger.info(f"실습 과제 생성 시작: {request.chapter_title}")
    # RAG 컨텍스트 검색
    search_query = f"{request.chapter_title} {request.chapter_description} 실습 연습"
    rag_context = search_rag_context(search_query, k=3)

    # 프롬프트 구성
    prompt_parts = [
        f"Course Title: {request.course_title}",
        f"course Description: {request.course_description}",
        f"Chapter Title: {request.chapter_title}",
        f"Chapter Description: {request.chapter_description}",
    ]

    # RAG 컨텍스트가 있으면 추가
    if rag_context:
        prompt_parts.append(f"\n[참고 교재 자료]\n{rag_context}")

    prompt = "\n".join(prompt_parts)

    system_message = """당신은 JSON 응답 전용 AI입니다.

입력 데이터는 다음 형식으로 주어집니다:

	"courseTitle": "string",
	"courseDescription": "string",
	"chapterTitle": "string",
	"chapterDescription": "string"

작업:
You are an AI assistant specializing in education and personalized learning. Your task is to generate approximately three distinct, personalized self-study exercises. These exercises should focus on basic concepts relevant to the provided chapter ID, course title, course description, and the user's learning profile details. The output should be clearly structured, presenting each of the three exercises distinctly.
If reference materials are provided, use them to create exercises that align with the concepts covered in the reference materials.
# Step by Step instructions
1. Review the provided Chapter ID, Course Title, Course Description, and Prompt to understand the context and the learner's profile details.
2. Generate the first personalized self-study exercise, focusing on basic concepts relevant to the Chapter ID, Course Title, Course Description, and the chapter's description.
3. Generate the second personalized self-study exercise, ensuring it is distinct from the first and also focuses on basic concepts relevant to the Chapter ID, Course Title, Course Description, and the learner's profile details.
4. Generate the third personalized self-study exercise, ensuring it is distinct from the previous two and also focuses on basic concepts relevant to the Course Title, Course Description, Chapter title, and its description.
5. Review the three generated exercises. Are there approximately three distinct exercises? If not, go back to step 2 and adjust or regenerate the exercises as needed to meet the count and distinctness requirements.
6. Ensure each exercise is clearly structured and presented individually.
output language: ko


출력 형식 (반드시 JSON):
{
  "title": "string",
  "description": "string",
  "contents": "string"
}

⚠️ 규칙:
- 반드시 위 JSON 구조만 출력하세요.
- 절대로 {"output": {...}} 또는 문자열(JSON string) 형태로 감싸지 마세요.
- 대화형 멘트, 설명, 사족 없이 오직 JSON 데이터만 출력하세요.
- "contents" 필드는 markdown 문서 본문으로 채우세요 .
⚠️ 출력 시 절대로 Markdown 코드블록(```json`, ``` 등)을 포함하지 마세요.
⚠️ 절대로 {"output": {...}} 형태로 감싸지 말고, 
오직 {"title": "...", "description": "...", "contents": "..."} 구조로만 출력하세요."""

    try:
        response = model.generate_content(
            f"{system_message}\n\n{prompt}",
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=8192,
            ),
        )

        result = extract_contents_from_json(response.text)
        logger.info(f"실습 과제 생성 완료: {request.chapter_title}")
        return ExerciseResponse(**result)
    except Exception as e:
        logger.error(f"실습 과제 생성 실패: {request.chapter_title} - {e}")
        raise HTTPException(status_code=500, detail=f"실습 과제 생성 실패: {str(e)}")


# QuizMaker - 퀴즈 생성
async def generate_quiz(
    request: ChapterRequest, course_prompt: str = ""
) -> QuizResponse:
    logger.info(f"퀴즈 생성 시작: {request.chapter_title}")
    # RAG 컨텍스트 검색
    search_query = f"{request.chapter_title} {request.chapter_description} 퀴즈 문제"
    rag_context = search_rag_context(search_query, k=3)

    # 프롬프트 구성
    prompt_parts = [
        f"Course Title: {request.course_title}",
        f"Chapter Title: {request.chapter_title}",
        f"Course Prompt: {course_prompt}",
    ]

    # RAG 컨텍스트가 있으면 추가
    if rag_context:
        prompt_parts.append(f"\n[참고 교재 자료]\n{rag_context}")

    prompt = "\n".join(prompt_parts)

    system_message = """당신은 JSON 응답 전용 AI입니다.

입력 데이터는 다음 형식으로 주어집니다:

	"courseTitle": "string",
	"courseDescription": "string",
	"chapterTitle": "string",
	"chapterDescription": "string"

작업:
You are an expert quiz question generator, skilled at crafting subjective essay-type questions that provoke thoughtful responses. Your task is to generate three subjective essay-type quiz questions based on the provided course title, chapter title, and course prompt. The output must be a JSON array named `quizes`, containing three objects, each with a `quiz` (string) field.
If reference materials are provided, use them to create questions that test understanding of the key concepts covered in the reference materials.
# Step by Step instructions
1. Acknowledge the provided Course Title, Chapter Title, and Course Prompt.
2. Generate one subjective essay-type quiz question that is related to the Course Title, Chapter Title, and Course Prompt.
3. Review the question generated so far. If three questions have been generated, proceed to the next step. Otherwise, return to Step 2 and generate another question.
4. Format the three generated questions into a JSON array named `quizes`, where each question is an object with a `quiz` field.


출력 형식 (반드시 JSON):
{
  "quizes" : [
    {
      "quiz" : "string"
    },
    {
      "quiz" : "string"
    },
    {
      "quiz" : "string"
  ]
}

⚠️ 규칙:
- 반드시 위 JSON 구조만 출력하세요.
- 절대로 {"output": {...}} 또는 문자열(JSON string) 형태로 감싸지 마세요.
- 대화형 멘트, 설명, 사족 없이 오직 JSON 데이터만 출력하세요.
- "contents" 필드는 markdown 문서 본문으로 채우세요 .
⚠️ 출력 시 절대로 Markdown 코드블록(```json`, ``` 등)을 포함하지 마세요.
⚠️ 절대로 {"output": {...}} 형태로 감싸지 말고, 
오직 {"title": "...", "description": "...", "contents": "..."} 구조로만 출력하세요."""

    try:
        response = model.generate_content(
            f"{system_message}\n\n{prompt}",
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=8192,  # 퀴즈 증가
            ),
        )

        # 안전하게 텍스트 추출
        try:
            response_text = response.text
        except ValueError as text_error:
            if "finish_reason" in str(text_error) or "Part" in str(text_error):
                logger.warning(f"안전 필터에 의해 차단됨. 재시도 중: {request.chapter_title}")
                retry_prompt_parts = [
                    f"Course Title: {request.course_title}",
                    f"Chapter Title: {request.chapter_title}",
                    f"Course Prompt: {course_prompt}",
                    "",
                    "위 주제에 대한 주관식 서술형 퀴즈 문제를 3개 생성해주세요.",
                ]
                
                if rag_context:
                    retry_prompt_parts.append(f"\n[참고 교재 자료]\n{rag_context}")
                
                retry_prompt = "\n".join(retry_prompt_parts)

                response = model.generate_content(
                    f"{system_message}\n\n{retry_prompt}",
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.6,
                        max_output_tokens=8192,
                    ),
                )
                response_text = response.text
            else:
                raise

        result = clean_json_response(response_text)
        logger.info(f"퀴즈 생성 완료: {request.chapter_title}")
        return QuizResponse(**result)
    except ValueError as e:
        if "finish_reason" in str(e) or "Part" in str(e):
            logger.error(f"퀴즈 생성 실패: 안전 필터에 의해 차단됨 - {request.chapter_title}")
            raise Exception(f"퀴즈 생성 실패: 안전 필터에 의해 차단되었습니다.")
        raise
    except Exception as e:
        logger.error(f"퀴즈 생성 실패: {request.chapter_title} - {type(e).__name__}: {e}", exc_info=True)
        raise Exception(f"퀴즈 생성 실패: {str(e)}")


# CourseMaker - 강의 커리큘럼 생성
async def generate_course(request: StudyTopicRequest) -> CourseResponse:
    course_description = request.course_description or request.topic

    # RAG 컨텍스트 검색 (커리큘럼 생성 시에도 참고)
    search_query = f"{request.topic} {course_description} 커리큘럼"
    rag_context = search_rag_context(search_query, k=3)

    # 프롬프트 구성
    prompt_parts = [
        f"Title: {request.topic}",
        f"Description: {course_description}",
        f"Prompt: {request.topic}에 대한 자습 과제를 생성해주세요.",
        f"MaxChapters: {request.max_chapters}",
        f"Links:",
        f"Difficulty: {request.difficulty}",
    ]

    # RAG 컨텍스트가 있으면 추가
    if rag_context:
        prompt_parts.append(f"\n[참고 교재 자료]\n{rag_context}")

    prompt = "\n".join(prompt_parts)

    system_message = """당신은 JSON 응답 전용 AI입니다.

입력 데이터는:
{
	"courseTitle" : string // 제목
	"courseDescription" : string // 학습 주제
	"prompt" : string // 본인 제약 상황(프롬프트)
	"maxchapters" : number // 최대 코스 개수
	"link" : string[] // 관련 링크 
	"difficulty": any // 난이도
}
형식으로 되어 있어.

작업:
You are an expert course designer and curriculum developer, skilled in creating comprehensive and tailored learning experiences. Your task is to generate a customized course syllabus in a structured JSON format. The syllabus should include a unique course ID and a list of chapters, where each chapter has its own ID, title, and description. You must use all provided course details, learner characteristics, maximum units, learning intensity, and any reference materials to create a comprehensive and tailored syllabus.
If reference materials are provided, use them to structure the course chapters in a logical learning progression that aligns with the content covered in the reference materials.
# Step by Step instructions
1. Create a unique Course ID (must be integer) for the syllabus.
2. Based on the courseTitle, courseDescription, prompts, maxchapters, and difficulty, generate the title and description for the first chapter.
3. based on link, get information from the URL provided and extract all contents from the page. Return the entire website contents if possible. If there is no URL in link, , do not return error and use Course Description to search the web and get contents from the promising search results.
3. Assign a unique ID to the chapter.
4. Check if the number of generated chapters has reached the Max Units. If not, go back to step 2 to generate the next chapter, ensuring progress towards the Max Units.




응답 형식:
{
	"course": {
		"id": number;
		"chapters": [
			{
				"chapterId" : number
				"chapterTitle": string
				"chapterDescription" : string					
			},
			{
				...
			}
		]
	} 
}

규칙:
You are working as part of an AI system, so no chit-chat and no explaining what you're doing and why.
DO NOT start with "Okay", or "Alright" or any preambles. Just the output, please."""

    try:
        response = model.generate_content(
            f"{system_message}\n\n{prompt}",
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=4096,
            ),
        )

        result = clean_json_response(response.text)
        return CourseResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"강의 커리큘럼 생성 실패: {str(e)}"
        )


# 메인 API 엔드포인트
# --- Lazy Loading을 위한 분리된 엔드포인트 ---


@app.post("/generate-course", response_model=CourseResponse)
async def generate_course_only(request: StudyTopicRequest):
    """
    1단계: 커리큘럼(목차)만 먼저 생성합니다. (빠름)
    """
    try:
        return await generate_course(request)
    except Exception as e:
        logger.error(f"커리큘럼 생성 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"커리큘럼 생성 실패: {str(e)}")


@app.post("/generate-chapter-content", response_model=ChapterContent)
async def generate_chapter_content_only(request: ChapterRequest):
    """
    2단계: 특정 챕터의 상세 내용(개념, 실습, 퀴즈)을 생성합니다. (챕터 클릭 시 호출)
    캐시에 있으면 재사용, 없으면 생성 후 캐시에 저장
    """
    # 캐시 키 생성
    cache_key = (
        request.course_title,
        request.chapter_title,
        request.chapter_description,
    )

    # 캐시 확인
    if cache_key in chapter_cache:
        logger.info(f"캐시에서 로드: {request.chapter_title}")
        return chapter_cache[cache_key]

    logger.info(f"챕터 콘텐츠 생성 시작: {request.chapter_title}")
    try:
        # 병렬로 생성 (개념, 실습, 퀴즈) - 에러를 개별적으로 처리
        results = await asyncio.gather(
            generate_concept(request),
            generate_exercise(request),
            generate_quiz(
                request, request.course_title
            ),  # course_title을 topic으로 사용
            return_exceptions=True,
        )

        # 각 결과 확인 및 에러 처리
        concept, exercise, quiz = results

        if isinstance(concept, Exception):
            logger.error(f"개념 생성 실패: {request.chapter_title} - {concept}")
            raise HTTPException(
                status_code=500, detail=f"개념 정리 생성 실패: {str(concept)}"
            )
        if isinstance(exercise, Exception):
            logger.error(f"실습 생성 실패: {request.chapter_title} - {exercise}")
            raise HTTPException(
                status_code=500, detail=f"실습 과제 생성 실패: {str(exercise)}"
            )
        if isinstance(quiz, Exception):
            logger.error(f"퀴즈 생성 실패: {request.chapter_title} - {quiz}")
            raise HTTPException(status_code=500, detail=f"퀴즈 생성 실패: {str(quiz)}")

        logger.info(f"챕터 콘텐츠 생성 완료: {request.chapter_title}")

        # Chapter 객체는 요청에서 재구성 (ID 등은 프론트엔드에서 관리한다고 가정하거나, 여기서 임시로 생성)
        # 여기서는 응답 모델을 맞추기 위해 더미 Chapter 객체를 만들거나,
        # 프론트엔드에서 Chapter 정보를 다 가지고 있으므로 Content만 리턴하는게 좋지만,
        # 기존 ChapterContent 구조를 재활용하기 위해 아래와 같이 구성

        # 주의: request에는 chapterId가 없을 수 있음.
        # 하지만 ChapterContent 모델은 Chapter 객체를 포함해야 함.
        # 편의상 request 정보를 바탕으로 Chapter 객체 생성
        chapter_info = Chapter(
            chapterId=0,  # ID는 프론트엔드 컨텍스트에 있음
            chapterTitle=request.chapter_title,
            chapterDescription=request.chapter_description,
        )

        result = ChapterContent(
            chapter=chapter_info, concept=concept, exercise=exercise, quiz=quiz
        )

        # 캐시에 저장
        chapter_cache[cache_key] = result
        logger.debug(f"캐시에 저장: {request.chapter_title}")

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
        course_response = await generate_course(request)
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

            # 병렬로 생성 (개념, 실습, 퀴즈)
            # asyncio.gather를 사용하여 3가지 요청을 동시에 보냄
            concept, exercise, quiz = await asyncio.gather(
                generate_concept(chapter_request),
                generate_exercise(chapter_request),
                generate_quiz(chapter_request, request.topic),
            )

            chapters_content.append(
                ChapterContent(
                    chapter=chapter, concept=concept, exercise=exercise, quiz=quiz
                )
            )

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
        # 없으면 생성 (generate_chapter_content_only 재사용)
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
async def grade_quiz(request: QuizGradingRequest):
    """
    퀴즈 답안을 AI로 채점합니다.
    """
    prompt = f"""다음은 학습 퀴즈 문제와 학생의 답안입니다.

**문제:**
{request.question}

**학생 답안:**
{request.answer}

**챕터 정보:**
- 제목: {request.chapter_title}
- 설명: {request.chapter_description}

위 답안을 채점하고 피드백을 제공해주세요. 다음 JSON 형식으로 응답해주세요:

{{
  "score": 0-100 사이의 점수,
  "feedback": "상세한 피드백 (한국어)",
  "correct_points": ["맞은 부분 1", "맞은 부분 2"],
  "improvements": ["개선할 점 1", "개선할 점 2"]
}}
"""

    system_message = """당신은 교육 전문가입니다. 학생의 답안을 공정하고 건설적으로 채점하고 피드백을 제공하세요.
점수는 0-100 사이로 주되, 답안의 완성도, 정확성, 이해도를 종합적으로 평가하세요.

⚠️ 중요: 반드시 완전한 JSON 형식으로 응답하세요. JSON이 잘리지 않도록 주의하세요.
반드시 다음 구조를 완전히 포함하세요:
{
  "score": 숫자,
  "feedback": "문자열",
  "correct_points": ["문자열 배열"],
  "improvements": ["문자열 배열"]
}"""

    try:
        response = model.generate_content(
            f"{system_message}\n\n{prompt}",
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,  # 채점은 일관성이 중요하므로 낮은 temperature
                max_output_tokens=4096,  # 긴 피드백을 위해 증가
            ),
        )

        # 안전하게 텍스트 추출
        try:
            response_text = response.text
        except ValueError as text_error:
            if "finish_reason" in str(text_error) or "Part" in str(text_error):
                logger.warning("안전 필터에 의해 차단됨. 재시도 중...")
                response = model.generate_content(
                    f"{system_message}\n\n{prompt}",
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.2,
                        max_output_tokens=4096,
                    ),
                )
                response_text = response.text
            else:
                raise

        result = clean_json_response(response_text)

        # 필수 필드 확인 및 기본값 설정
        if "correct_points" not in result:
            result["correct_points"] = []
        if "improvements" not in result:
            result["improvements"] = []
        if "score" not in result:
            result["score"] = 0
        if "feedback" not in result:
            result["feedback"] = "피드백을 생성할 수 없습니다."

        return result
    except Exception as e:
        logger.error(f"퀴즈 채점 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"퀴즈 채점 실패: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
