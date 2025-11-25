from sqlalchemy import Column, Integer, String, Text, DateTime
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
