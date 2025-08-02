from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash
import uuid

# Import the same db instance from models.py
from models import db

class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category = db.Column(db.String(100), nullable=True)
    level = db.Column(db.String(50), nullable=True)  # Beginner, Intermediate, Advanced
    duration_hours = db.Column(db.Float, default=0.0)
    max_students = db.Column(db.Integer, default=50)
    is_active = db.Column(db.Boolean, default=True)
    is_public = db.Column(db.Boolean, default=True)
    is_approved = db.Column(db.Boolean, default=True)  # For moderation
    is_reported = db.Column(db.Boolean, default=False)  # For reporting
    is_removed = db.Column(db.Boolean, default=False)  # For removal
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    rejected_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    rejected_at = db.Column(db.DateTime, nullable=True)
    report_resolved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    report_resolved_at = db.Column(db.DateTime, nullable=True)
    removed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    removed_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    report_resolution = db.Column(db.Text, nullable=True)
    removal_reason = db.Column(db.Text, nullable=True)
    thumbnail_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    instructor = db.relationship('User', backref='courses_teaching', foreign_keys=[instructor_id])
    topics = db.relationship('Topic', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    enrollments = db.relationship('Enrollment', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    assignments = db.relationship('Assignment', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'code': self.code,
            'instructor_id': self.instructor_id,
            'instructor_name': self.instructor.get_full_name() if self.instructor else None,
            'category': self.category,
            'level': self.level,
            'duration_hours': self.duration_hours,
            'max_students': self.max_students,
            'is_active': self.is_active,
            'is_public': self.is_public,
            'is_approved': self.is_approved,
            'is_reported': self.is_reported,
            'is_removed': self.is_removed,
            'thumbnail_url': self.thumbnail_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'topics_count': self.topics.count(),
            'enrollments_count': self.enrollments.count()
        }

class Topic(db.Model):
    __tablename__ = 'topics'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    order_index = db.Column(db.Integer, default=0)
    duration_minutes = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    materials = db.relationship('LearningMaterial', backref='topic', lazy='dynamic', cascade='all, delete-orphan')
    quizzes = db.relationship('Quiz', backref='topic', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'course_id': self.course_id,
            'order_index': self.order_index,
            'duration_minutes': self.duration_minutes,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'materials_count': self.materials.count(),
            'quizzes_count': self.quizzes.count()
        }

class LearningMaterial(db.Model):
    __tablename__ = 'learning_materials'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=False)
    material_type = db.Column(db.String(50), nullable=False)  # video, document, presentation, link
    file_url = db.Column(db.String(500), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)  # in bytes
    duration_minutes = db.Column(db.Integer, nullable=True)  # for videos
    order_index = db.Column(db.Integer, default=0)
    is_required = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    is_approved = db.Column(db.Boolean, default=True)  # For moderation
    is_reported = db.Column(db.Boolean, default=False)  # For reporting
    is_removed = db.Column(db.Boolean, default=False)  # For removal
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    rejected_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    rejected_at = db.Column(db.DateTime, nullable=True)
    report_resolved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    report_resolved_at = db.Column(db.DateTime, nullable=True)
    removed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    removed_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    report_resolution = db.Column(db.Text, nullable=True)
    removal_reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'topic_id': self.topic_id,
            'material_type': self.material_type,
            'file_url': self.file_url,
            'file_size': self.file_size,
            'duration_minutes': self.duration_minutes,
            'order_index': self.order_index,
            'is_required': self.is_required,
            'is_active': self.is_active,
            'is_approved': self.is_approved,
            'is_reported': self.is_reported,
            'is_removed': self.is_removed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Video(db.Model):
    __tablename__ = 'videos'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    material_id = db.Column(db.Integer, db.ForeignKey('learning_materials.id'), nullable=False)
    video_url = db.Column(db.String(500), nullable=False)
    thumbnail_url = db.Column(db.String(500), nullable=True)
    duration_seconds = db.Column(db.Integer, nullable=True)
    quality = db.Column(db.String(20), nullable=True)  # 720p, 1080p, etc.
    is_processed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    material = db.relationship('LearningMaterial', backref='video')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'material_id': self.material_id,
            'video_url': self.video_url,
            'thumbnail_url': self.thumbnail_url,
            'duration_seconds': self.duration_seconds,
            'quality': self.quality,
            'is_processed': self.is_processed,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Quiz(db.Model):
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=False)
    quiz_type = db.Column(db.String(50), default='multiple_choice')  # multiple_choice, true_false, essay
    time_limit_minutes = db.Column(db.Integer, nullable=True)
    passing_score = db.Column(db.Integer, default=70)  # percentage
    max_attempts = db.Column(db.Integer, default=3)
    is_active = db.Column(db.Boolean, default=True)
    is_approved = db.Column(db.Boolean, default=True)  # For moderation
    is_reported = db.Column(db.Boolean, default=False)  # For reporting
    is_removed = db.Column(db.Boolean, default=False)  # For removal
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    rejected_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    rejected_at = db.Column(db.DateTime, nullable=True)
    report_resolved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    report_resolved_at = db.Column(db.DateTime, nullable=True)
    removed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    removed_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    report_resolution = db.Column(db.Text, nullable=True)
    removal_reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    questions = db.relationship('QuizQuestion', backref='quiz', lazy='dynamic', cascade='all, delete-orphan')
    attempts = db.relationship('QuizAttempt', backref='quiz', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'topic_id': self.topic_id,
            'quiz_type': self.quiz_type,
            'time_limit_minutes': self.time_limit_minutes,
            'passing_score': self.passing_score,
            'max_attempts': self.max_attempts,
            'is_active': self.is_active,
            'is_approved': self.is_approved,
            'is_reported': self.is_reported,
            'is_removed': self.is_removed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'questions_count': self.questions.count()
        }

