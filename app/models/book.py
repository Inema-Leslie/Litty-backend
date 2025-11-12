# app/models/book.py
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship 
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, validator
from typing import List, Optional, Union

from app.utils.database import Base

class Book(Base):
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    google_books_id = Column(String, unique=True, index=True)  # ID from Internet Archive
    archive_id = Column(String, unique=True, index=True)  # Also from Internet Archive
    title = Column(String, nullable=False)
    authors = Column(String)  # Store as comma-separated string
    description = Column(Text)
    isbn = Column(String, index=True)
    page_count = Column(Integer)
    categories = Column(String)  # Store as comma-separated string
    thumbnail = Column(String)  # Book cover URL
    published_date = Column(String)
    publisher = Column(String)
    download_links = Column(String, default="archive")
    content_url = Column(String)
    language = Column(String, default="en")
    word_count = Column(Integer, default=0)

    reading_sessions = relationship("ReadingSession", back_populates="book")

# Pydantic models for API
class BookBase(BaseModel):
    google_books_id: str
    archive_id: Optional[str] = None
    title: str
    authors: str
    description: Optional[str] = None
    isbn: Optional[str] = None
    page_count: Optional[int] = None
    categories: Optional[str] = None
    thumbnail: Optional[str] = None
    published_date: Optional[str] = None
    publisher: Optional[str] = None

class BookCreate(BookBase):
    pass

class BookResponse(BookBase):
    id: int
    
    class Config:
        from_attributes = True

class GoogleBookSearchResult(BaseModel):
    google_books_id: str
    title: str
    authors: List[str]
    description: Optional[str]
    isbn: Optional[str] = None
    page_count: Optional[int] = None
    categories: List[str]
    thumbnail: Optional[str]
    published_date: Optional[str]
    publisher: Optional[str]
    
    @validator('isbn', pre=True)
    def validate_isbn(cls, v):
        """Handle ISBN field that can be string or list"""
        if isinstance(v, list):
            # Take the first ISBN if it's a list
            return v[0] if v else None
        return v
    
    @validator('page_count', pre=True)
    def validate_page_count(cls, v):
        """Handle page_count field that can be string or integer"""
        if isinstance(v, str):
            try:
                return int(v)
            except (ValueError, TypeError):
                return None
        return v
    
    @validator('categories', pre=True)
    def validate_categories(cls, v):
        """Handle categories field that can be string or list"""
        if isinstance(v, str):
            return [v]
        elif isinstance(v, list):
            return v
        return []
    
    @validator('published_date', pre=True)
    def validate_published_date(cls, v):
        """Handle published_date field that can be string or list"""
        if isinstance(v, list):
            return v[0] if v else None
        return v
    
    @validator('publisher', pre=True)
    def validate_publisher(cls, v):
        """Handle publisher field that can be string or list"""
        if isinstance(v, list):
            return v[0] if v else None
        return v

class BookContentResponse(BaseModel):
    book_id: int
    title: str
    author: str
    content: str
    content_source: str
    total_chars: int
    current_position: int
    progress_percentage: float
    word_count: int
    total_reading_time: int
    total_pages_read: int
    estimated_total_pages: int
    has_full_content: bool

    class Config:
        from_attributes = True