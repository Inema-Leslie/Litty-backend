# app/models/user_library.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from datetime import datetime

from app.utils.database import Base

class UserLibrary(Base):
    __tablename__ = "user_library"
    __table_args__ = {'extend_existing': True}  # ADD THIS LINE
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    book_id = Column(Integer, ForeignKey("books.id"))
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    is_favorite = Column(Boolean, default=False)
    reading_status = Column(String, default="want_to_read")  # want_to_read, reading, completed
    
    # Relationships
    user = relationship("" \
    "User", back_populates="library_books")
    book = relationship("Book")

# Pydantic models
class UserLibraryBase(BaseModel):
    user_id: int
    book_id: int
    is_favorite: bool = False
    reading_status: str = "want_to_read"

class UserLibraryCreate(UserLibraryBase):
    pass

class UserLibraryResponse(UserLibraryBase):
    id: int
    added_at: datetime
    book: 'BookResponse'  # We'll forward declare this
    
    class Config:
        from_attributes = True

# Forward declaration fix
from app.models.book import BookResponse
UserLibraryResponse.update_forward_refs()