from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from models import db
import json
import numpy as np
from enum import Enum

class BadgeType(Enum):
    ACHIEVEMENT = "achievement"
    MILESTONE = "milestone"
    SPECIAL = "special"
    SEASONAL = "seasonal"
    COMPETITIVE = "competitive"

class BadgeCategory(Enum):
    LEARNING = "learning"
    ASSESSMENT = "assessment"
    ENGAGEMENT = "engagement"
    SOCIAL = "social"
    CREATIVITY = "creativity"

class Badge(db.Model):
    """Badges that users can earn"""
    __tablename__ = 'badges'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    badge_type = db.Column(db.String(50), nullable=False)  # achievement, milestone, etc.
    category = db.Column(db.String(50), nullable=False)  # learning, assessment, etc.
    
    # Badge appearance
    icon_name = db.Column(db.String(50), nullable=False)  # FontAwesome icon name
    color = db.Column(db.String(20), default='#007bff')
    rarity = db.Column(db.String(20), default='common')  # common, rare, epic, legendary
    
    # Achievement criteria
    criteria_type = db.Column(db.String(50), nullable=False)  # points, streak, completion, etc.
    criteria_value = db.Column(db.Integer, nullable=False)  # Value needed to earn badge
    criteria_config = db.Column(db.Text, nullable=True)  # JSON configuration for complex criteria
    
    # Rewards
    points_reward = db.Column(db.Integer, default=0)
    experience_reward = db.Column(db.Integer, default=0)
    
    # Metadata
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Statistics
    times_awarded = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'badge_type': self.badge_type,
            'category': self.category,
            'icon_name': self.icon_name,
            'color': self.color,
            'rarity': self.rarity,
            'criteria_type': self.criteria_type,
            'criteria_value': self.criteria_value,
            'criteria_config': json.loads(self.criteria_config) if self.criteria_config else {},
            'points_reward': self.points_reward,
            'experience_reward': self.experience_reward,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'times_awarded': self.times_awarded
        }

class UserBadge(db.Model):
    """User's earned badges"""
    __tablename__ = 'user_badges'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey('badges.id'), nullable=False)
    
    # Achievement details
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    progress_value = db.Column(db.Integer, nullable=True)  # Value when badge was earned
    context_data = db.Column(db.Text, nullable=True)  # JSON data about earning context
    
    # Relationships
    user = db.relationship('User', backref='earned_badges')
    badge = db.relationship('Badge', backref='user_earnings')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'badge_id': self.badge_id,
            'earned_at': self.earned_at.isoformat() if self.earned_at else None,
            'progress_value': self.progress_value,
            'context_data': json.loads(self.context_data) if self.context_data else {},
            'badge': self.badge.to_dict() if self.badge else None
        }

class UserPoints(db.Model):
    """User's points and experience system"""
    __tablename__ = 'user_points'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Points system
    total_points = db.Column(db.Integer, default=0)
    current_points = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.Integer, default=0)
    experience_to_next_level = db.Column(db.Integer, default=100)
    
    # Streaks
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    last_activity_date = db.Column(db.DateTime, nullable=True)
    
    # Statistics
    total_activities = db.Column(db.Integer, default=0)
    total_assessments_completed = db.Column(db.Integer, default=0)
    total_courses_completed = db.Column(db.Integer, default=0)
    
    # Last updated
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='points')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'total_points': self.total_points,
            'current_points': self.current_points,
            'level': self.level,
            'experience': self.experience,
            'experience_to_next_level': self.experience_to_next_level,
            'current_streak': self.current_streak,
            'longest_streak': self.longest_streak,
            'last_activity_date': self.last_activity_date.isoformat() if self.last_activity_date else None,
            'total_activities': self.total_activities,
            'total_assessments_completed': self.total_assessments_completed,
            'total_courses_completed': self.total_courses_completed,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
    
    def add_points(self, points, experience=0):
        """Add points and experience to user"""
        self.current_points += points
        self.total_points += points
        self.experience += experience
        
        # Check for level up
        while self.experience >= self.experience_to_next_level:
            self.level_up()
        
        self.last_updated = datetime.utcnow()
    
    def level_up(self):
        """Level up the user"""
        self.experience -= self.experience_to_next_level
        self.level += 1
        self.experience_to_next_level = int(self.experience_to_next_level * 1.2)  # 20% increase
    
    def update_streak(self):
        """Update user's activity streak"""
        today = datetime.utcnow().date()
        
        if self.last_activity_date:
            last_date = self.last_activity_date.date()
            if today == last_date:
                return  # Already updated today
            
            if today - last_date == timedelta(days=1):
                self.current_streak += 1
            else:
                self.current_streak = 1
        else:
            self.current_streak = 1
        
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
        
        self.last_activity_date = datetime.utcnow()

