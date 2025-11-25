import os
import json
import re
import logging
import asyncio
import time
import google.generativeai as genai
from pathlib import Path
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from datetime import datetime

# DB imports
from sqlalchemy.orm import Session
from app.models import GenerationLog, QuizResult, UserFeedback
from app.database import SessionLocal

# RAG imports
try:
    from langchain_community.vectorstores import FAISS
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    FAISS = None
    GoogleGenerativeAIEmbeddings = None

try:
    from langchain_openai import OpenAIEmbeddings
    OPENAI_EMBEDDINGS_AVAILABLE = True
except ImportError:
    OPENAI_EMBEDDINGS_AVAILABLE = False
    OpenAIEmbeddings = None

load_dotenv()
logger = logging.getLogger("pop_pins_api")

class ContentGenerator:
    def __init__(self):
        self.model = None
        self.vector_store = None
        self.model_name = "gemini-2.5-flash"
        self.setup_gemini()
        self.setup_rag()

    def setup_gemini(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your_api_key_here":
            logger.error("GEMINI_API_KEY not set")
            raise ValueError("GEMINI_API_KEY environment variable is not set.")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(self.model_name)

    def setup_rag(self):
        use_rag = os.getenv("USE_RAG", "true").lower() == "true"
        if not use_rag or not RAG_AVAILABLE:
            self.vector_store = None
            return

        vector_db_path = os.getenv("VECTOR_DB_PATH", "../python_textbook_gemini_db_semantic")
        embedding_model = os.getenv("VECTOR_DB_EMBEDDING_MODEL", "gemini")

        try:
            db_path = Path(vector_db_path)
            if not db_path.exists():
                logger.warning(f"Vector DB not found at {db_path}")
                return

            if embedding_model == "gemini":
                api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
                embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=api_key)
            elif embedding_model == "openai" and OPENAI_EMBEDDINGS_AVAILABLE:
                api_key = os.getenv("OPENAI_API_KEY")
                embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=api_key)
            else:
                logger.warning(f"Unsupported or missing embedding model: {embedding_model}")
                return

            self.vector_store = FAISS.load_local(str(db_path), embeddings, allow_dangerous_deserialization=True)
            logger.info(f"RAG Vector DB loaded from {db_path}")
        except Exception as e:
            logger.error(f"Failed to load Vector DB: {e}")
            self.vector_store = None

    def _log_to_db(self, request_type: str, topic: str, prompt_context: str, generated_content: str, latency_ms: int):
        """Logs the generation event to the database."""
        try:
            db = SessionLocal()
            log_entry = GenerationLog(
                request_type=request_type,
                topic=topic,
                prompt_context=prompt_context,
                generated_content=generated_content,
                model_name=self.model_name,
                latency_ms=latency_ms,
                timestamp=datetime.utcnow()
            )
            db.add(log_entry)
            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"Failed to log to DB: {e}")

    def search_context(self, query: str, k: int = 3) -> str:
        if not self.vector_store:
            return ""
        try:
            docs = self.vector_store.similarity_search(query, k=k)
            if not docs: return ""
            
            context_parts = []
            for i, doc in enumerate(docs, 1):
                source = doc.metadata.get("file_name", "Unknown")
                content = doc.page_content[:500]
                context_parts.append(f"[참고 자료 {i} - 출처: {source}]\n{content}")
            return "\n\n".join(context_parts)
        except Exception as e:
            logger.error(f"RAG search failed: {e}")
            return ""

    def _clean_json(self, raw: str) -> dict:
        cleaned = raw.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                json_str = match.group()
                try:
                    return json.loads(json_str)
                except:
                    pass
            raise ValueError(f"Failed to parse JSON: {cleaned[:100]}...")

    def _extract_content(self, raw: str) -> dict:
        cleaned = raw.replace("```json", "").replace("```", "").strip()
        title_match = re.search(r'"title"\s*:\s*"([^"]*)"', cleaned)
        desc_match = re.search(r'"description"\s*:\s*"([^"]*)"', cleaned)
        
        title = title_match.group(1) if title_match else ""
        description = desc_match.group(1) if desc_match else ""
        
        contents = ""
        if '"contents"' in cleaned:
            parts = cleaned.split('"contents"')
            if len(parts) > 1:
                c_part = parts[1].strip()
                if c_part.startswith(":"): c_part = c_part[1:].strip()
                if c_part.startswith('"'): c_part = c_part[1:]
                last_quote = c_part.rfind('"')
                if last_quote > 0: c_part = c_part[:last_quote]
                contents = c_part.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"')
        
        return {"title": title, "description": description, "contents": contents}

    def get_learning_context(self, course_title: str) -> str:
        """Fetches recent quiz results and feedback for the course to build a learning context."""
        try:
            db = SessionLocal()
            # Get recent 3 quiz results for this course (assuming course_title is unique enough for now)
            # In a real app, we would filter by user_id and course_id
            # Here we filter by chapter_title that might contain the course topic or we rely on the fact that we store chapter_title
            # Wait, our models only have chapter_title. We need to be careful.
            # Ideally we should store course_title in QuizResult.
            # For now, let's fetch ALL recent results and filter or just fetch recent ones.
            # Let's assume the user is working on one course at a time or we just look at global recent performance.
            # Better: Let's fetch recent 5 results globally as a proxy for "User's recent state".
            
            recent_quizzes = db.query(QuizResult).order_by(QuizResult.timestamp.desc()).limit(3).all()
            recent_feedback = db.query(UserFeedback).order_by(UserFeedback.timestamp.desc()).limit(3).all()
            db.close()

            context_parts = []
            if recent_quizzes:
                context_parts.append("Recent Quiz Performance:")
                for q in recent_quizzes:
                    context_parts.append(f"- Chapter '{q.chapter_title}': Score {q.score}/100. Weak points: {q.weak_points}")
            
            if recent_feedback:
                context_parts.append("Recent User Feedback:")
                for f in recent_feedback:
                    context_parts.append(f"- Chapter '{f.chapter_title}': Rating {f.rating}/5. Comment: '{f.comment}'")
            
            if not context_parts:
                return ""
            
            return "\n".join(context_parts)
        except Exception as e:
            logger.error(f"Failed to get learning context: {e}")
            return ""

    async def generate_course(self, topic: str, description: str, difficulty: str, max_chapters: int) -> dict:
        start_time = time.time()
        course_description = description or topic
        search_query = f"{topic} {course_description} 커리큘럼"
        rag_context = self.search_context(search_query, k=3)

        prompt_parts = [
            f"Title: {topic}",
            f"Description: {course_description}",
            f"Prompt: {topic}에 대한 자습 과제를 생성해주세요.",
            f"MaxChapters: {max_chapters}",
            f"Links:",
            f"Difficulty: {difficulty}",
        ]
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

        response = self.model.generate_content(
            f"{system_message}\n\n{prompt}",
            generation_config=genai.types.GenerationConfig(temperature=0.7, max_output_tokens=4096)
        )
        
        result = self._clean_json(response.text)
        
        # Log to DB
        latency = int((time.time() - start_time) * 1000)
        self._log_to_db("course", topic, prompt, json.dumps(result, ensure_ascii=False), latency)
        
        return result

    async def generate_concept(self, course_title: str, course_desc: str, chapter_title: str, chapter_desc: str, learning_context: str = "") -> dict:
        start_time = time.time()
        search_query = f"{chapter_title} {chapter_desc} 개념 설명"
        rag_context = self.search_context(search_query, k=3)

        prompt_parts = [
            f"Course Title: {course_title}",
            f"Course Description: {course_desc}",
            f"Chapter Title: {chapter_title}",
            f"Chapter Description: {chapter_desc}",
        ]
        if learning_context:
            prompt_parts.append(f"\n[User Learning Context]\n{learning_context}\n(Please adapt the content difficulty and focus based on this context.)")

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

        response = self.model.generate_content(
            f"{system_message}\n\n{prompt}",
            generation_config=genai.types.GenerationConfig(temperature=0.7, max_output_tokens=8192)
        )
        
        result = self._extract_content(response.text)
        
        # Log to DB
        latency = int((time.time() - start_time) * 1000)
        self._log_to_db("concept", chapter_title, prompt, json.dumps(result, ensure_ascii=False), latency)

        return result

    async def generate_exercise(self, course_title: str, course_desc: str, chapter_title: str, chapter_desc: str, learning_context: str = "") -> dict:
        start_time = time.time()
        search_query = f"{chapter_title} {chapter_desc} 실습 연습"
        rag_context = self.search_context(search_query, k=3)

        prompt_parts = [
            f"Course Title: {course_title}",
            f"course Description: {course_desc}",
            f"Chapter Title: {chapter_title}",
            f"Chapter Description: {chapter_desc}",
        ]
        if learning_context:
            prompt_parts.append(f"\n[User Learning Context]\n{learning_context}\n(Please adapt the exercises based on the user's weak points and feedback.)")

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

        response = self.model.generate_content(
            f"{system_message}\n\n{prompt}",
            generation_config=genai.types.GenerationConfig(temperature=0.7, max_output_tokens=8192)
        )
        
        result = self._extract_content(response.text)
        
        # Log to DB
        latency = int((time.time() - start_time) * 1000)
        self._log_to_db("exercise", chapter_title, prompt, json.dumps(result, ensure_ascii=False), latency)

        return result

    async def generate_quiz(self, course_title: str, chapter_title: str, chapter_desc: str, course_prompt: str = "", learning_context: str = "") -> dict:
        start_time = time.time()
        search_query = f"{chapter_title} {chapter_desc} 퀴즈 문제"
        rag_context = self.search_context(search_query, k=3)

        prompt_parts = [
            f"Course Title: {course_title}",
            f"Chapter Title: {chapter_title}",
            f"Course Prompt: {course_prompt}",
        ]
        if learning_context:
            prompt_parts.append(f"\n[User Learning Context]\n{learning_context}\n(Please adapt the quiz difficulty and focus based on the user's performance.)")

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
    }
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

        response = self.model.generate_content(
            f"{system_message}\n\n{prompt}",
            generation_config=genai.types.GenerationConfig(temperature=0.7, max_output_tokens=8192)
        )
        
        result = self._clean_json(response.text)
        
        # Log to DB
        latency = int((time.time() - start_time) * 1000)
        self._log_to_db("quiz", chapter_title, prompt, json.dumps(result, ensure_ascii=False), latency)

        return result

    async def grade_quiz(self, question: str, answer: str, chapter_title: str, chapter_desc: str) -> dict:
        start_time = time.time()
        prompt = f"""다음은 학습 퀴즈 문제와 학생의 답안입니다.

**문제:**
{question}

**학생 답안:**
{answer}

**챕터 정보:**
- 제목: {chapter_title}
- 설명: {chapter_desc}

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

        response = self.model.generate_content(
            f"{system_message}\n\n{prompt}",
            generation_config=genai.types.GenerationConfig(temperature=0.3, max_output_tokens=4096)
        )
        
        result = self._clean_json(response.text)
        
        # Log to DB
        latency = int((time.time() - start_time) * 1000)
        self._log_to_db("grading", chapter_title, prompt, json.dumps(result, ensure_ascii=False), latency)

        return result
