from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from models import db
import json

class LearningSession(db.Model):
    """Track individual learning sessions"""
    __tablename__ = 'learning_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=True)
    
    # Session details
    session_start = db.Column(db.DateTime, default=datetime.utcnow)
    session_end = db.Column(db.DateTime, nullable=True)
    duration_minutes = db.Column(db.Integer, default=0)
    session_type = db.Column(db.String(50), default='study')  # study, quiz, assignment, review
    
    # Activity tracking
    pages_viewed = db.Column(db.Integer, default=0)
    materials_accessed = db.Column(db.Integer, default=0)
    interactions_count = db.Column(db.Integer, default=0)
    
    # Device and location info
    device_type = db.Column(db.String(50), nullable=True)  # desktop, mobile, tablet
    browser = db.Column(db.String(100), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    
    # Session status
    is_active = db.Column(db.Boolean, default=True)
    was_completed = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = db.relationship('User', backref='learning_sessions')
    course = db.relationship('Course', backref='sessions')
    topic = db.relationship('Topic', backref='sessions')
    activities = db.relationship('LearningActivity', backref='session', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'course_id': self.course_id,
            'topic_id': self.topic_id,
            'session_start': self.session_start.isoformat() if self.session_start else None,
            'session_end': self.session_end.isoformat() if self.session_end else None,
            'duration_minutes': self.duration_minutes,
            'session_type': self.session_type,
            'pages_viewed': self.pages_viewed,
            'materials_accessed': self.materials_accessed,
            'interactions_count': self.interactions_count,
            'device_type': self.device_type,
            'browser': self.browser,
            'is_active': self.is_active,
            'was_completed': self.was_completed
        }
    
    def end_session(self):
        """End the current session and calculate duration"""
        if self.is_active:
            self.session_end = datetime.utcnow()
            self.is_active = False
            self.was_completed = True
            
            if self.session_start:
                duration = self.session_end - self.session_start
                self.duration_minutes = int(duration.total_seconds() / 60)
            
            return self.duration_minutes
        return 0

class LearningActivity(db.Model):
    """Track specific learning activities within sessions"""
    __tablename__ = 'learning_activities'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('learning_sessions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=True)
    material_id = db.Column(db.Integer, db.ForeignKey('learning_materials.id'), nullable=True)
    
    # Activity details
    activity_type = db.Column(db.String(50), nullable=False)  # lesson_view, quiz_take, assignment_submit, video_watch, etc.
    activity_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Timing
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    duration_seconds = db.Column(db.Integer, default=0)
    
    # Progress and performance
    progress_percentage = db.Column(db.Float, default=0.0)  # 0-100
    score = db.Column(db.Float, nullable=True)  # For quizzes/assignments
    max_score = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(50), default='started')  # started, in_progress, completed, abandoned
    
    # Additional data (JSON)
    activity_metadata = db.Column(db.Text, nullable=True)  # Store additional data as JSON
    
    # Relationships
    user = db.relationship('User', backref='learning_activities')
    course = db.relationship('Course', backref='activities')
    topic = db.relationship('Topic', backref='activities')
    material = db.relationship('LearningMaterial', backref='activities')
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'course_id': self.course_id,
            'topic_id': self.topic_id,
            'material_id': self.material_id,
            'activity_type': self.activity_type,
            'activity_name': self.activity_name,
            'description': self.description,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': self.duration_seconds,
            'progress_percentage': self.progress_percentage,
            'score': self.score,
            'max_score': self.max_score,
            'status': self.status,
            'activity_metadata': self.activity_metadata
        }
    
    def complete_activity(self, progress=100.0, score=None, max_score=None):
        """Mark activity as completed"""
        self.completed_at = datetime.utcnow()
        self.progress_percentage = progress
        self.status = 'completed'
        
        if score is not None:
            self.score = score
        if max_score is not None:
            self.max_score = max_score
        
        # Calculate duration
        if self.started_at:
            duration = self.completed_at - self.started_at
            self.duration_seconds = int(duration.total_seconds())
    
    def update_progress(self, progress_percentage):
        """Update progress percentage"""
        self.progress_percentage = min(100.0, max(0.0, progress_percentage))
        if self.progress_percentage >= 100:
            self.status = 'completed'
        elif self.progress_percentage > 0:
            self.status = 'in_progress'

