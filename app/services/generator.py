"""
PopPins II - AI 콘텐츠 생성 서비스

이 모듈은 Google Gemini API를 사용하여 교육 콘텐츠를 생성하는 핵심 서비스입니다.

주요 기능:
- 학습 목표 생성: 주제에 대한 3가지 학습 경로 제안
- 커리큘럼 생성: 코스의 챕터 구조 생성
- 개념 설명 생성: 상세한 개념 학습 자료 생성
- 실습 과제 생성: 실전 연습 문제 생성
- 퀴즈 생성: 주관식 서술형 문제 생성
- 퀴즈 채점: 사용자 답안 평가 및 피드백 제공
- RAG (Retrieval-Augmented Generation): 벡터 DB를 활용한 참고 자료 검색

기술 스택:
- Google Gemini API (gemini-2.5-flash)
- LangChain + FAISS (RAG 벡터 검색)
- SQLAlchemy (생성 이력 저장)

작성자: PopPins II 개발팀
버전: 1.0.0
"""
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
from datetime import datetime, timezone

# DB imports
from sqlalchemy.orm import Session
from app.models import GenerationLog, QuizResult, UserFeedback
from app.database import SessionLocal

# RAG imports (선택적 의존성)
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
    """
    AI 기반 교육 콘텐츠 생성기
    
    Google Gemini API를 사용하여 다양한 교육 콘텐츠를 생성합니다.
    RAG(Retrieval-Augmented Generation)를 통해 참고 자료를 활용한 고품질 콘텐츠 생성이 가능합니다.
    
    주요 기능:
    - 학습 목표 제안
    - 커리큘럼 생성
    - 개념/실습/퀴즈 콘텐츠 생성
    - 퀴즈 채점 및 피드백
    
    Attributes:
        model: Google Gemini GenerativeModel 인스턴스
        vector_store: FAISS 벡터 스토어 (RAG용, 선택적)
        model_name (str): 사용할 Gemini 모델 이름
        safety_settings (list): Gemini API 안전 설정
            모든 카테고리를 BLOCK_NONE으로 설정하여 콘텐츠 생성이 차단되지 않도록 함
    
    Example:
        generator = ContentGenerator()
        objectives = await generator.generate_learning_objectives("파이썬 리스트")
    """
    def __init__(self):
        """
        ContentGenerator 초기화
        
        Gemini API 설정 및 RAG 벡터 스토어 로드를 수행합니다.
        
        Raises:
            ValueError: GEMINI_API_KEY 환경 변수가 설정되지 않은 경우
        
        Note:
            - RAG는 선택적 기능이므로 로드 실패해도 계속 진행됩니다
            - 환경 변수 USE_RAG=false로 설정하면 RAG 비활성화
        """
        self.model = None
        self.vector_store = None
        self.model_name = "gemini-2.5-flash"
        self.setup_gemini()  # Gemini API 설정
        self.setup_rag()  # RAG 벡터 스토어 로드 (선택적)
        
        # Safety settings: 콘텐츠 생성이 안전 필터에 의해 차단되지 않도록 설정
        # finish_reason: 2 (SAFETY) 오류 방지
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

    def setup_gemini(self):
        """
        Google Gemini API 설정
        
        환경 변수에서 API 키를 읽어 Gemini 모델을 초기화합니다.
        
        Raises:
            ValueError: GEMINI_API_KEY가 설정되지 않았거나 기본값인 경우
        
        Note:
            API 키는 .env 파일에 GEMINI_API_KEY=your_actual_key 형식으로 저장해야 합니다
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your_api_key_here":
            error_msg = "GEMINI_API_KEY environment variable is not set or is set to default value"
            logger.error(error_msg)
            logger.error("Please set GEMINI_API_KEY in your .env file")
            raise ValueError(error_msg)
        
        # API 키 형식 기본 검증 (최소 길이 체크)
        if len(api_key.strip()) < 20:
            error_msg = "GEMINI_API_KEY appears to be invalid (too short)"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # Gemini API 설정
            genai.configure(api_key=api_key)
            # GenerativeModel 인스턴스 생성 (비동기 호출 지원)
            self.model = genai.GenerativeModel(self.model_name)
            logger.info(f"Gemini API configured successfully with model: {self.model_name}")
        except Exception as e:
            error_msg = f"Failed to configure Gemini API: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def setup_rag(self):
        """
        RAG (Retrieval-Augmented Generation) 벡터 스토어 설정
        
        사전에 구축된 벡터 데이터베이스를 로드하여 참고 자료 검색 기능을 활성화합니다.
        RAG를 통해 생성되는 콘텐츠의 정확성과 품질이 향상됩니다.
        
        환경 변수:
            USE_RAG: RAG 사용 여부 (true/false), 기본값 "true"
            VECTOR_DB_PATH: 벡터 DB 경로, 기본값 "../python_textbook_gemini_db_semantic"
            VECTOR_DB_EMBEDDING_MODEL: 임베딩 모델 (gemini/openai), 기본값 "gemini"
        
        Note:
            - RAG는 선택적 기능이므로 로드 실패해도 서비스는 계속 작동합니다
            - 벡터 DB가 없으면 RAG 없이 일반 생성 모드로 동작합니다
            - allow_dangerous_deserialization=True: 신뢰할 수 있는 소스의 벡터 DB만 로드해야 함
        """
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

            # 임베딩 모델 선택 (Gemini 또는 OpenAI)
            if embedding_model == "gemini":
                api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
                embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=api_key)
            elif embedding_model == "openai" and OPENAI_EMBEDDINGS_AVAILABLE:
                api_key = os.getenv("OPENAI_API_KEY")
                embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=api_key)
            else:
                logger.warning(f"Unsupported or missing embedding model: {embedding_model}")
                return

            # FAISS 벡터 스토어 로드
            self.vector_store = FAISS.load_local(str(db_path), embeddings, allow_dangerous_deserialization=True)
            logger.info(f"RAG Vector DB loaded from {db_path}")
        except Exception as e:
            logger.error(f"Failed to load Vector DB: {e}")
            self.vector_store = None  # RAG 없이 계속 진행

    def _log_to_db(self, request_type: str, topic: str, prompt_context: str, generated_content: str, latency_ms: int):
        """
        생성 이벤트를 데이터베이스에 기록합니다.
        
        모든 AI 콘텐츠 생성 요청을 로그로 저장하여 디버깅, 성능 분석, 사용 패턴 분석에 활용합니다.
        
        Args:
            request_type (str): 요청 타입
                가능한 값: "course", "concept", "exercise", "quiz", "objectives", "grading"
            topic (str): 주제/토픽
            prompt_context (str): 사용된 프롬프트/컨텍스트 (JSON 문자열)
            generated_content (str): 생성된 콘텐츠 (JSON 문자열)
            latency_ms (int): 생성 소요 시간 (밀리초)
        
        Note:
            - 로그 저장 실패해도 콘텐츠 생성은 계속 진행됩니다 (에러만 로깅)
            - 각 요청마다 새로운 DB 세션을 생성하여 사용
        """
        try:
            db = SessionLocal()
            log_entry = GenerationLog(
                request_type=request_type,
                topic=topic,
                prompt_context=prompt_context,
                generated_content=generated_content,
                model_name=self.model_name,
                latency_ms=latency_ms,
                timestamp=datetime.now(timezone.utc)
            )
            db.add(log_entry)
            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"Failed to log to DB: {e}")

    async def search_context(self, query: str, k: int = 3) -> str:
        """
        RAG를 사용하여 관련 참고 자료를 검색합니다.
        
        벡터 유사도 검색을 통해 쿼리와 관련된 문서를 찾아 반환합니다.
        검색된 자료는 프롬프트에 포함되어 더 정확하고 품질 높은 콘텐츠 생성에 활용됩니다.
        
        Args:
            query (str): 검색 쿼리
                예: "파이썬 리스트 커리큘럼", "리스트 기초 개념 설명"
            k (int): 반환할 문서 수, 기본값 3
                상위 k개의 유사한 문서를 반환
        
        Returns:
            str: 검색된 참고 자료를 포맷팅한 문자열
                형식: "[참고 자료 1 - 출처: 파일명]\n내용...\n\n[참고 자료 2 - ...]"
                검색 결과가 없거나 RAG가 비활성화된 경우 빈 문자열 반환
        
        Note:
            - FAISS는 동기 함수이므로 thread pool에서 실행하여 비동기로 처리
            - 검색 실패 시 빈 문자열 반환 (콘텐츠 생성은 계속 진행)
            - 각 문서의 내용은 500자로 제한하여 프롬프트 길이 관리
        """
        if not self.vector_store:
            return ""  # RAG가 비활성화된 경우
        try:
            loop = asyncio.get_running_loop()
            # 동기 FAISS 검색을 thread pool에서 실행하여 비동기 처리
            docs = await loop.run_in_executor(None, lambda: self.vector_store.similarity_search(query, k=k))
            
            if not docs: 
                return ""  # 검색 결과 없음
            
            # 검색 결과를 프롬프트에 포함할 수 있는 형식으로 포맷팅
            context_parts = []
            for i, doc in enumerate(docs, 1):
                source = doc.metadata.get("file_name", "Unknown")  # 출처 파일명
                content = doc.page_content[:500]  # 내용은 500자로 제한
                context_parts.append(f"[참고 자료 {i} - 출처: {source}]\n{content}")
            return "\n\n".join(context_parts)
        except Exception as e:
            logger.error(f"RAG search failed: {e}")
            return ""  # 검색 실패해도 계속 진행

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

            return {"title": title, "description": description, "contents": contents}

    def _repair_json(self, json_str: str) -> dict:
        """Attempt to repair truncated JSON."""
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # Try closing quotes and braces
            try:
                return json.loads(json_str + '"}')
            except:
                try:
                    return json.loads(json_str + '"]}')
                except:
                    try:
                        return json.loads(json_str + '}')
                    except:
                        return None

    def _extract_content(self, raw: str) -> dict:
        """Extract content from Gemini response, handling both JSON and partial responses."""
        cleaned = raw.replace("```json", "").replace("```", "").strip()
        
        # Try proper JSON parsing first
        try:
            parsed = json.loads(cleaned)
            return {
                "title": parsed.get("title", ""),
                "description": parsed.get("description", ""),
                "contents": parsed.get("contents", "")
            }
        except json.JSONDecodeError:
            # Attempt to repair if truncated
            repaired = self._repair_json(cleaned)
            if repaired:
                 return {
                    "title": repaired.get("title", ""),
                    "description": repaired.get("description", ""),
                    "contents": repaired.get("contents", "")
                }

            # Fallback: Try to extract JSON object
            try:
                match = re.search(r'\{.*\}', cleaned, re.DOTALL)
                if match:
                    parsed = json.loads(match.group())
                    return {
                        "title": parsed.get("title", ""),
                        "description": parsed.get("description", ""),
                        "contents": parsed.get("contents", "")
                    }
            except:
                pass
            
            # Last resort: manual extraction for malformed JSON
            title_match = re.search(r'"title"\s*:\s*"([^"]*)"', cleaned)
            desc_match = re.search(r'"description"\s*:\s*"([^"]*)"', cleaned)
            
            title = title_match.group(1) if title_match else ""
            description = desc_match.group(1) if desc_match else ""
            
            # For contents, find the content between "contents": and the last }
            contents = ""
            if '"contents"' in cleaned:
                # Find where contents starts
                contents_start = cleaned.find('"contents"')
                if contents_start != -1:
                    # Find the colon after "contents"
                    colon_pos = cleaned.find(':', contents_start)
                    if colon_pos != -1:
                        # Skip whitespace and opening quote
                        content_start = colon_pos + 1
                        while content_start < len(cleaned) and cleaned[content_start] in ' \t\n\r':
                            content_start += 1
                        if content_start < len(cleaned) and cleaned[content_start] == '"':
                            content_start += 1
                            # Find the last quote before the final }
                            # We need to be careful about escaped quotes
                            content_end = cleaned.rfind('"', content_start, cleaned.rfind('}'))
                            if content_end > content_start:
                                contents = cleaned[content_start:content_end]
                                # Unescape
                                contents = contents.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
            
            return {"title": title, "description": description, "contents": contents}

    def get_learning_context(self, course_title: str) -> str:
        """
        최근 퀴즈 결과와 피드백을 조회하여 학습 컨텍스트를 생성합니다.
        
        Args:
            course_title: 코스 제목 (현재는 사용하지 않지만 향후 필터링에 활용 가능)
        
        Returns:
            str: 학습 컨텍스트 문자열 (최근 성적, 약점, 피드백 포함)
        
        변경 이유:
            - 변수명 개선: q → quiz_result, f → feedback
            - 주석 정리 및 명확화
            - 에러 처리 개선
        """
        try:
            db = SessionLocal()
            
            # 최근 퀴즈 결과 조회 (전역 기준, 향후 course_id로 필터링 가능)
            recent_quiz_results = (
                db.query(QuizResult)
                .order_by(QuizResult.timestamp.desc())
                .limit(3)
                .all()
            )
            
            # 최근 피드백 조회
            recent_feedback_list = (
                db.query(UserFeedback)
                .order_by(UserFeedback.timestamp.desc())
                .limit(3)
                .all()
            )
            
            db.close()

            # 컨텍스트 문자열 생성
            context_parts = []
            
            if recent_quiz_results:
                context_parts.append("Recent Quiz Performance:")
                for quiz_result in recent_quiz_results:
                    weak_points = quiz_result.weak_points or "없음"
                    context_parts.append(
                        f"- Chapter '{quiz_result.chapter_title}': "
                        f"Score {quiz_result.score}/100. Weak points: {weak_points}"
                    )
            
            if recent_feedback_list:
                context_parts.append("Recent User Feedback:")
                for feedback in recent_feedback_list:
                    comment = feedback.comment or "없음"
                    context_parts.append(
                        f"- Chapter '{feedback.chapter_title}': "
                        f"Rating {feedback.rating}/5. Comment: '{comment}'"
                    )
            
            return "\n".join(context_parts) if context_parts else ""
            
        except Exception as error:
            logger.error(f"Failed to get learning context: {error}", exc_info=True)
            return ""  # 컨텍스트 없이도 콘텐츠 생성 가능

    async def generate_learning_objectives(self, topic: str, language: str = "ko") -> dict:
        start_time = time.time()
        
        if language == "ko":
            prompt = f"주제 '{topic}'에 대한 3가지 다른 학습 경로/목표를 제안해주세요."
            lang_instruction = "IMPORTANT: All output (titles, descriptions, target_audience) MUST be in Korean."
            example_title = "파이썬 기초"
            example_desc = "string (short description in Korean)"
            example_audience = "string (in Korean)"
        else:
            prompt = f"Suggest 3 distinct learning paths/objectives for the topic: '{topic}'."
            lang_instruction = "IMPORTANT: All output (titles, descriptions, target_audience) MUST be in English."
            example_title = "Python Basics"
            example_desc = "string (short description)"
            example_audience = "string"

        system_message = f"""You are an expert curriculum designer.
        Create 3 distinct learning paths for the given topic.
        1. Beginner/Foundational: Focus on basics and core concepts.
        2. Practical/Project-based: Focus on building things and hands-on practice.
        3. Advanced/Theoretical: Focus on deep dive, internal mechanics, and advanced usage.
        
        {lang_instruction}
        
        Output JSON format:
        {{
            "objectives": [
                {{
                    "id": 1,
                    "title": "string (e.g., '{example_title}')",
                    "description": "{example_desc}",
                    "target_audience": "{example_audience}"
                }},
                ...
            ]
        }}
        """

        
        max_retries = 3
        last_exception = None

        for attempt in range(max_retries):
            try:
                # API 키 재검증 (런타임에서 변경되었을 수 있음)
                if not self.model:
                    error_msg = "Gemini model is not initialized. ContentGenerator may have failed to initialize."
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                
                logger.info(f"Generating learning objectives for topic: '{topic}' (attempt {attempt + 1}/{max_retries})")
                
                response = await self.model.generate_content_async(
                    f"{system_message}\n\n{prompt}",
                    generation_config=genai.types.GenerationConfig(temperature=0.7, max_output_tokens=2048),
                    safety_settings=self.safety_settings
                )
                
                # 응답 검증
                if not response or not response.text:
                    raise ValueError("Empty response from Gemini API")
                
                result = self._clean_json(response.text)
                
                # 결과 검증
                if "objectives" not in result or not isinstance(result.get("objectives"), list):
                    raise ValueError(f"Invalid response format: missing 'objectives' field or not a list")
                
                if len(result.get("objectives", [])) == 0:
                    raise ValueError("No objectives returned in response")
                
                # Log to DB
                latency = int((time.time() - start_time) * 1000)
                self._log_to_db("objectives", topic, prompt, json.dumps(result, ensure_ascii=False), latency)
                
                logger.info(f"Successfully generated {len(result.get('objectives', []))} learning objectives")
                return result
                
            except ValueError as ve:
                # 검증 에러는 즉시 실패 (재시도 불필요)
                logger.error(f"Validation error in generate_learning_objectives: {ve}")
                raise ve
            except Exception as e:
                last_exception = e
                error_type = type(e).__name__
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed ({error_type}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)  # Async sleep before retry

        # 모든 재시도 실패
        error_summary = f"All {max_retries} attempts failed. Last error ({type(last_exception).__name__}): {last_exception}"
        logger.error(error_summary)
        logger.error("Possible causes:")
        logger.error("  1. Invalid or expired GEMINI_API_KEY")
        logger.error("  2. Network connectivity issues")
        logger.error("  3. Gemini API service unavailable")
        logger.error("  4. Rate limiting or quota exceeded")
        raise last_exception

    async def generate_course(self, topic: str, description: str, difficulty: str, max_chapters: int, selected_objective: str = "", language: str = "ko") -> dict:
        start_time = time.time()
        course_description = description or topic
        search_query = f"{topic} {course_description} 커리큘럼"
        rag_context = await self.search_context(search_query, k=3)
        
        lang_instruction = "IMPORTANT: All output (titles, descriptions) MUST be in Korean." if language == "ko" else "IMPORTANT: All output (titles, descriptions) MUST be in English."

        prompt_parts = [
            f"Title: {topic}",
            f"Description: {course_description}",
            f"Prompt: {topic}에 대한 자습 과제를 생성해주세요.",
            f"MaxChapters: {max_chapters}",
            f"Links:",
            f"Difficulty: {difficulty}",
        ]
        if selected_objective:
             prompt_parts.append(f"Selected Learning Objective: {selected_objective}\n(Please tailor the curriculum to match this specific objective.)")

        if rag_context:
            prompt_parts.append(f"\n[참고 교재 자료]\n{rag_context}")
        
        prompt = "\n".join(prompt_parts)
        
        system_message = f"""당신은 JSON 응답 전용 AI입니다.
