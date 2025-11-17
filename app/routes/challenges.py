from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.utils.database import get_db
from app.models.challenge import Challenge, ChallengeType
from app.models.user_challenge import UserChallenge
from app.schemas.user import UserSchema
from app.models.user import User
from app.utils.auth import get_current_user

# CHANGED: Import response models using TYPE_CHECKING to avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.challenge import ChallengeResponse
    from app.models.user_challenge import UserChallengeResponse

router = APIRouter(prefix="/challenges", tags=["challenges"])

# CHANGED: Use string annotation "ChallengeResponse" instead of direct reference
@router.get("/", response_model=List["ChallengeResponse"])
def get_challenges(
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user)
):
    """Get all active challenges"""
    challenges = db.query(Challenge).filter(Challenge.is_active == True).all()
    return challenges

# CHANGED: Use string annotation "UserChallengeResponse" instead of direct reference
@router.get("/user/progress", response_model=List["UserChallengeResponse"])
def get_user_challenges(
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user)
):
    """Get current user's challenge progress"""
    user_challenges = db.query(UserChallenge).filter(
        UserChallenge.user_id == current_user.id
    ).all()
    return user_challenges

@router.post("/{challenge_id}/start")
def start_challenge(
    challenge_id: int,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user)
):
    """User opts into a challenge"""
    
    # Check if challenge exists and is active
    challenge = db.query(Challenge).filter(
        Challenge.id == challenge_id,
        Challenge.is_active == True
    ).first()
    
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    # Check if user already has this challenge
    existing = db.query(UserChallenge).filter(
        UserChallenge.user_id == current_user.id,
        UserChallenge.challenge_id == challenge_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already enrolled in this challenge")
    
    # Create user challenge entry
    user_challenge = UserChallenge(
        user_id=current_user.id,
        challenge_id=challenge_id,
        progress=0,
        is_completed=False
    )
    
    db.add(user_challenge)
    db.commit()
    db.refresh(user_challenge)
    
    return {"message": "Challenge started successfully", "user_challenge_id": user_challenge.id}

@router.post("/{challenge_id}/abandon")
def abandon_challenge(
    challenge_id: int,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user)
):
    """User abandons an active challenge"""
    
    user_challenge = db.query(UserChallenge).filter(
        UserChallenge.user_id == current_user.id,
        UserChallenge.challenge_id == challenge_id,
        UserChallenge.is_completed == False
    ).first()
    
    if not user_challenge:
        raise HTTPException(status_code=404, detail="Active challenge not found")
    
    db.delete(user_challenge)
    db.commit()
    
    return {"message": "Challenge abandoned successfully"}

# CHANGED: Use string annotation "UserChallengeResponse" instead of direct reference
@router.get("/user/challenges", response_model=List["UserChallengeResponse"])
def get_user_challenges_alt(
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user)
):
    """Alternative endpoint for user challenges (to match frontend)"""
    user_challenges = db.query(UserChallenge).filter(
        UserChallenge.user_id == current_user.id
    ).all()
    return user_challenges

@router.get("/user/streak")
def get_user_streak(
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user)
):
    """Get user's current streak"""
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "current_streak": user.current_streak,
        "longest_streak": user.longest_streak,
        "last_reading_date": user.last_reading_date
    }

# REMOVED: Bottom imports are no longer needed with TYPE_CHECKING approach