class CourseProgress(db.Model):
    """Track overall course progress for each student"""
    __tablename__ = 'course_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    
    # Progress metrics
    overall_progress = db.Column(db.Float, default=0.0)  # 0-100
    topics_completed = db.Column(db.Integer, default=0)
    total_topics = db.Column(db.Integer, default=0)
    materials_completed = db.Column(db.Integer, default=0)
    total_materials = db.Column(db.Integer, default=0)
    
    # Time tracking
    total_time_spent_minutes = db.Column(db.Integer, default=0)
    last_activity = db.Column(db.DateTime, nullable=True)
    first_access = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Performance metrics
    average_quiz_score = db.Column(db.Float, default=0.0)
    quizzes_taken = db.Column(db.Integer, default=0)
    assignments_submitted = db.Column(db.Integer, default=0)
    assignments_graded = db.Column(db.Integer, default=0)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    completion_date = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='course_progress')
    course = db.relationship('Course', backref='student_progress')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'course_id': self.course_id,
            'overall_progress': self.overall_progress,
            'topics_completed': self.topics_completed,
            'total_topics': self.total_topics,
            'materials_completed': self.materials_completed,
            'total_materials': self.total_materials,
            'total_time_spent_minutes': self.total_time_spent_minutes,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'first_access': self.first_access.isoformat() if self.first_access else None,
            'average_quiz_score': self.average_quiz_score,
            'quizzes_taken': self.quizzes_taken,
            'assignments_submitted': self.assignments_submitted,
            'assignments_graded': self.assignments_graded,
            'is_active': self.is_active,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None
        }
    
    def update_progress(self):
        """Recalculate progress based on completed items"""
        if self.total_topics > 0:
            topic_progress = (self.topics_completed / self.total_topics) * 100
        else:
            topic_progress = 0
            
        if self.total_materials > 0:
            material_progress = (self.materials_completed / self.total_materials) * 100
        else:
            material_progress = 0
        
        # Overall progress is average of topic and material progress
        self.overall_progress = (topic_progress + material_progress) / 2
        
        # Check if course is completed
        if self.overall_progress >= 100:
            self.completion_date = datetime.utcnow()
    
    def add_time_spent(self, minutes):
        """Add time spent to total"""
        self.total_time_spent_minutes += minutes
        self.last_activity = datetime.utcnow()

class TopicProgress(db.Model):
    """Track progress for individual topics"""
    __tablename__ = 'topic_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    
    # Progress metrics
    progress_percentage = db.Column(db.Float, default=0.0)
    materials_completed = db.Column(db.Integer, default=0)
    total_materials = db.Column(db.Integer, default=0)
    time_spent_minutes = db.Column(db.Integer, default=0)
    
    # Completion status
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Performance
    quiz_scores = db.Column(db.Text, nullable=True)  # JSON array of quiz scores
    average_quiz_score = db.Column(db.Float, default=0.0)
    
    # Relationships
    user = db.relationship('User', backref='topic_progress')
    topic = db.relationship('Topic', backref='student_progress')
    course = db.relationship('Course', backref='topic_progress')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'topic_id': self.topic_id,
            'course_id': self.course_id,
            'progress_percentage': self.progress_percentage,
            'materials_completed': self.materials_completed,
            'total_materials': self.total_materials,
            'time_spent_minutes': self.time_spent_minutes,
            'is_completed': self.is_completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'quiz_scores': self.quiz_scores,
            'average_quiz_score': self.average_quiz_score
        }
    
    def update_progress(self):
        """Update progress based on completed materials"""
        if self.total_materials > 0:
            self.progress_percentage = (self.materials_completed / self.total_materials) * 100
        else:
            self.progress_percentage = 0
        
        # Check if topic is completed
        if self.progress_percentage >= 100 and not self.is_completed:
            self.is_completed = True
            self.completed_at = datetime.utcnow()
    
    def add_quiz_score(self, score):
        """Add a new quiz score"""
        scores = []
        if self.quiz_scores:
            try:
                scores = json.loads(self.quiz_scores)
            except:
                scores = []
        
        scores.append(score)
        self.quiz_scores = json.dumps(scores)
        
        # Update average
        if scores:
            self.average_quiz_score = sum(scores) / len(scores)