class Leaderboard(db.Model):
    """Leaderboards for different categories"""
    __tablename__ = 'leaderboards'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False)  # points, streak, assessments, etc.
    
    # Leaderboard configuration
    time_period = db.Column(db.String(20), default='all_time')  # daily, weekly, monthly, all_time
    max_entries = db.Column(db.Integer, default=100)
    is_active = db.Column(db.Boolean, default=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'time_period': self.time_period,
            'max_entries': self.max_entries,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

class LeaderboardEntry(db.Model):
    """Individual entries in leaderboards"""
    __tablename__ = 'leaderboard_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    leaderboard_id = db.Column(db.Integer, db.ForeignKey('leaderboards.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Entry data
    score = db.Column(db.Float, nullable=False)
    rank = db.Column(db.Integer, nullable=True)
    entry_data = db.Column(db.Text, nullable=True)  # JSON data about the entry
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    leaderboard = db.relationship('Leaderboard', backref='entries')
    user = db.relationship('User', backref='leaderboard_entries')
    
    def to_dict(self):
        return {
            'id': self.id,
            'leaderboard_id': self.leaderboard_id,
            'user_id': self.user_id,
            'score': self.score,
            'rank': self.rank,
            'entry_data': json.loads(self.entry_data) if self.entry_data else {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user': {
                'id': self.user.id,
                'name': self.user.get_full_name(),
                'email': self.user.email
            } if self.user else None
        }

class Achievement(db.Model):
    """Achievement system for tracking user progress"""
    __tablename__ = 'achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Achievement tracking
    achievement_type = db.Column(db.String(50), nullable=False)  # login_streak, assessment_score, etc.
    current_value = db.Column(db.Integer, default=0)
    target_value = db.Column(db.Integer, nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Progress tracking
    progress_percentage = db.Column(db.Float, default=0.0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='achievements')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'achievement_type': self.achievement_type,
            'current_value': self.current_value,
            'target_value': self.target_value,
            'is_completed': self.is_completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'progress_percentage': self.progress_percentage,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
    
    def update_progress(self, new_value):
        """Update achievement progress"""
        self.current_value = new_value
        self.progress_percentage = min(100.0, (new_value / self.target_value) * 100)
        
        if new_value >= self.target_value and not self.is_completed:
            self.complete_achievement()
        
        self.last_updated = datetime.utcnow()
    
    def complete_achievement(self):
        """Mark achievement as completed"""
        self.is_completed = True
        self.completed_at = datetime.utcnow()
        self.progress_percentage = 100.0

class Notification(db.Model):
    """Gamification notifications and rewards"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Notification content
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # badge_earned, level_up, streak, etc.
    
    # Notification data
    data = db.Column(db.Text, nullable=True)  # JSON data for rich notifications
    icon_name = db.Column(db.String(50), nullable=True)
    color = db.Column(db.String(20), nullable=True)
    
    # Status
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='notifications')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'data': json.loads(self.data) if self.data else {},
            'icon_name': self.icon_name,
            'color': self.color,
            'is_read': self.is_read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = datetime.utcnow()

class GamificationEngine:
    """Engine for managing gamification features"""
    
    def __init__(self):
        self.badge_checkers = {}
        self.achievement_checkers = {}
    
    def check_badges(self, user_id, activity_type, activity_value, context=None):
        """Check if user should earn any badges"""
        from gamification_models import Badge, UserBadge
        
        # Get user's current badges
        user_badges = UserBadge.query.filter_by(user_id=user_id).all()
        earned_badge_ids = [ub.badge_id for ub in user_badges]
        
        # Get applicable badges
        applicable_badges = Badge.query.filter(
            Badge.criteria_type == activity_type,
            Badge.is_active == True,
            ~Badge.id.in_(earned_badge_ids)
        ).all()
        
        new_badges = []
        
        for badge in applicable_badges:
            if self._check_badge_criteria(badge, activity_value, context):
                new_badge = self._award_badge(user_id, badge, activity_value, context)
                new_badges.append(new_badge)
        
        return new_badges
    
    def check_achievements(self, user_id, achievement_type, new_value):
        """Check and update achievements"""
        from gamification_models import Achievement
        
        achievement = Achievement.query.filter_by(
            user_id=user_id,
            achievement_type=achievement_type
        ).first()
        
        if not achievement:
            # Create new achievement
            achievement = Achievement(
                user_id=user_id,
                achievement_type=achievement_type,
                target_value=self._get_achievement_target(achievement_type)
            )
            db.session.add(achievement)
        
        achievement.update_progress(new_value)
        db.session.commit()
        
        return achievement
    
    def update_leaderboard(self, leaderboard_id, user_id, score, entry_data=None):
        """Update leaderboard entry"""
        from gamification_models import LeaderboardEntry
        
        entry = LeaderboardEntry.query.filter_by(
            leaderboard_id=leaderboard_id,
            user_id=user_id
        ).first()
        
        if entry:
            entry.score = score
            entry.entry_data = json.dumps(entry_data) if entry_data else None
            entry.updated_at = datetime.utcnow()
        else:
            entry = LeaderboardEntry(
                leaderboard_id=leaderboard_id,
                user_id=user_id,
                score=score,
                entry_data=json.dumps(entry_data) if entry_data else None
            )
            db.session.add(entry)
        
        db.session.commit()
        
        # Recalculate ranks
        self._recalculate_leaderboard_ranks(leaderboard_id)
        
        return entry
    
    def create_notification(self, user_id, title, message, notification_type, data=None, icon=None, color=None):
        """Create a new notification"""
        from gamification_models import Notification
        
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            data=json.dumps(data) if data else None,
            icon_name=icon,
            color=color
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return notification
    
    def _check_badge_criteria(self, badge, activity_value, context):
        """Check if badge criteria are met"""
        if badge.criteria_type == 'points':
            return activity_value >= badge.criteria_value
        elif badge.criteria_type == 'streak':
            return activity_value >= badge.criteria_value
        elif badge.criteria_type == 'completion':
            return activity_value >= badge.criteria_value
        elif badge.criteria_type == 'score':
            return activity_value >= badge.criteria_value
        else:
            # Custom criteria checking
            config = json.loads(badge.criteria_config) if badge.criteria_config else {}
            return self._check_custom_criteria(badge.criteria_type, activity_value, context, config)
    
    def _check_custom_criteria(self, criteria_type, activity_value, context, config):
        """Check custom badge criteria"""
        # Implement custom criteria checking logic
        return False
    
    def _award_badge(self, user_id, badge, activity_value, context):
        """Award a badge to a user"""
        from gamification_models import UserBadge, UserPoints
        
        # Create user badge record
        user_badge = UserBadge(
            user_id=user_id,
            badge_id=badge.id,
            progress_value=activity_value,
            context_data=json.dumps(context) if context else None
        )
        
        db.session.add(user_badge)
        
        # Update badge statistics
        badge.times_awarded += 1
        
        # Award points and experience
        user_points = UserPoints.query.filter_by(user_id=user_id).first()
        if user_points:
            user_points.add_points(badge.points_reward, badge.experience_reward)
        
        db.session.commit()
        
        # Create notification
        self.create_notification(
            user_id=user_id,
            title=f"Badge Earned: {badge.name}",
            message=f"Congratulations! You've earned the {badge.name} badge.",
            notification_type='badge_earned',
            data={'badge_id': badge.id, 'points_reward': badge.points_reward},
            icon=badge.icon_name,
            color=badge.color
        )
        
        return user_badge
    
    def _get_achievement_target(self, achievement_type):
        """Get target value for achievement type"""
        targets = {
            'login_streak': 7,
            'assessment_score_90': 5,
            'courses_completed': 3,
            'total_points': 1000,
            'perfect_assessment': 1
        }
        return targets.get(achievement_type, 10)
    
    def _recalculate_leaderboard_ranks(self, leaderboard_id):
        """Recalculate ranks for a leaderboard"""
        from gamification_models import LeaderboardEntry
        
        entries = LeaderboardEntry.query.filter_by(leaderboard_id=leaderboard_id).order_by(
            LeaderboardEntry.score.desc()
        ).all()
        
        for i, entry in enumerate(entries):
            entry.rank = i + 1
        
        db.session.commit()

# Global gamification engine instance
gamification_engine = GamificationEngine() 