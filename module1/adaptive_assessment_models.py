from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from models import db
import json
import numpy as np
from enum import Enum

class QuestionType(Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    MATCHING = "matching"
    DRAG_DROP = "drag_drop"

class DifficultyLevel(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"

class AdaptiveQuestion(db.Model):
    """Store adaptive questions with difficulty levels and metadata"""
    __tablename__ = 'adaptive_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    
    # Question content
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(50), nullable=False)  # multiple_choice, true_false, etc.
    difficulty_level = db.Column(db.String(20), nullable=False)  # easy, medium, hard, expert
    points = db.Column(db.Integer, default=1)
    
    # Question options (JSON for multiple choice)
    options = db.Column(db.Text, nullable=True)  # JSON array of options
    correct_answer = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text, nullable=True)
    
    # Adaptive parameters
    initial_difficulty = db.Column(db.Float, default=0.5)  # 0-1 scale
    discrimination = db.Column(db.Float, default=1.0)  # Item discrimination parameter
    guessing = db.Column(db.Float, default=0.25)  # Guessing parameter
    time_limit = db.Column(db.Integer, default=60)  # seconds
    
    # Metadata
    tags = db.Column(db.Text, nullable=True)  # JSON array of tags
    learning_objectives = db.Column(db.Text, nullable=True)  # JSON array of objectives
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Statistics
    times_used = db.Column(db.Integer, default=0)
    correct_responses = db.Column(db.Integer, default=0)
    average_response_time = db.Column(db.Float, default=0.0)
    
    # Relationships
    topic = db.relationship('Topic', backref='adaptive_questions')
    course = db.relationship('Course', backref='adaptive_questions')
    creator = db.relationship('User', backref='created_questions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'topic_id': self.topic_id,
            'course_id': self.course_id,
            'question_text': self.question_text,
            'question_type': self.question_type,
            'difficulty_level': self.difficulty_level,
            'points': self.points,
            'options': json.loads(self.options) if self.options else [],
            'correct_answer': self.correct_answer,
            'explanation': self.explanation,
            'initial_difficulty': self.initial_difficulty,
            'discrimination': self.discrimination,
            'guessing': self.guessing,
            'time_limit': self.time_limit,
            'tags': json.loads(self.tags) if self.tags else [],
            'learning_objectives': json.loads(self.learning_objectives) if self.learning_objectives else [],
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'times_used': self.times_used,
            'correct_responses': self.correct_responses,
            'average_response_time': self.average_response_time
        }
    
    def get_difficulty_score(self):
        """Get current difficulty score based on performance"""
        if self.times_used == 0:
            return self.initial_difficulty
        
        success_rate = self.correct_responses / self.times_used
        # Adjust difficulty based on success rate
        if success_rate > 0.8:
            return min(1.0, self.initial_difficulty + 0.1)
        elif success_rate < 0.3:
            return max(0.0, self.initial_difficulty - 0.1)
        else:
            return self.initial_difficulty
    
    def update_statistics(self, is_correct, response_time):
        """Update question statistics after use"""
        self.times_used += 1
        if is_correct:
            self.correct_responses += 1
        
        # Update average response time
        if self.average_response_time == 0:
            self.average_response_time = response_time
        else:
            self.average_response_time = (self.average_response_time + response_time) / 2