class LearningAnalytics(db.Model):
    """Store aggregated analytics data for quick access"""
    __tablename__ = 'learning_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)
    
    # Daily/weekly/monthly stats
    period_type = db.Column(db.String(20), nullable=False)  # daily, weekly, monthly
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    
    # Activity metrics
    sessions_count = db.Column(db.Integer, default=0)
    total_time_minutes = db.Column(db.Integer, default=0)
    activities_completed = db.Column(db.Integer, default=0)
    materials_accessed = db.Column(db.Integer, default=0)
    
    # Performance metrics
    average_score = db.Column(db.Float, default=0.0)
    quizzes_taken = db.Column(db.Integer, default=0)
    assignments_submitted = db.Column(db.Integer, default=0)
    
    # Engagement metrics
    login_frequency = db.Column(db.Integer, default=0)
    streak_days = db.Column(db.Integer, default=0)
    
    # Calculated metrics
    efficiency_score = db.Column(db.Float, default=0.0)  # activities per hour
    consistency_score = db.Column(db.Float, default=0.0)  # regularity of study
    
    # Relationships
    user = db.relationship('User', backref='learning_analytics')
    course = db.relationship('Course', backref='analytics')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'course_id': self.course_id,
            'period_type': self.period_type,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'sessions_count': self.sessions_count,
            'total_time_minutes': self.total_time_minutes,
            'activities_completed': self.activities_completed,
            'materials_accessed': self.materials_accessed,
            'average_score': self.average_score,
            'quizzes_taken': self.quizzes_taken,
            'assignments_submitted': self.assignments_submitted,
            'login_frequency': self.login_frequency,
            'streak_days': self.streak_days,
            'efficiency_score': self.efficiency_score,
            'consistency_score': self.consistency_score
        }

class StudyStreak(db.Model):
    """Track consecutive days of study"""
    __tablename__ = 'study_streaks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Streak information
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    last_study_date = db.Column(db.Date, nullable=True)
    streak_start_date = db.Column(db.Date, nullable=True)
    
    # Study history
    study_dates = db.Column(db.Text, nullable=True)  # JSON array of study dates
    
    # Relationships
    user = db.relationship('User', backref='study_streak')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'current_streak': self.current_streak,
            'longest_streak': self.longest_streak,
            'last_study_date': self.last_study_date.isoformat() if self.last_study_date else None,
            'streak_start_date': self.streak_start_date.isoformat() if self.streak_start_date else None,
            'study_dates': self.study_dates
        }
    
    def update_streak(self, study_date=None):
        """Update streak based on study activity"""
        if study_date is None:
            study_date = datetime.utcnow().date()
        
        # Get existing study dates
        dates = []
        if self.study_dates:
            try:
                dates = json.loads(self.study_dates)
            except:
                dates = []
        
        # Add new date if not already present
        date_str = study_date.isoformat()
        if date_str not in dates:
            dates.append(date_str)
            dates.sort()
            self.study_dates = json.dumps(dates)
        
        # Calculate current streak
        self.current_streak = self._calculate_current_streak(dates)
        
        # Update longest streak
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
        
        self.last_study_date = study_date
    
    def _calculate_current_streak(self, dates):
        """Calculate current consecutive days streak"""
        if not dates:
            return 0
        
        today = datetime.utcnow().date()
        streak = 0
        
        # Check consecutive days backwards from today
        for i in range(len(dates) - 1, -1, -1):
            date = datetime.strptime(dates[i], '%Y-%m-%d').date()
            if (today - date).days == streak:
                streak += 1
            else:
                break
        
        return streak 