입력 데이터는:
{{
	"courseTitle" : string // 제목
	"courseDescription" : string // 학습 주제
	"prompt" : string // 본인 제약 상황(프롬프트)
	"maxchapters" : number // 최대 코스 개수
	"link" : string[] // 관련 링크 
	"difficulty": any // 난이도
}}
형식으로 되어 있어.

작업:
You are an expert course designer and curriculum developer, skilled in creating comprehensive and tailored learning experiences. Your task is to generate a customized course syllabus in a structured JSON format. The syllabus should include a unique course ID and a list of chapters, where each chapter has its own ID, title, and description. You must use all provided course details, learner characteristics, maximum units, learning intensity, and any reference materials to create a comprehensive and tailored syllabus.
If reference materials are provided, use them to structure the course chapters in a logical learning progression that aligns with the content covered in the reference materials.

{lang_instruction}

# Step by Step instructions
1. Create a unique Course ID (must be integer) for the syllabus.
2. Based on the courseTitle, courseDescription, prompts, maxchapters, and difficulty, generate the title and description for the first chapter.
3. based on link, get information from the URL provided and extract all contents from the page. Return the entire website contents if possible. If there is no URL in link, , do not return error and use Course Description to search the web and get contents from the promising search results.
3. Assign a unique ID to the chapter.
4. Check if the number of generated chapters has reached the Max Units. If not, go back to step 2 to generate the next chapter, ensuring progress towards the Max Units.

