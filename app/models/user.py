# app/models/user.py - SIMPLIFIED VERSION
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship 
from app.utils.database import Base
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
import re
from .challenge import ChallengeResponse

# Single User model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(30), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    streak = Column(Integer, default=0)
    total_reading_time = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_reading_date = Column(DateTime(timezone=True))
    streak_updated_at = Column(DateTime(timezone=True))
    current_week_count = Column(Integer, default=0)
    weekly_goal = Column(Integer, default=5)
    total_reading_weeks = Column(Integer, default=0)
    perfect_weeks = Column(Integer, default=0)
    
    # Relationships
    library_books = relationship("UserLibrary", back_populates="user")
    reading_sessions = relationship("ReadingSession", back_populates="user")
    challenges = relationship("UserChallenge", back_populates="user")

# Pydantic Models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

    @validator('username')
    def validate_username(cls, v):

        v = v.strip()

        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if len(v) > 30:
            raise ValueError('Username cannot exceed 30 characters')
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    streak: int
    total_reading_time: int
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse