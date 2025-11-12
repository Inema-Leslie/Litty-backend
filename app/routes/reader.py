# app/routes/reader.py
import requests
import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from app.utils.database import get_db
from app.utils.auth import get_current_user
from app.models.user import UserResponse
from app.models.book import Book
from app.models.reading_session import ReadingSession, ReadingSessionCreate, ReadingSessionResponse

router = APIRouter()

# Store current reading positions in memory (in production, use Redis)
current_positions = {}

@router.get("/book-content/{book_id}")
async def get_book_content(
    book_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get book content for reading using database ID"""
    try:
        print(f"📖 Getting content for book ID: {book_id}")
        
        # Find book by database ID
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        
        # Fetch text content from Internet Archive
        if not book.archive_id:
            raise HTTPException(status_code=404, detail="Book content not available")
            
        content_url = f"https://archive.org/download/{book.archive_id}/{book.archive_id}.txt"
        response = requests.get(content_url)
        
        if response.status_code == 200:
            content = response.text
            
            # Clean and format content
            content = clean_book_content(content)
            
            # Get current position from memory or start at 0
            position_key = f"{current_user.id}_{book.id}"
            current_position = current_positions.get(position_key, 0)
            
            # Calculate reading progress based on sessions
            total_reading_time = db.query(func.sum(ReadingSession.duration_minutes)).filter(
                ReadingSession.user_id == current_user.id,
                ReadingSession.book_id == book.id
            ).scalar() or 0
            
            total_pages_read = db.query(func.sum(ReadingSession.pages_read)).filter(
                ReadingSession.user_id == current_user.id,
                ReadingSession.book_id == book.id
            ).scalar() or 0
            
            # Estimate progress based on reading time and position
            estimated_pages = estimate_pages(content)
            progress_percentage = min(100.0, (current_position / len(content)) * 100) if content else 0
            
            return {
                "book_id": book.id,
                "archive_id": book.archive_id,
                "title": book.title,
                "author": book.authors,
                "content": content,
                "total_chars": len(content),
                "current_position": current_position,
                "progress_percentage": progress_percentage,
                "word_count": len(content.split()),
                "total_reading_time": total_reading_time,
                "total_pages_read": total_pages_read,
                "estimated_total_pages": estimated_pages
            }
        else:
            raise HTTPException(status_code=404, detail="Book content not available")
            
    except Exception as e:
        print(f"❌ Error getting book content: {e}")
        raise HTTPException(status_code=500, detail="Failed to get book content")

def clean_book_content(content: str) -> str:
    """Clean and format book content"""
    # Remove excessive whitespace
    content = re.sub(r'\n\s*\n', '\n\n', content)
    # Remove Project Gutenberg headers/footers
    content = re.sub(r'\*\*\*.*?END.*?\*\*\*', '', content, flags=re.DOTALL)
    content = re.sub(r'Project Gutenberg.*?\n', '', content, flags=re.DOTALL)
    return content.strip()

def estimate_pages(content: str, chars_per_page: int = 1800) -> int:
    """Estimate page count based on character count"""
    return max(1, len(content) // chars_per_page)

@router.post("/start-reading-session/{book_id}")
async def start_reading_session(
    book_id: int,
    current_position: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new reading session and update current position"""
    try:
        print(f"📚 Starting reading session for book {book_id}")
        
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        
        # Store current position in memory
        position_key = f"{current_user.id}_{book_id}"
        current_positions[position_key] = current_position
        
        # Calculate pages read based on position change
        if not book.archive_id:
            raise HTTPException(status_code=404, detail="Book content not available")
            
        content_url = f"https://archive.org/download/{book.archive_id}/{book.archive_id}.txt"
        response = requests.get(content_url)
        total_chars = len(response.text) if response.status_code == 200 else 1
        
        # Estimate pages read based on position
        chars_per_page = 1800
        pages_read = max(1, (current_position // chars_per_page))
        
        # Create a new reading session (duration will be updated when session ends)
        reading_session = ReadingSession(
            user_id=current_user.id,
            book_id=book_id,
            pages_read=pages_read,
            duration_minutes=0,  # Will be updated when session ends
            session_date=func.now()
        )
        
        db.add(reading_session)
        db.commit()
        db.refresh(reading_session)
        
        progress_percentage = min(100.0, (current_position / total_chars) * 100)
        
        return {
            "success": True,
            "session_id": reading_session.id,
            "current_position": current_position,
            "progress_percentage": progress_percentage,
            "pages_read": pages_read
        }
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error starting reading session: {e}")
        raise HTTPException(status_code=500, detail="Failed to start reading session")

@router.post("/end-reading-session/{session_id}")
async def end_reading_session(
    session_id: int,
    duration_minutes: int,
    final_position: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """End a reading session and update duration"""
    try:
        print(f"⏹️ Ending reading session {session_id}")
        
        reading_session = db.query(ReadingSession).filter(
            ReadingSession.id == session_id,
            ReadingSession.user_id == current_user.id
        ).first()
        
        if not reading_session:
            raise HTTPException(status_code=404, detail="Reading session not found")
        
        # Update session with duration and recalculate pages
        reading_session.duration_minutes = duration_minutes
        
        # Update current position
        position_key = f"{current_user.id}_{reading_session.book_id}"
        current_positions[position_key] = final_position
        
        db.commit()
        
        # Calculate total reading stats
        total_stats = db.query(
            func.sum(ReadingSession.duration_minutes).label('total_time'),
            func.sum(ReadingSession.pages_read).label('total_pages')
        ).filter(
            ReadingSession.user_id == current_user.id,
            ReadingSession.book_id == reading_session.book_id
        ).first()
        
        return {
            "success": True,
            "session_duration": duration_minutes,
            "total_reading_time": total_stats.total_time or 0,
            "total_pages_read": total_stats.total_pages or 0,
            "final_position": final_position
        }
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error ending reading session: {e}")
        raise HTTPException(status_code=500, detail="Failed to end reading session")

@router.get("/reading-stats/{book_id}")
async def get_reading_stats(
    book_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get reading statistics for a book"""
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        
        # Get current position from memory
        position_key = f"{current_user.id}_{book_id}"
        current_position = current_positions.get(position_key, 0)
        
        # Get book content for progress calculation
        total_chars = 0
        if book.archive_id:
            content_url = f"https://archive.org/download/{book.archive_id}/{book.archive_id}.txt"
            response = requests.get(content_url)
            if response.status_code == 200:
                total_chars = len(response.text)
        
        # Get reading sessions statistics
        stats = db.query(
            func.count(ReadingSession.id).label('session_count'),
            func.sum(ReadingSession.duration_minutes).label('total_time'),
            func.sum(ReadingSession.pages_read).label('total_pages'),
            func.max(ReadingSession.session_date).label('last_read')
        ).filter(
            ReadingSession.user_id == current_user.id,
            ReadingSession.book_id == book_id
        ).first()
        
        progress_percentage = min(100.0, (current_position / total_chars) * 100) if total_chars > 0 else 0
        
        return {
            "book_id": book_id,
            "current_position": current_position,
            "progress_percentage": progress_percentage,
            "session_count": stats.session_count or 0,
            "total_reading_time": stats.total_time or 0,
            "total_pages_read": stats.total_pages or 0,
            "last_read": stats.last_read
        }
        
    except Exception as e:
        print(f"❌ Error getting reading stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get reading stats")

@router.get("/reading-sessions/{book_id}")
async def get_reading_sessions(
    book_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all reading sessions for a book"""
    try:
        sessions = db.query(ReadingSession).filter(
            ReadingSession.user_id == current_user.id,
            ReadingSession.book_id == book_id
        ).order_by(ReadingSession.session_date.desc()).all()
        
        return [ReadingSessionResponse.from_orm(session) for session in sessions]
        
    except Exception as e:
        print(f"❌ Error getting reading sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get reading sessions")

@router.post("/update-position/{book_id}")
async def update_current_position(
    book_id: int,
    position: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current reading position without creating a session"""
    try:
        position_key = f"{current_user.id}_{book_id}"
        current_positions[position_key] = position
        
        return {
            "success": True,
            "current_position": position,
            "message": "Position updated"
        }
        
    except Exception as e:
        print(f"❌ Error updating position: {e}")
        raise HTTPException(status_code=500, detail="Failed to update position")