from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, Boolean 
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.utils.database import Base
from pydantic import BaseModel
from datetime import datetime
import enum

class ChallengeType(enum.Enum):
    STREAK = "streak"
    CONSISTENCY = "consistency"  # For Page-a-Day type challenges
    PAGES = "pages"
    COMPLETION = "completion"
    TIME = "time"

class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(Enum(ChallengeType), nullable=False)
    target_value = Column(Integer, nullable=False)  # 7 days, 100 pages, etc.
    reward_points = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user_progress = relationship("UserChallenge", back_populates="challenge")

class ChallengeCreate(BaseModel):
    name: str
    description: str = None
    type: str
    target_value: int
    reward_points: int = 0

class ChallengeResponse(BaseModel):
    id: int
    name: str
    description: str = None
    type: str
    target_value: int
    reward_points: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True