응답 형식:
{{
	"course": {{
		"id": number;
		"chapters": [
			{{
				"chapterId" : number
				"chapterTitle": string
				"chapterDescription" : string					
			}},
			{{
				...
			}}
		]
	}} 
}}

규칙:
You are working as part of an AI system, so no chit-chat and no explaining what you're doing and why.
DO NOT start with "Okay", or "Alright" or any preambles. Just the output, please."""

        response = await self.model.generate_content_async(
            f"{system_message}\n\n{prompt}",
            generation_config=genai.types.GenerationConfig(temperature=0.7, max_output_tokens=4096),
            safety_settings=self.safety_settings
        )
        
        result = self._clean_json(response.text)
        
        # Log to DB
        latency = int((time.time() - start_time) * 1000)
        self._log_to_db("course", topic, prompt, json.dumps(result, ensure_ascii=False), latency)
        
        return result

    async def generate_concept(self, course_title: str, course_desc: str, chapter_title: str, chapter_desc: str, learning_context: str = "") -> dict:
        start_time = time.time()
        search_query = f"{chapter_title} {chapter_desc} 개념 설명"
        rag_context = await self.search_context(search_query, k=3)

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
You are an experienced educational content creator, skilled at transforming course details and specific prompts into comprehensive and well-structured self-study materials. Your goal is to generate 800~1000 words worth of high-quality educational content in a markdown format that is easy for self-learners to understand. Use headings, subheadings, bullet points, etc. for easier understanding.
IMPORTANT: Ensure the JSON response is complete and valid. Do not truncate the output. Prioritize finishing the JSON structure over exceeding the word count.
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

        response = await self.model.generate_content_async(
            f"{system_message}\n\n{prompt}",
            generation_config=genai.types.GenerationConfig(temperature=0.7, max_output_tokens=8192),
            safety_settings=self.safety_settings
        )
        
        result = self._extract_content(response.text)
        
        # Log to DB
        latency = int((time.time() - start_time) * 1000)
        self._log_to_db("concept", chapter_title, prompt, json.dumps(result, ensure_ascii=False), latency)

        return result

    async def generate_exercise(self, course_title: str, course_desc: str, chapter_title: str, chapter_desc: str, learning_context: str = "") -> dict:
        start_time = time.time()
        search_query = f"{chapter_title} {chapter_desc} 실습 연습"
        rag_context = await self.search_context(search_query, k=3)

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

        response = await self.model.generate_content_async(
            f"{system_message}\n\n{prompt}",
            generation_config=genai.types.GenerationConfig(temperature=0.7, max_output_tokens=8192),
            safety_settings=self.safety_settings
        )
        
        result = self._extract_content(response.text)
        
        # Log to DB
        latency = int((time.time() - start_time) * 1000)
        self._log_to_db("exercise", chapter_title, prompt, json.dumps(result, ensure_ascii=False), latency)

        return result

    async def generate_quiz(self, course_title: str, chapter_title: str, chapter_desc: str, course_prompt: str = "", learning_context: str = "") -> dict:
        """Generate 5 Multiple Choice Questions."""
        start_time = time.time()
        search_query = f"{chapter_title} {chapter_desc} 객관식 퀴즈"
        rag_context = await self.search_context(search_query, k=3)

        prompt_parts = [
            f"Course Title: {course_title}",
            f"Chapter Title: {chapter_title}",
            f"Course Prompt: {course_prompt}",
        ]
        if learning_context:
            prompt_parts.append(f"\n[User Learning Context]\n{learning_context}")

        if rag_context:
            prompt_parts.append(f"\n[참고 교재 자료]\n{rag_context}")

        prompt = "\n".join(prompt_parts)

        system_message = """당신은 JSON 응답 전용 AI입니다.
