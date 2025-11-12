from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import inspect, text
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables FIRST
load_dotenv()

# Debug: Check environment variables
print("🔍 Environment Variables Debug:")
print(f"DATABASE_URL exists: {'DATABASE_URL' in os.environ}")
print(f"DATABASE_URL value: {os.getenv('DATABASE_URL')}")
print(f"JWT_SECRET_KEY exists: {'JWT_SECRET_KEY' in os.environ}")
print(f"Current directory: {os.getcwd()}")
print(f".env file exists: {os.path.exists('.env')}")

# List all environment variables that start with DATABASE or JWT
for key, value in os.environ.items():
    if 'DATABASE' in key or 'DB' in key or 'JWT' in key:
        print(f"Found env var: {key} = {value}")

from app.utils.database import engine, Base, get_db
from app.utils.auth import get_current_user  # ADD THIS IMPORT

# Import all models to ensure they're registered with SQLAlchemy
from app.models.user import User
from app.models.book import Book
from app.models.user_library import UserLibrary
from app.models.reading_session import ReadingSession 
from app.models.challenge import Challenge
from app.models.user_challenge import UserChallenge
from app.models.streak import DailyReading

# Create FastAPI app instance
app = FastAPI(
    title="Litty API",
    description="Backend for Litty reading app",
    version="1.0.0"
)

# CORS middleware - Update for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Your local React dev server
        "https://your-frontend-url.onrender.com",  # Replace with your frontend URL
        "https://your-frontend-url.netlify.app",   # If using Netlify
        "http://localhost:3000",   # Alternative React dev server
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Add this for production
    allow_origin_regex=r"https?://.*\.render\.com"  # Allow Render subdomains
)

# Include routes
from app.routes import simple_auth, books, reader, challenges

