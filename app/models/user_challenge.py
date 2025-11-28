from sqlalchemy import Column, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.utils.database import Base
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UserChallenge(Base):
    __tablename__ = "user_challenges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False)
    progress = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    completed_date = Column(DateTime(timezone=True))
    started_date = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="challenges")
    challenge = relationship("Challenge", back_populates="user_progress")


class UserChallengeCreate(BaseModel):
    challenge_id: int


class UserChallengeResponse(BaseModel):
    id: int
    user_id: int
    challenge_id: int
    progress: int
    is_completed: bool
    completed_date: Optional[datetime] = None
    started_date: datetime
    

    challenge: 'ChallengeResponse'

    class Config:
        from_attributes = True