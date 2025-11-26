from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class GenerationLog(Base):
    __tablename__ = "generation_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    request_type = Column(String, index=True)  # course, concept, exercise, quiz
    topic = Column(String, index=True)
    prompt_context = Column(Text)  # JSON string of the prompt/context used
    generated_content = Column(Text)  # JSON string of the result
    model_name = Column(String)
    latency_ms = Column(Integer, nullable=True)

class QuizResult(Base):
    __tablename__ = "quiz_results"

    id = Column(Integer, primary_key=True, index=True)
    chapter_title = Column(String, index=True)
    score = Column(Integer)
    weak_points = Column(Text)  # JSON string of weak points
    timestamp = Column(DateTime, default=datetime.utcnow)

class UserFeedback(Base):
    __tablename__ = "user_feedback"

    id = Column(Integer, primary_key=True, index=True)
    chapter_title = Column(String, index=True)
    rating = Column(Integer)  # 1-5
    comment = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, index=True)
    description = Column(Text)
    level = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    chapters = relationship("Chapter", back_populates="course")

class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    title = Column(String)
    description = Column(Text)
    content = Column(Text, nullable=True)  # JSON string of generated content (concept, exercise, quiz)
    is_completed = Column(Integer, default=0)  # 0: False, 1: True (SQLite doesn't have native Boolean)

    course = relationship("Course", back_populates="chapters")

class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    learning_goal = Column(String)
    learning_style = Column(String)
    desired_depth = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
