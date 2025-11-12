# app/models/simple_user.py
#from sqlalchemy import Column, Integer, String, DateTime
#from sqlalchemy.sql import func
#from sqlalchemy.orm import relationship 
#from app.utils.database import Base
#from pydantic import BaseModel, EmailStr
#from datetime import datetime

# Simple User model without any relationships
#class SimpleUser(Base):
 #   __tablename__ = "users"
  #  __table_args__ = {'extend_existing': True}

   # id = Column(Integer, primary_key=True, index=True)
    #username = Column(String(30), unique=True, index=True, nullable=False)
    #email = Column(String(255), unique=True, index=True, nullable=False)
    #password_hash = Column(String(255), nullable=False)
    #streak = Column(Integer, default=0)
    #total_reading_time = Column(Integer, default=0)
    #created_at = Column(DateTime(timezone=True), server_default=func.now())
    #library_books = relationship("UserLibrary", back_populates="user")
    #reading_sessions = relationship("ReadingSession", back_populates="user")
#class SimpleUserCreate(BaseModel):
 #   username: str
  #  email: EmailStr
   # password: str

# ADD THIS: Login model
#class SimpleUserLogin(BaseModel):
 #   username: str
  #  password: str

#class SimpleUserResponse(BaseModel):
 #   id: int
  #  username: str
   # email: str
    #streak: int
    #total_reading_time: int
    #created_at: datetime

    #class Config:
      #  from_attributes = True

#class SimpleToken(BaseModel):
 #   access_token: str
  #  token_type: str
   # user: SimpleUserResponse      