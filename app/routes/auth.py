from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import random
import string

from app.models.user import User, UserCreate, UserLogin, UserResponse, Token
from app.utils.auth import verify_password, get_password_hash, create_access_token, verify_token
from app.utils.database import get_db

router = APIRouter()
security = HTTPBearer()

def generate_username_suggestions(base_username: str, db: Session) -> list[str]:
    """Generate available username suggestions similar to the requested one"""
    suggestions = []
    base_username = base_username.lower().strip()
    
    # Strategy 1: Add numbers
    for i in range(1, 6):
        suggestion = f"{base_username}{i}"
        existing = db.query(User).filter(User.username == suggestion).first()
        if not existing:
            suggestions.append(suggestion)
        if len(suggestions) >= 3:
            return suggestions
    
    # Strategy 2: Add random characters
    for _ in range(5):
        suggestion = f"{base_username}_{''.join(random.choices(string.ascii_lowercase + string.digits, k=3))}"
        existing = db.query(User).filter(User.username == suggestion).first()
        if not existing and suggestion not in suggestions:
            suggestions.append(suggestion)
        if len(suggestions) >= 3:
            return suggestions
    
    # Strategy 3: Add "reader" or "book" suffix
    suffixes = ['reader', 'booklover', 'reader', 'bookworm', 'bibliophile']
    for suffix in suffixes:
        suggestion = f"{base_username}_{suffix}"
        existing = db.query(User).filter(User.username == suggestion).first()
        if not existing and suggestion not in suggestions:
            suggestions.append(suggestion)
        if len(suggestions) >= 3:
            return suggestions
    
    return suggestions[:3]

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> UserResponse:
    """Get current user from JWT token"""
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # CHANGED: Now using username as the unique identifier in tokens
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    
    # CHANGED: Query user by username instead of ID
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return UserResponse.from_orm(user)

@router.post("/register", response_model=Token)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if username already exists
    existing_user_by_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_user_by_username:
        # Generate smart suggestions for available usernames
        suggestions = generate_username_suggestions(user_data.username, db)
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Username already taken",
                "suggestions": suggestions,
                "field": "username"
            }
        )
    
    # Check if email already exists
    existing_user_by_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_user_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Email already registered",
                "field": "email"
            }
        )
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Create user
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # CHANGED: Store username in token instead of user ID
    access_token = create_access_token(data={"sub": db_user.username})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(db_user)
    )

@router.post("/login", response_model=Token)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Login user with username and password"""
    # CHANGED: Only check by username (not email)
    user = db.query(User).filter(User.username == login_data.username).first()
    
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # CHANGED: Store username in token instead of user ID
    access_token = create_access_token(data={"sub": user.username})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    """Get current user profile"""
    return current_user

# NEW: Endpoint to check username availability
@router.get("/check-username/{username}")
async def check_username_availability(username: str, db: Session = Depends(get_db)):
    """Check if a username is available and suggest alternatives if taken"""
    existing_user = db.query(User).filter(User.username == username).first()
    
    if not existing_user:
        return {
            "available": True,
            "message": "Username is available"
        }
    else:
        suggestions = generate_username_suggestions(username, db)
        return {
            "available": False,
            "message": "Username already taken",
            "suggestions": suggestions
        }