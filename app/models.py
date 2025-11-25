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