입력 데이터는 다음 형식으로 주어집니다:
	"courseTitle": "string",
	"chapterTitle": "string"

작업:
You are an expert quiz generator. Create 5 multiple-choice questions (4 options each) based on the chapter content.
Output must be a JSON object with a "quizes" array.
Each item in "quizes" must have:
- "question": string
- "options": array of 4 strings
- "answer": string (must be one of the options)
- "explanation": string (explanation of the correct answer)

output language: ko

출력 형식 (반드시 JSON):
{
  "quizes": [
    {
      "question": "string",
      "options": ["string", "string", "string", "string"],
      "answer": "string",
      "explanation": "string"
    },
    ... (5 items)
  ]
}

⚠️ 규칙:
- 반드시 위 JSON 구조만 출력하세요.
- 절대로 {"output": {...}} 또는 문자열(JSON string) 형태로 감싸지 마세요.
"""

        response = await self.model.generate_content_async(
            f"{system_message}\n\n{prompt}",
            generation_config=genai.types.GenerationConfig(temperature=0.7, max_output_tokens=8192),
            safety_settings=self.safety_settings
        )
        
        result = self._clean_json(response.text)
        
        # Log to DB
        latency = int((time.time() - start_time) * 1000)
        self._log_to_db("quiz", chapter_title, prompt, json.dumps(result, ensure_ascii=False), latency)

        return result

    async def generate_advanced_learning(self, course_title: str, chapter_title: str, chapter_desc: str, course_prompt: str = "", learning_context: str = "") -> dict:
        start_time = time.time()
        search_query = f"{chapter_title} {chapter_desc} 심화 학습 주관식 문제"
        rag_context = await self.search_context(search_query, k=3)

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
You are an expert educational content creator. Your task is to generate three subjective essay-type "Advanced Learning" questions that provoke thoughtful responses and deep understanding.
For each question, also provide a comprehensive model answer that demonstrates depth of understanding and critical thinking.
The output must be a JSON array named `quizes`, containing three objects, each with:
- `quiz` (string): The question
- `model_answer` (string): A detailed model answer (200-300 words in Korean)

output language: ko

출력 형식 (반드시 JSON):
{
  "quizes" : [
    {
      "quiz" : "string",
      "model_answer" : "string"
    },
    {
      "quiz" : "string",
      "model_answer" : "string"
    },
    {
      "quiz" : "string",
      "model_answer" : "string"
    }
  ]
}

⚠️ 규칙:
- 반드시 위 JSON 구조만 출력하세요.
- 절대로 {"output": {...}} 또는 문자열(JSON string) 형태로 감싸지 마세요.
- model_answer는 학습자가 스스로 답을 작성한 후 참고할 수 있는 모범적인 답안이어야 합니다.
"""

        response = await self.model.generate_content_async(
            f"{system_message}\n\n{prompt}",
            generation_config=genai.types.GenerationConfig(temperature=0.7, max_output_tokens=8192),
            safety_settings=self.safety_settings
        )
        
        result = self._clean_json(response.text)
        
        # Log to DB
        latency = int((time.time() - start_time) * 1000)
        self._log_to_db("advanced_learning", chapter_title, prompt, json.dumps(result, ensure_ascii=False), latency)

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

        response = await self.model.generate_content_async(
            f"{system_message}\n\n{prompt}",
            generation_config=genai.types.GenerationConfig(temperature=0.3, max_output_tokens=4096),
            safety_settings=self.safety_settings
        )
        
        result = self._clean_json(response.text)
        
        # Log to DB
        latency = int((time.time() - start_time) * 1000)
        self._log_to_db("grading", chapter_title, prompt, json.dumps(result, ensure_ascii=False), latency)

        return result
