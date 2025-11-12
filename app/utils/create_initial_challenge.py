# app/utils/create_initial_challenges.py
from sqlalchemy.orm import Session
from app.models.challenge import Challenge, ChallengeType

def create_initial_challenges(db: Session):
    """Create the initial challenges for the app"""
    
    initial_challenges = [
        {
            "name": "Warm-up Streak",
            "description": "Read for 7 days in a row", 
            "type": ChallengeType.STREAK,
            "target_value": 7,
            "reward_points": 50
        },
        {
            "name": "Unbreakable Chain",
            "description": "Maintain a 30-day reading streak",
            "type": ChallengeType.STREAK, 
            "target_value": 30,
            "reward_points": 200
        },
        {
            "name": "Page a Day", 
            "description": "Read at least one page every day for 14 days",
            "type": ChallengeType.CONSISTENCY,
            "target_value": 14,
            "reward_points": 100
        },
        {
            "name": "Bookworm Initiate",
            "description": "Finish your first 5 books",
            "type": ChallengeType.COMPLETION,
            "target_value": 5,
            "reward_points": 150
        },
        {
            "name": "Marathon Reader",
            "description": "Read 10,000 pages in total", 
            "type": ChallengeType.PAGES,
            "target_value": 10000,
            "reward_points": 500
        }
    ]
    
    for challenge_data in initial_challenges:
        # Check if challenge already exists
        existing = db.query(Challenge).filter(
            Challenge.name == challenge_data["name"]
        ).first()
        
        if not existing:
            challenge = Challenge(**challenge_data)
            db.add(challenge)
    
    db.commit()
    print("Initial challenges created successfully!")

# You can run this from your main.py or in a separate migration script
if __name__ == "__main__":
    from app.utils.database import SessionLocal
    db = SessionLocal()
    create_initial_challenges(db)
    db.close()