class AdaptiveAssessment(db.Model):
    """Store adaptive assessment sessions"""
    __tablename__ = 'adaptive_assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=True)
    
    # Assessment configuration
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    assessment_type = db.Column(db.String(50), default='adaptive')  # adaptive, diagnostic, practice
    max_questions = db.Column(db.Integer, default=20)
    time_limit_minutes = db.Column(db.Integer, default=30)
    
    # Adaptive parameters
    initial_difficulty = db.Column(db.Float, default=0.5)
    difficulty_adjustment_rate = db.Column(db.Float, default=0.1)
    confidence_threshold = db.Column(db.Float, default=0.8)
    
    # Session state
    current_question_index = db.Column(db.Integer, default=0)
    current_difficulty = db.Column(db.Float, default=0.5)
    questions_answered = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
    
    # Timing
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    time_spent_minutes = db.Column(db.Integer, default=0)
    
    # Results
    final_score = db.Column(db.Float, nullable=True)
    proficiency_level = db.Column(db.String(20), nullable=True)  # beginner, intermediate, advanced, expert
    confidence_interval = db.Column(db.Float, nullable=True)
    
    # Status
    status = db.Column(db.String(20), default='in_progress')  # in_progress, completed, abandoned
    
    # Relationships
    user = db.relationship('User', backref='adaptive_assessments')
    course = db.relationship('Course', backref='adaptive_assessments')
    topic = db.relationship('Topic', backref='adaptive_assessments')
    responses = db.relationship('AssessmentResponse', backref='assessment', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'course_id': self.course_id,
            'topic_id': self.topic_id,
            'title': self.title,
            'description': self.description,
            'assessment_type': self.assessment_type,
            'max_questions': self.max_questions,
            'time_limit_minutes': self.time_limit_minutes,
            'initial_difficulty': self.initial_difficulty,
            'difficulty_adjustment_rate': self.difficulty_adjustment_rate,
            'confidence_threshold': self.confidence_threshold,
            'current_question_index': self.current_question_index,
            'current_difficulty': self.current_difficulty,
            'questions_answered': self.questions_answered,
            'correct_answers': self.correct_answers,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'time_spent_minutes': self.time_spent_minutes,
            'final_score': self.final_score,
            'proficiency_level': self.proficiency_level,
            'confidence_interval': self.confidence_interval,
            'status': self.status
        }
    
    def get_progress_percentage(self):
        """Get assessment progress percentage"""
        return (self.questions_answered / self.max_questions) * 100 if self.max_questions > 0 else 0
    
    def get_accuracy_rate(self):
        """Get current accuracy rate"""
        return (self.correct_answers / self.questions_answered) * 100 if self.questions_answered > 0 else 0
    
    def adjust_difficulty(self, is_correct, response_time):
        """Adjust difficulty based on response"""
        if self.questions_answered < 3:
            # Use initial questions to establish baseline
            return
        
        # Calculate difficulty adjustment
        if is_correct:
            # Increase difficulty if correct
            self.current_difficulty = min(1.0, self.current_difficulty + self.difficulty_adjustment_rate)
        else:
            # Decrease difficulty if incorrect
            self.current_difficulty = max(0.0, self.current_difficulty - self.difficulty_adjustment_rate)
    
    def complete_assessment(self):
        """Mark assessment as completed and calculate final results"""
        self.completed_at = datetime.utcnow()
        self.status = 'completed'
        
        # Calculate time spent
        if self.started_at:
            time_diff = self.completed_at - self.started_at
            self.time_spent_minutes = int(time_diff.total_seconds() / 60)
        
        # Calculate final score
        self.final_score = self.get_accuracy_rate()
        
        # Determine proficiency level
        if self.final_score >= 90:
            self.proficiency_level = 'expert'
        elif self.final_score >= 75:
            self.proficiency_level = 'advanced'
        elif self.final_score >= 60:
            self.proficiency_level = 'intermediate'
        else:
            self.proficiency_level = 'beginner'
        
        # Calculate confidence interval (simplified)
        if self.questions_answered > 0:
            standard_error = np.sqrt((self.final_score * (100 - self.final_score)) / self.questions_answered)
            self.confidence_interval = min(standard_error, 10.0)  # Cap at 10%

