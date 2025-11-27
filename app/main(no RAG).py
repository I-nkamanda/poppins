from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
from dotenv import load_dotenv
import google.generativeai as genai
import json
import re

load_dotenv()

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


# 요청 모델
class StudyTopicRequest(BaseModel): #클라이언트가 이런  JSON을 보내야 한다는 의미다.
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
class ConceptResponse(BaseModel): #API는 이런 식으로 응답하게 한다.
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


# JSON 파싱 헬퍼 함수
def clean_json_response(raw: str) -> dict:
    """JSON 응답에서 코드블록과 불필요한 부분 제거"""
    cleaned = raw
    # 코드블록 제거
    cleaned = cleaned.replace("```json", "").replace("```", "").strip()
    # JSON 파싱
    try:
        return json.loads(cleaned) #문자열을 python Dictionary로 변환
    except json.JSONDecodeError:
        # 실패 시 정규식으로 추출 시도
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
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
    prompt = f"""Course Title: {request.course_title}
Course Description: {request.course_description}

Chapter Title: {request.chapter_title}
Chapter Description: {request.chapter_description}"""

    system_message = """당신은 JSON 응답 전용 AI입니다.

입력 데이터는 다음 형식으로 주어집니다:

	"courseTitle": "string",
	"courseDescription": "string",
	"chapterTitle": "string",
	"chapterDescription": "string"

작업:
You are an experienced educational content creator, skilled at transforming course details and specific prompts into comprehensive and well-structured self-study materials. Your goal is to generate 1000~1200 words worth of high-quality educational content in a markdown format that is easy for self-learners to understand. Use headings, subheadings, bullet points, etc. for easier understanding.
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
        return ConceptResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"개념 정리 생성 실패: {str(e)}")


# ExerciseMaker - 실습 과제 생성
async def generate_exercise(request: ChapterRequest) -> ExerciseResponse:
    prompt = f"""Course Title: {request.course_title}
course Description: {request.course_description}

Chapter Title: {request.chapter_title}
Chapter Description: {request.chapter_description}"""

    system_message = """당신은 JSON 응답 전용 AI입니다.

입력 데이터는 다음 형식으로 주어집니다:

	"courseTitle": "string",
	"courseDescription": "string",
	"chapterTitle": "string",
	"chapterDescription": "string"

작업:
You are an AI assistant specializing in education and personalized learning. Your task is to generate approximately three distinct, personalized self-study exercises. These exercises should focus on basic concepts relevant to the provided chapter ID, course title, course description, and the user's learning profile details. The output should be clearly structured, presenting each of the three exercises distinctly.
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
        return ExerciseResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"실습 과제 생성 실패: {str(e)}")


# QuizMaker - 퀴즈 생성
async def generate_quiz(
    request: ChapterRequest, course_prompt: str = ""
) -> QuizResponse:
    prompt = f"""Course Title: {request.course_title}
Chapter Title: {request.chapter_title}
Course Prompt: {course_prompt}"""

    system_message = """당신은 JSON 응답 전용 AI입니다.

입력 데이터는 다음 형식으로 주어집니다:

	"courseTitle": "string",
	"courseDescription": "string",
	"chapterTitle": "string",
	"chapterDescription": "string"

작업:
You are an expert quiz question generator, skilled at crafting subjective essay-type questions that provoke thoughtful responses. Your task is to generate three subjective essay-type quiz questions based on the provided course title, chapter title, and course prompt. The output must be a JSON array named `quizes`, containing three objects, each with a `quiz` (string) field.
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
                max_output_tokens=2048,
            ),
        )

        result = clean_json_response(response.text)
        return QuizResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"퀴즈 생성 실패: {str(e)}")


# CourseMaker - 강의 커리큘럼 생성
async def generate_course(request: StudyTopicRequest) -> CourseResponse:
    course_description = request.course_description or request.topic
    prompt = f"""Title: {request.topic}
Description: {course_description}
Prompt: {request.topic}에 대한 자습 과제를 생성해주세요.
MaxChapters: {request.max_chapters}
Links: 
Difficulty: {request.difficulty}"""

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
@app.post("/generate-study-material", response_model=StudyMaterialResponse)
async def generate_study_material(request: StudyTopicRequest):
    """
    공부 주제를 입력받아 자습 과제를 생성합니다.

    - **topic**: 학습 주제 (필수)
    - **difficulty**: 난이도 (선택, 기본값: "중급")
    - **max_chapters**: 최대 챕터 수 (선택, 기본값: 3)
    - **course_description**: 강의 설명 (선택)
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
            concept = await generate_concept(chapter_request)
            exercise = await generate_exercise(chapter_request)
            quiz = await generate_quiz(chapter_request, request.topic)

            chapters_content.append(
                ChapterContent(
                    chapter=chapter, concept=concept, exercise=exercise, quiz=quiz
                )
            )

        return StudyMaterialResponse(course=course, chapters=chapters_content)
    except Exception as e:
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
