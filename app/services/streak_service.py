from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.streak import DailyReading
from app.models.user_challenge import UserChallenge
from app.models.challenge import Challenge, ChallengeType

class StreakService:
    
    @staticmethod
    def update_streak(db: Session, user_id: int, reading_seconds: int = 0, page_count: int = 0):
        """Update user streak when they read"""
        today = date.today()
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return None
        
        # Check if already logged reading today
        existing_reading = db.query(DailyReading).filter(
            DailyReading.user_id == user_id,
            DailyReading.reading_date == today
        ).first()
        
        if existing_reading:
            # Update existing reading
            existing_reading.reading_seconds += reading_seconds
            existing_reading.page_count += page_count
        else:
            # Create new daily reading
            new_reading = DailyReading(
                user_id=user_id,
                reading_date=today,
                reading_seconds=reading_seconds,
                page_count=page_count
            )
            db.add(new_reading)
            
            # This is NEW reading for today - update streaks
            StreakService._update_user_streaks(db, user, today)
            StreakService._update_challenge_progress(db, user, today)  # NEW: Update challenges
            
        db.commit()
        return user
    
    @staticmethod
    def _update_user_streaks(db: Session, user: User, today: date):
        """Update daily streak counters"""
        yesterday = today - timedelta(days=1)
        
        if user.last_reading_date:
            last_date = user.last_reading_date.date()
            
            if last_date == yesterday:
                # Consecutive day - increment streak
                user.current_streak += 1
            elif last_date == today:
                # Already updated today - do nothing
                return
            else:
                # Streak broken - reset to 1
                user.current_streak = 1
        else:
            # First time reading
            user.current_streak = 1
        
        # Update longest streak if needed
        if user.current_streak > user.longest_streak:
            user.longest_streak = user.current_streak
        
        user.last_reading_date = datetime.now()
        user.streak_updated_at = datetime.now()
        
        # Check streak-based challenges
        StreakService._check_streak_challenges(db, user)
    
    @staticmethod
    def _update_weekly_progress(db: Session, user: User, today: date):
        """Update weekly consistency tracking"""
        # For now, we'll track this in the DailyReading table
        # Weekly challenges are checked separately
        pass
    
    @staticmethod
    def _check_streak_challenges(db: Session, user: User):
        """Award streak-based challenges"""
        streak_milestones = [3, 7, 14, 30, 90, 365]
        
        for milestone in streak_milestones:
            if user.current_streak == milestone:
                # Find the streak challenge
                challenge = db.query(Challenge).filter(
                    Challenge.type == ChallengeType.STREAK,
                    Challenge.target_value == milestone
                ).first()
                
                if challenge:
                    # Check if user already has this challenge
                    existing = db.query(UserChallenge).filter(
                        UserChallenge.user_id == user.id,
                        UserChallenge.challenge_id == challenge.id
                    ).first()
                    
                    if not existing:
                        # Award challenge to user
                        user_challenge = UserChallenge(
                            user_id=user.id,
                            challenge_id=challenge.id,
                            progress=milestone,
                            is_completed=True,
                            completed_date=datetime.now()
                        )
                        db.add(user_challenge)

    @staticmethod
    def _update_challenge_progress(db: Session, user: User, today: date):
        """Update progress for all active challenges when user logs reading"""
        
        # Get user's active challenges
        active_challenges = db.query(UserChallenge).filter(
            UserChallenge.user_id == user.id,
            UserChallenge.is_completed == False
        ).all()
        
        for user_challenge in active_challenges:
            challenge = user_challenge.challenge
            
            if challenge.type == ChallengeType.STREAK:
                # For streak challenges, progress is the current streak
                user_challenge.progress = user.current_streak
                
                # Check if completed
                if user.current_streak >= challenge.target_value:
                    user_challenge.is_completed = True
                    user_challenge.completed_date = datetime.now()
            
            elif challenge.type == ChallengeType.CONSISTENCY:
                # For Page-a-Day challenge, we need special logic
                StreakService._update_consistency_challenge(db, user, user_challenge, today)

    @staticmethod
    def _update_consistency_challenge(db: Session, user: User, user_challenge: UserChallenge, today: date):
        """Update consistency challenge (Page-a-Day) progress"""
        challenge = user_challenge.challenge
        
        # Get the last N days of reading where page_count > 0
        start_date = today - timedelta(days=challenge.target_value - 1)
        
        consistent_days = db.query(DailyReading).filter(
            DailyReading.user_id == user.id,
            DailyReading.reading_date >= start_date,
            DailyReading.reading_date <= today,
            DailyReading.page_count > 0  # At least one page read
        ).count()
        
        user_challenge.progress = consistent_days
        
        # Check if completed
        if consistent_days >= challenge.target_value:
            user_challenge.is_completed = True
            user_challenge.completed_date = datetime.now()