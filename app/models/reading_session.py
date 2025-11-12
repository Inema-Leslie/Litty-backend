from sqlalchemy import Column, Integer, ForeignKey, DateTime, Interval
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.utils.database import Base
from pydantic import BaseModel
from datetime import datetime, timedelta

class ReadingSession(Base):
    __tablename__ = "reading_sessions"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    pages_read = Column(Integer, default=0)
    duration_minutes = Column(Integer, default=0)
    session_date = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="reading_sessions")
    book = relationship("Book", back_populates="reading_sessions")

class ReadingSessionCreate(BaseModel):
    book_id: int
    pages_read: int
    duration_minutes: int

class ReadingSessionResponse(BaseModel):
    id: int
    user_id: int
    book_id: int
    pages_read: int
    duration_minutes: int
    session_date: datetime
    book: 'BookResponse' = None

    class Config:
        from_attributes = True