class QuizQuestion(db.Model):
    __tablename__ = 'quiz_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(50), default='multiple_choice')  # multiple_choice, true_false, essay
    points = db.Column(db.Integer, default=1)
    order_index = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    options = db.relationship('QuizOption', backref='question', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'quiz_id': self.quiz_id,
            'question_text': self.question_text,
            'question_type': self.question_type,
            'points': self.points,
            'order_index': self.order_index,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'options': [option.to_dict() for option in self.options]
        }

class QuizOption(db.Model):
    __tablename__ = 'quiz_options'
    
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_questions.id'), nullable=False)
    option_text = db.Column(db.String(500), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    order_index = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'question_id': self.question_id,
            'option_text': self.option_text,
            'is_correct': self.is_correct,
            'order_index': self.order_index
        }

class Assignment(db.Model):
    __tablename__ = 'assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=True)
    assignment_type = db.Column(db.String(50), default='homework')  # homework, project, exam
    due_date = db.Column(db.DateTime, nullable=False)
    max_points = db.Column(db.Integer, default=100)
    instructions = db.Column(db.Text, nullable=True)
    attachment_url = db.Column(db.String(500), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_approved = db.Column(db.Boolean, default=True)  # For moderation
    is_reported = db.Column(db.Boolean, default=False)  # For reporting
    is_removed = db.Column(db.Boolean, default=False)  # For removal
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    rejected_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    rejected_at = db.Column(db.DateTime, nullable=True)
    report_resolved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    report_resolved_at = db.Column(db.DateTime, nullable=True)
    removed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    removed_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    report_resolution = db.Column(db.Text, nullable=True)
    removal_reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    topic = db.relationship('Topic', backref='assignments')
    submissions = db.relationship('AssignmentSubmission', backref='assignment', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'course_id': self.course_id,
            'topic_id': self.topic_id,
            'assignment_type': self.assignment_type,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'max_points': self.max_points,
            'instructions': self.instructions,
            'attachment_url': self.attachment_url,
            'is_active': self.is_active,
            'is_approved': self.is_approved,
            'is_reported': self.is_reported,
            'is_removed': self.is_removed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'submissions_count': self.submissions.count()
        }

class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    completion_date = db.Column(db.DateTime, nullable=True)
    progress_percentage = db.Column(db.Float, default=0.0)
    grade = db.Column(db.String(10), nullable=True)  # A, B, C, D, F
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    student = db.relationship('User', backref='enrollments')
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'course_id': self.course_id,
            'enrollment_date': self.enrollment_date.isoformat() if self.enrollment_date else None,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'progress_percentage': self.progress_percentage,
            'grade': self.grade,
            'is_active': self.is_active
        }

class QuizAttempt(db.Model):
    __tablename__ = 'quiz_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    attempt_number = db.Column(db.Integer, default=1)
    score = db.Column(db.Float, default=0.0)
    max_score = db.Column(db.Float, default=0.0)
    percentage = db.Column(db.Float, default=0.0)
    passed = db.Column(db.Boolean, default=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    student = db.relationship('User', backref='quiz_attempts')
    answers = db.relationship('QuizAnswer', backref='attempt', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'quiz_id': self.quiz_id,
            'attempt_number': self.attempt_number,
            'score': self.score,
            'max_score': self.max_score,
            'percentage': self.percentage,
            'passed': self.passed,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class QuizAnswer(db.Model):
    __tablename__ = 'quiz_answers'
    
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('quiz_attempts.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_questions.id'), nullable=False)
    selected_option_id = db.Column(db.Integer, db.ForeignKey('quiz_options.id'), nullable=True)
    answer_text = db.Column(db.Text, nullable=True)  # for essay questions
    is_correct = db.Column(db.Boolean, default=False)
    points_earned = db.Column(db.Float, default=0.0)
    answered_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    question = db.relationship('QuizQuestion', backref='answers')
    selected_option = db.relationship('QuizOption', backref='answers')
    
    def to_dict(self):
        return {
            'id': self.id,
            'attempt_id': self.attempt_id,
            'question_id': self.question_id,
            'selected_option_id': self.selected_option_id,
            'answer_text': self.answer_text,
            'is_correct': self.is_correct,
            'points_earned': self.points_earned,
            'answered_at': self.answered_at.isoformat() if self.answered_at else None
        }

class AssignmentSubmission(db.Model):
    __tablename__ = 'assignment_submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'), nullable=False)
    submission_text = db.Column(db.Text, nullable=True)
    attachment_url = db.Column(db.String(500), nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    graded_at = db.Column(db.DateTime, nullable=True)
    score = db.Column(db.Float, nullable=True)
    max_score = db.Column(db.Float, nullable=True)
    feedback = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='submitted')  # submitted, graded, late
    
    # Relationships
    student = db.relationship('User', backref='assignment_submissions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'assignment_id': self.assignment_id,
            'submission_text': self.submission_text,
            'attachment_url': self.attachment_url,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'graded_at': self.graded_at.isoformat() if self.graded_at else None,
            'score': self.score,
            'max_score': self.max_score,
            'feedback': self.feedback,
            'status': self.status
        } 