class AssessmentResponse(db.Model):
    """Store individual question responses"""
    __tablename__ = 'assessment_responses'
    
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('adaptive_assessments.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('adaptive_questions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Response data
    user_answer = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    points_earned = db.Column(db.Float, default=0.0)
    
    # Timing
    question_started_at = db.Column(db.DateTime, nullable=True)
    answered_at = db.Column(db.DateTime, default=datetime.utcnow)
    response_time_seconds = db.Column(db.Float, default=0.0)
    
    # Adaptive data
    question_difficulty = db.Column(db.Float, nullable=True)
    user_ability_estimate = db.Column(db.Float, nullable=True)
    
    # Feedback
    feedback_given = db.Column(db.Text, nullable=True)
    explanation_shown = db.Column(db.Boolean, default=False)
    
    # Relationships
    question = db.relationship('AdaptiveQuestion', backref='responses')
    user = db.relationship('User', backref='assessment_responses')
    
    def to_dict(self):
        return {
            'id': self.id,
            'assessment_id': self.assessment_id,
            'question_id': self.question_id,
            'user_id': self.user_id,
            'user_answer': self.user_answer,
            'is_correct': self.is_correct,
            'points_earned': self.points_earned,
            'question_started_at': self.question_started_at.isoformat() if self.question_started_at else None,
            'answered_at': self.answered_at.isoformat() if self.answered_at else None,
            'response_time_seconds': self.response_time_seconds,
            'question_difficulty': self.question_difficulty,
            'user_ability_estimate': self.user_ability_estimate,
            'feedback_given': self.feedback_given,
            'explanation_shown': self.explanation_shown
        }

class AssessmentAnalytics(db.Model):
    """Store aggregated assessment analytics"""
    __tablename__ = 'assessment_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=True)
    
    # Performance metrics
    total_assessments = db.Column(db.Integer, default=0)
    completed_assessments = db.Column(db.Integer, default=0)
    average_score = db.Column(db.Float, default=0.0)
    best_score = db.Column(db.Float, default=0.0)
    total_questions_answered = db.Column(db.Integer, default=0)
    total_correct_answers = db.Column(db.Integer, default=0)
    
    # Time metrics
    total_time_spent_minutes = db.Column(db.Integer, default=0)
    average_time_per_question = db.Column(db.Float, default=0.0)
    
    # Difficulty progression
    current_proficiency_level = db.Column(db.String(20), default='beginner')
    difficulty_progression = db.Column(db.Text, nullable=True)  # JSON array of difficulty levels
    strength_areas = db.Column(db.Text, nullable=True)  # JSON array of strong topics
    weak_areas = db.Column(db.Text, nullable=True)  # JSON array of weak topics
    
    # Engagement metrics
    last_assessment_date = db.Column(db.DateTime, nullable=True)
    assessment_frequency = db.Column(db.Float, default=0.0)  # assessments per week
    improvement_rate = db.Column(db.Float, default=0.0)  # score improvement over time
    
    # Last updated
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='assessment_analytics')
    course = db.relationship('Course', backref='assessment_analytics')
    topic = db.relationship('Topic', backref='assessment_analytics')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'course_id': self.course_id,
            'topic_id': self.topic_id,
            'total_assessments': self.total_assessments,
            'completed_assessments': self.completed_assessments,
            'average_score': self.average_score,
            'best_score': self.best_score,
            'total_questions_answered': self.total_questions_answered,
            'total_correct_answers': self.total_correct_answers,
            'total_time_spent_minutes': self.total_time_spent_minutes,
            'average_time_per_question': self.average_time_per_question,
            'current_proficiency_level': self.current_proficiency_level,
            'difficulty_progression': json.loads(self.difficulty_progression) if self.difficulty_progression else [],
            'strength_areas': json.loads(self.strength_areas) if self.strength_areas else [],
            'weak_areas': json.loads(self.weak_areas) if self.weak_areas else [],
            'last_assessment_date': self.last_assessment_date.isoformat() if self.last_assessment_date else None,
            'assessment_frequency': self.assessment_frequency,
            'improvement_rate': self.improvement_rate,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
    
    def get_accuracy_rate(self):
        """Get overall accuracy rate"""
        return (self.total_correct_answers / self.total_questions_answered) * 100 if self.total_questions_answered > 0 else 0
    
    def get_completion_rate(self):
        """Get assessment completion rate"""
        return (self.completed_assessments / self.total_assessments) * 100 if self.total_assessments > 0 else 0