app.include_router(simple_auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(books.router, prefix="/api/books", tags=["books"])
app.include_router(reader.router, prefix="/api/reader", tags=["reader"])
app.include_router(challenges.router, prefix="/api", tags=["challenges"])

# MOVE TABLE CREATION TO STARTUP EVENT
@app.on_event("startup")
async def startup_event():
    print("📋 Tables to create:", Base.metadata.tables.keys())
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created/verified!")
    
    # FORCE reseeding every time for now
    print("🔄 Forcing challenge reseeding...")
    await seed_default_challenges()

async def seed_default_challenges():
    from app.utils.database import SessionLocal
    from app.models.challenge import Challenge, ChallengeType
    
    print("🔍 Python ChallengeType values:")
    for challenge_type in ChallengeType:
        print(f"   - {challenge_type.name} = '{challenge_type.value}'")
        
    db = SessionLocal()
    try:
        # Clear existing challenges to ensure fresh data
        db.query(Challenge).delete()
        print("🧹 Cleared existing challenges")
        
        # Create our three core challenges plus bonus ones
        all_challenges = [
            # Core Challenges We're Implementing
            Challenge(
                name="Warm-up Streak",
                description="Read for 7 days in a row",
                type=ChallengeType.STREAK,
                target_value=7,
                reward_points=50,
                is_active=True
            ),
            Challenge(
                name="Unbreakable Chain", 
                description="Maintain a 30-day reading streak",
                type=ChallengeType.STREAK,
                target_value=30,
                reward_points=200,
                is_active=True
            ),
            Challenge(
                name="Page a Day",
                description="Read at least one page every day for 14 days",
                type=ChallengeType.PAGES,
                target_value=14,
                reward_points=100,
                is_active=True
            ),
            # Bonus Challenges
            Challenge(
                name="Bookworm Initiate",
                description="Finish your first 5 books",
                type=ChallengeType.COMPLETION,
                target_value=5,
                reward_points=150,
                is_active=True
            ),
            Challenge(
                name="Marathon Reader",
                description="Read 10,000 pages in total",
                type=ChallengeType.PAGES,
                target_value=10000,
                reward_points=500,
                is_active=True
            ),
            # Additional Streak Challenges
            Challenge(
                name="3-Day Starter",
                description="Read for 3 consecutive days",
                type=ChallengeType.STREAK,
                target_value=3,
                reward_points=25,
                is_active=True
            ),
            Challenge(
                name="Fortnight Faithful",
                description="14-day reading streak", 
                type=ChallengeType.STREAK,
                target_value=14,
                reward_points=100,
                is_active=True
            )
        ]
        
        # Add all to database
        for challenge in all_challenges:
            db.add(challenge)
        
        db.commit()
        print(f"✅ Seeded {len(all_challenges)} default challenges!")
        
        # Verify they were saved
        saved_count = db.query(Challenge).count()
        print(f"✅ Database now has {saved_count} challenges total")
        
        # Print challenge names for verification
        challenges = db.query(Challenge).all()
        print("📋 Seeded challenges:")
        for challenge in challenges:
            print(f"   - {challenge.name} (Type: {challenge.type.value}, Target: {challenge.target_value})")
        
    except Exception as e:
        print(f"❌ Error seeding challenges: {e}")
        import traceback
        print(f"❌ Full error: {traceback.format_exc()}")
        db.rollback()
    finally:
        db.close()

# DEBUG ENDPOINTS (Remove these for production)
@app.get("/debug-all")
async def debug_all(db: Session = Depends(get_db)):
    """Comprehensive debug information"""
    # Check challenges
    challenges = db.query(Challenge).all()
    challenges_data = [
        {
            "id": c.id,
            "name": c.name,
            "type": c.type.value if c.type else "None",
            "target_value": c.target_value,
            "is_active": c.is_active,
            "reward_points": c.reward_points
        }
        for c in challenges
    ]
    
    # Check database tables
    inspector = inspect(db.get_bind())
    tables = inspector.get_table_names()
    
    return {
        "database_tables": tables,
        "total_challenges": len(challenges),
        "challenges": challenges_data,
        "seeding_status": "Check console for seeding messages"
    }

@app.get("/debug-seeding")
async def debug_seeding():
    """Check if seeding worked"""
    from app.utils.database import SessionLocal
    from app.models.challenge import Challenge
    
    db = SessionLocal()
    try:
        challenge_count = db.query(Challenge).count()
        challenges = db.query(Challenge).all()
        challenge_list = [{"id": c.id, "name": c.name, "is_active": c.is_active} for c in challenges]
        
        return {
            "challenge_count": challenge_count,
            "challenges": challenge_list,
            "status": "Seeded successfully" if challenge_count > 0 else "No challenges found - seeding may have failed"
        }
    finally:
        db.close()

@app.get("/debug-challenges")
async def debug_challenges(db: Session = Depends(get_db)):
    """Check what challenges are in the database"""
    challenges = db.query(Challenge).all()
    return {
        "total_challenges": len(challenges),
        "challenges": [
            {
                "id": challenge.id,
                "name": challenge.name,
                "type": challenge.type.value if challenge.type else "None",
                "target_value": challenge.target_value,
                "reward_points": challenge.reward_points,
                "is_active": challenge.is_active
            }
            for challenge in challenges
        ]
    }

@app.get("/debug-tables")
async def debug_tables(db: Session = Depends(get_db)):
    inspector = inspect(db.get_bind())
    tables = inspector.get_table_names()
    table_info = {}
    
    for table in tables:
        columns = inspector.get_columns(table)
        table_info[table] = [{"name": col["name"], "type": str(col["type"])} for col in columns]
    
    return {
        "tables": tables,
        "table_columns": table_info
    }

@app.get("/test-db-connection")
async def test_db_connection(db: Session = Depends(get_db)):
    """Test database connection"""
    try:
        result = db.execute(text("SELECT 1 as test"))
        test_value = result.first()[0]
        return {"status": "success", "database": "connected", "test_value": test_value}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

@app.get("/")
async def root():
    return {"message": "Litty Backend API is running!"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "Litty API"}

# Add the missing endpoints directly to main.py to ensure they work
@app.get("/api/user/challenges")
async def get_user_challenges_direct(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Direct endpoint for user challenges"""
    from app.models.user_challenge import UserChallenge
    
    user_challenges = db.query(UserChallenge).filter(
        UserChallenge.user_id == current_user.id
    ).all()
    return user_challenges

@app.get("/api/user/streak")
async def get_user_streak_direct(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Direct endpoint for user streak"""
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "current_streak": user.current_streak,
        "longest_streak": user.longest_streak,
        "last_reading_date": user.last_reading_date
    }

# ADD THIS FOR RENDER DEPLOYMENT
@app.on_event("startup")
async def startup_event():
    """Enhanced startup event with better error handling"""
    try:
        print("📋 Starting up Litty API...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created/verified!")
        
        # Only seed challenges once in production
        # Remove the forced reseeding for production
        print("🔄 Seeding default challenges...")
        await seed_default_challenges()
        
        print("🎉 Litty API startup complete!")
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        raise

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))  # Use Render's PORT environment variable
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)