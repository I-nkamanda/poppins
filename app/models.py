"""
PopPins II - 데이터베이스 모델 정의

이 모듈은 SQLAlchemy를 사용하여 데이터베이스 테이블 구조를 정의합니다.

모델 목록:
- GenerationLog: AI 콘텐츠 생성 이력
- QuizResult: 퀴즈 채점 결과
- UserFeedback: 사용자 피드백
- Course: 코스 정보
- Chapter: 챕터 정보
- UserPreference: 사용자 학습 선호도

작성자: PopPins II 개발팀
버전: 1.0.0
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .database import Base

class GenerationLog(Base):
    """
    AI 콘텐츠 생성 이력 모델
    
    AI가 콘텐츠를 생성할 때마다 기록되는 로그입니다.
    디버깅, 성능 분석, 사용 패턴 분석에 활용됩니다.
    
    테이블명: generation_logs
    
    Attributes:
        id (int): 기본 키 (자동 증가)
        timestamp (DateTime): 생성 시각 (UTC)
        request_type (str): 요청 타입 (인덱스)
            가능한 값: "course", "concept", "exercise", "quiz", "objectives", "grading"
        topic (str): 주제/토픽 (인덱스)
        prompt_context (Text): 사용된 프롬프트/컨텍스트 (JSON 문자열)
        generated_content (Text): 생성된 콘텐츠 (JSON 문자열)
        model_name (str): 사용된 AI 모델 이름
            예: "gemini-2.5-flash"
        latency_ms (int, optional): 생성 소요 시간 (밀리초)
    """
    __tablename__ = "generation_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    request_type = Column(String, index=True)  # course, concept, exercise, quiz
    topic = Column(String, index=True)
    prompt_context = Column(Text)  # JSON string of the prompt/context used
    generated_content = Column(Text)  # JSON string of the result
    model_name = Column(String)
    latency_ms = Column(Integer, nullable=True)  # 생성 소요 시간 (밀리초)

class QuizResult(Base):
    """
    퀴즈 채점 결과 모델
    
    사용자가 퀴즈에 답변을 제출하고 AI가 채점한 결과를 저장합니다.
    저장된 결과는 학습 컨텍스트로 활용되어 개인화된 콘텐츠 생성에 사용됩니다.
    
    테이블명: quiz_results
    
    Attributes:
        id (int): 기본 키 (자동 증가)
        chapter_title (str): 챕터 제목 (인덱스)
        score (int): 점수 (0-100)
        weak_points (Text): 약점 목록 (JSON 문자열)
            형식: ["개선할 점 1", "개선할 점 2", ...]
        timestamp (DateTime): 채점 시각 (UTC)
    """
    __tablename__ = "quiz_results"

    id = Column(Integer, primary_key=True, index=True)
    chapter_title = Column(String, index=True)
    score = Column(Integer)  # 0-100 점수
    weak_points = Column(Text)  # JSON string of weak points
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class UserFeedback(Base):
    """
    사용자 피드백 모델
    
    사용자가 챕터에 대한 평가를 제출할 때 저장됩니다.
    피드백은 향후 콘텐츠 개선 및 개인화에 활용됩니다.
    
    테이블명: user_feedback
    
    Attributes:
        id (int): 기본 키 (자동 증가)
        chapter_title (str): 챕터 제목 (인덱스)
        rating (int): 평점 (1-5)
            1: 매우 불만족, 5: 매우 만족
        comment (Text, optional): 사용자 코멘트
        timestamp (DateTime): 피드백 제출 시각 (UTC)
    """
    __tablename__ = "user_feedback"

    id = Column(Integer, primary_key=True, index=True)
    chapter_title = Column(String, index=True)
    rating = Column(Integer)  # 1-5 평점
    comment = Column(Text, nullable=True)  # 선택적 코멘트
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Course(Base):
    """
    코스 모델
    
    사용자가 생성한 교육 코스의 기본 정보를 저장합니다.
    하나의 코스는 여러 개의 챕터를 포함합니다 (1:N 관계).
    
    테이블명: courses
    
    Attributes:
        id (int): 기본 키 (자동 증가)
        topic (str): 코스 제목 (인덱스)
            예: "파이썬 리스트", "React 기초"
        description (Text): 코스 설명
        level (str): 난이도
            가능한 값: "초급", "중급", "고급"
        created_at (DateTime): 코스 생성 시각 (UTC)
        chapters (relationship): 이 코스에 속한 챕터 목록
            SQLAlchemy relationship으로 자동 로드됨
    
    Relationships:
        - chapters: Chapter 모델과 1:N 관계
    """
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, index=True)
    description = Column(Text)
    level = Column(String)  # 초급, 중급, 고급
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # SQLAlchemy relationship: 이 코스의 모든 챕터를 자동으로 로드
    chapters = relationship("Chapter", back_populates="course")

class Chapter(Base):
    """
    챕터 모델
    
    코스의 개별 챕터 정보를 저장합니다.
    각 챕터는 개념, 실습, 퀴즈 콘텐츠를 포함할 수 있습니다.
    
    테이블명: chapters
    
    Attributes:
        id (int): 기본 키 (자동 증가)
        course_id (int): 소속 코스 ID (외래키)
            ForeignKey("courses.id")로 Course와 연결
        title (str): 챕터 제목
            예: "리스트 기초", "리스트 메서드"
        description (Text): 챕터 설명
        content (Text, optional): 생성된 콘텐츠 (JSON 문자열)
            형식: {"concept": {...}, "exercise": {...}, "quiz": {...}}
            사용자가 챕터를 학습할 때 생성되어 저장됨
        is_completed (int): 완료 여부
            0: 미완료, 1: 완료
            SQLite는 Boolean 타입이 없어 Integer 사용
    
    Relationships:
        - course: Course 모델과 N:1 관계 (다대일)
    """
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))  # 외래키: courses 테이블 참조
    title = Column(String)
    description = Column(Text)
    content = Column(Text, nullable=True)  # JSON string of generated content (concept, exercise, quiz)
    is_completed = Column(Integer, default=0)  # 0: False, 1: True (SQLite doesn't have native Boolean)

    # SQLAlchemy relationship: 이 챕터가 속한 코스 정보
    course = relationship("Course", back_populates="chapters")

class UserPreference(Base):
    """
    사용자 학습 선호도 모델
    
    사용자가 설문을 통해 입력한 학습 선호도를 저장합니다.
    저장된 선호도는 향후 개인화된 콘텐츠 생성에 활용됩니다.
    
    테이블명: user_preferences
    
    Attributes:
        id (int): 기본 키 (자동 증가)
        learning_goal (str): 학습 목표
            예: "취업 준비", "프로젝트 완성", "이론 이해"
        learning_style (str): 학습 스타일
            예: "실습 중심", "이론 중심", "균형"
        desired_depth (str): 원하는 학습 깊이
            예: "기초", "중급", "고급"
        created_at (DateTime): 선호도 저장 시각 (UTC)
    
    Note:
        현재는 단일 사용자 환경을 가정하지만, 향후 다중 사용자 지원 시
        user_id 컬럼 추가 필요
    """
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    learning_goal = Column(String)  # 학습 목표
    learning_style = Column(String)  # 학습 스타일
    desired_depth = Column(String)  # 원하는 학습 깊이
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
