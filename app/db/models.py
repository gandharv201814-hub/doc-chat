from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String
from app.db.database import Base

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(String, unique=True, nullable=False, index=True)
    filename = Column(String, nullable=False)
    chunk_count = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

class QuestionHistory(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    question = Column(String, nullable=False)
    doc_id = Column(String, nullable=True)
    latency_ms = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)