class AdaptiveAssessmentEngine:
    """Engine for managing adaptive assessments"""
    
    def __init__(self):
        self.ability_estimation_method = 'irt'  # irt, bayesian, simple
    
    def select_next_question(self, assessment, user_responses):
        """Select the next question based on current performance"""
        if assessment.questions_answered >= assessment.max_questions:
            return None
        
        # Get available questions for the topic/course
        available_questions = AdaptiveQuestion.query.filter_by(
            topic_id=assessment.topic_id,
            course_id=assessment.course_id,
            is_active=True
        ).all()
        
        if not available_questions:
            return None
        
        # Filter out already answered questions
        answered_question_ids = [r.question_id for r in user_responses]
        available_questions = [q for q in available_questions if q.id not in answered_question_ids]
        
        if not available_questions:
            return None
        
        # Select question based on current difficulty
        target_difficulty = assessment.current_difficulty
        
        # Find questions close to target difficulty
        question_scores = []
        for question in available_questions:
            difficulty_diff = abs(question.get_difficulty_score() - target_difficulty)
            # Prefer questions with similar difficulty, but add some randomness
            score = 1.0 / (1.0 + difficulty_diff) + np.random.normal(0, 0.1)
            question_scores.append((question, score))
        
        # Sort by score and select top question
        question_scores.sort(key=lambda x: x[1], reverse=True)
        return question_scores[0][0] if question_scores else available_questions[0]
    
    def estimate_user_ability(self, user_responses):
        """Estimate user ability using IRT or other methods"""
        if not user_responses:
            return 0.5  # Default ability
        
        # Simple ability estimation based on performance
        correct_count = sum(1 for r in user_responses if r.is_correct)
        total_count = len(user_responses)
        
        if total_count == 0:
            return 0.5
        
        # Calculate average difficulty of answered questions
        avg_difficulty = np.mean([r.question_difficulty for r in user_responses if r.question_difficulty is not None])
        
        # Simple ability estimation
        performance = correct_count / total_count
        ability = performance * 0.7 + avg_difficulty * 0.3
        
        return max(0.0, min(1.0, ability))
    
    def should_terminate_assessment(self, assessment, user_responses):
        """Determine if assessment should end early"""
        if assessment.questions_answered < 5:
            return False  # Need minimum questions
        
        # Check if confidence threshold is met
        ability_estimate = self.estimate_user_ability(user_responses)
        
        # Calculate confidence based on number of questions and consistency
        if assessment.questions_answered >= 10:
            recent_responses = user_responses[-5:]  # Last 5 responses
            recent_consistency = sum(1 for r in recent_responses if r.is_correct) / len(recent_responses)
            
            # If recent performance is very consistent, we can be more confident
            if recent_consistency > 0.8 or recent_consistency < 0.2:
                return True
        
        return False
    
    def generate_feedback(self, response):
        """Generate personalized feedback for a response"""
        feedback = {
            'is_correct': response.is_correct,
            'points_earned': response.points_earned,
            'explanation': response.question.explanation if response.question.explanation else None,
            'suggestions': []
        }
        
        if response.is_correct:
            feedback['suggestions'].append("Great job! You've mastered this concept.")
        else:
            feedback['suggestions'].append("Consider reviewing the related material.")
            if response.response_time_seconds < 10:
                feedback['suggestions'].append("Take your time to read the question carefully.")
            elif response.response_time_seconds > 120:
                feedback['suggestions'].append("Try to work more efficiently on similar questions.")
        
        return feedback

# Global assessment engine instance
assessment_engine = AdaptiveAssessmentEngine() 