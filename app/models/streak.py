from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.utils.database import Base
from pydantic import BaseModel
from datetime import datetime, date

class DailyReading(Base):
    __tablename__ = "daily_readings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reading_date = Column(Date, nullable=False)  # Just the date part
    reading_seconds = Column(Integer, default=0)  # Total seconds read that day
    page_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    user = relationship("User")

class DailyReadingCreate(BaseModel):
    reading_seconds: int = 0
    page_count: int = 0

class DailyReadingResponse(BaseModel):
    id: int
    user_id: int
    reading_date: date
    reading_seconds: int
    page_count: int
    
    class Config:
        from_attributes = True