from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from models import db
import json
import numpy as np
from enum import Enum

class GradingType(Enum):
    ESSAY = "essay"
    SHORT_ANSWER = "short_answer"
    CODE = "code"
    OPEN_ENDED = "open_ended"
    PROBLEM_SOLVING = "problem_solving"

class EvaluationCriteria(Enum):
    CONTENT_QUALITY = "content_quality"
    GRAMMAR_SPELLING = "grammar_spelling"
    LOGICAL_FLOW = "logical_flow"
    TECHNICAL_ACCURACY = "technical_accuracy"
    CREATIVITY = "creativity"
    COMPLETENESS = "completeness"

class AutoGradingModel(db.Model):
    """AI/ML models for auto-grading different types of responses"""
    __tablename__ = 'auto_grading_models'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    model_type = db.Column(db.String(50), nullable=False)  # nlp, code_analysis, etc.
    grading_type = db.Column(db.String(50), nullable=False)  # essay, short_answer, code
    
    # Model configuration
    model_config = db.Column(db.Text, nullable=True)  # JSON configuration
    version = db.Column(db.String(20), default='1.0')
    is_active = db.Column(db.Boolean, default=True)
    
    # Performance metrics
    accuracy = db.Column(db.Float, default=0.0)
    precision = db.Column(db.Float, default=0.0)
    recall = db.Column(db.Float, default=0.0)
    f1_score = db.Column(db.Float, default=0.0)
    
    # Training data
    training_samples = db.Column(db.Integer, default=0)
    last_trained = db.Column(db.DateTime, nullable=True)
    
    # Metadata
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.Text, nullable=True)
    
    # Relationships
    creator = db.relationship('User', backref='grading_models')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'model_type': self.model_type,
            'grading_type': self.grading_type,
            'model_config': json.loads(self.model_config) if self.model_config else {},
            'version': self.version,
            'is_active': self.is_active,
            'accuracy': self.accuracy,
            'precision': self.precision,
            'recall': self.recall,
            'f1_score': self.f1_score,
            'training_samples': self.training_samples,
            'last_trained': self.last_trained.isoformat() if self.last_trained else None,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'description': self.description
        }

class GradingCriteria(db.Model):
    """Evaluation criteria for different question types"""
    __tablename__ = 'grading_criteria'
    
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('adaptive_questions.id'), nullable=False)
    criteria_type = db.Column(db.String(50), nullable=False)  # content_quality, grammar, etc.
    weight = db.Column(db.Float, default=1.0)  # Weight in final score
    max_score = db.Column(db.Float, default=10.0)
    
    # Criteria details
    description = db.Column(db.Text, nullable=True)
    rubric_points = db.Column(db.Text, nullable=True)  # JSON array of rubric points
    keywords = db.Column(db.Text, nullable=True)  # JSON array of important keywords
    
    # Relationships
    question = db.relationship('AdaptiveQuestion', backref='grading_criteria')
    
    def to_dict(self):
        return {
            'id': self.id,
            'question_id': self.question_id,
            'criteria_type': self.criteria_type,
            'weight': self.weight,
            'max_score': self.max_score,
            'description': self.description,
            'rubric_points': json.loads(self.rubric_points) if self.rubric_points else [],
            'keywords': json.loads(self.keywords) if self.keywords else []
        }

class AutoGradingResult(db.Model):
    """Results of AI auto-grading for responses"""
    __tablename__ = 'auto_grading_results'
    
    id = db.Column(db.Integer, primary_key=True)
    response_id = db.Column(db.Integer, db.ForeignKey('assessment_responses.id'), nullable=False)
    model_id = db.Column(db.Integer, db.ForeignKey('auto_grading_models.id'), nullable=False)
    
    # Grading results
    overall_score = db.Column(db.Float, nullable=False)
    confidence_score = db.Column(db.Float, default=0.0)  # Model confidence in grading
    
    # Detailed scores by criteria
    criteria_scores = db.Column(db.Text, nullable=True)  # JSON object with criteria scores
    
    # AI-generated feedback
    feedback_text = db.Column(db.Text, nullable=True)
    suggestions = db.Column(db.Text, nullable=True)  # JSON array of suggestions
    strengths = db.Column(db.Text, nullable=True)  # JSON array of identified strengths
    weaknesses = db.Column(db.Text, nullable=True)  # JSON array of identified weaknesses
    
    # Processing metadata
    processing_time = db.Column(db.Float, default=0.0)  # Time taken to grade
    model_version = db.Column(db.String(20), nullable=True)
    graded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Quality control
    needs_human_review = db.Column(db.Boolean, default=False)
    review_reason = db.Column(db.Text, nullable=True)
    
    # Relationships
    response = db.relationship('AssessmentResponse', backref='auto_grading_results')
    model = db.relationship('AutoGradingModel', backref='grading_results')
    
    def to_dict(self):
        return {
            'id': self.id,
            'response_id': self.response_id,
            'model_id': self.model_id,
            'overall_score': self.overall_score,
            'confidence_score': self.confidence_score,
            'criteria_scores': json.loads(self.criteria_scores) if self.criteria_scores else {},
            'feedback_text': self.feedback_text,
            'suggestions': json.loads(self.suggestions) if self.suggestions else [],
            'strengths': json.loads(self.strengths) if self.strengths else [],
            'weaknesses': json.loads(self.weaknesses) if self.weaknesses else [],
            'processing_time': self.processing_time,
            'model_version': self.model_version,
            'graded_at': self.graded_at.isoformat() if self.graded_at else None,
            'needs_human_review': self.needs_human_review,
            'review_reason': self.review_reason
        }

class HumanReview(db.Model):
    """Human review of auto-graded responses for quality control"""
    __tablename__ = 'human_reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    grading_result_id = db.Column(db.Integer, db.ForeignKey('auto_grading_results.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Review results
    human_score = db.Column(db.Float, nullable=True)
    score_difference = db.Column(db.Float, default=0.0)  # Difference from AI score
    
    # Review feedback
    review_notes = db.Column(db.Text, nullable=True)
    ai_accuracy_rating = db.Column(db.Integer, nullable=True)  # 1-5 scale
    feedback_quality_rating = db.Column(db.Integer, nullable=True)  # 1-5 scale
    
    # Review metadata
    reviewed_at = db.Column(db.DateTime, default=datetime.utcnow)
    review_duration = db.Column(db.Float, default=0.0)  # Time taken for review
    
    # Relationships
    grading_result = db.relationship('AutoGradingResult', backref='human_reviews')
    reviewer = db.relationship('User', backref='grading_reviews')
    
    def to_dict(self):
        return {
            'id': self.id,
            'grading_result_id': self.grading_result_id,
            'reviewer_id': self.reviewer_id,
            'human_score': self.human_score,
            'score_difference': self.score_difference,
            'review_notes': self.review_notes,
            'ai_accuracy_rating': self.ai_accuracy_rating,
            'feedback_quality_rating': self.feedback_quality_rating,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'review_duration': self.review_duration
        }

class GradingAnalytics(db.Model):
    """Analytics for auto-grading system performance"""
    __tablename__ = 'grading_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('auto_grading_models.id'), nullable=False)
    
    # Performance metrics
    total_graded = db.Column(db.Integer, default=0)
    average_processing_time = db.Column(db.Float, default=0.0)
    average_confidence = db.Column(db.Float, default=0.0)
    
    # Accuracy metrics
    human_review_rate = db.Column(db.Float, default=0.0)  # Percentage requiring human review
    average_score_difference = db.Column(db.Float, default=0.0)  # Average difference from human scores
    accuracy_trend = db.Column(db.Text, nullable=True)  # JSON array of accuracy over time
    
    # Usage statistics
    daily_grading_volume = db.Column(db.Integer, default=0)
    peak_usage_hour = db.Column(db.Integer, nullable=True)
    most_graded_question_types = db.Column(db.Text, nullable=True)  # JSON object
    
    # Quality metrics
    feedback_satisfaction_score = db.Column(db.Float, default=0.0)  # Student satisfaction with feedback
    common_feedback_themes = db.Column(db.Text, nullable=True)  # JSON array of common feedback patterns
    
    # Last updated
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    model = db.relationship('AutoGradingModel', backref='analytics')
    
    def to_dict(self):
        return {
            'id': self.id,
            'model_id': self.model_id,
            'total_graded': self.total_graded,
            'average_processing_time': self.average_processing_time,
            'average_confidence': self.average_confidence,
            'human_review_rate': self.human_review_rate,
            'average_score_difference': self.average_score_difference,
            'accuracy_trend': json.loads(self.accuracy_trend) if self.accuracy_trend else [],
            'daily_grading_volume': self.daily_grading_volume,
            'peak_usage_hour': self.peak_usage_hour,
            'most_graded_question_types': json.loads(self.most_graded_question_types) if self.most_graded_question_types else {},
            'feedback_satisfaction_score': self.feedback_satisfaction_score,
            'common_feedback_themes': json.loads(self.common_feedback_themes) if self.common_feedback_themes else [],
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

class AutoGradingEngine:
    """Engine for AI-powered auto-grading"""
    
    def __init__(self):
        self.nlp_models = {}
        self.code_analyzers = {}
        self.feedback_generators = {}
    
    def grade_essay(self, response_text, criteria, model_config=None):
        """Grade essay responses using NLP"""
        # Simulate NLP-based grading
        scores = {}
        feedback = []
        strengths = []
        weaknesses = []
        
        # Content quality analysis
        content_score = self._analyze_content_quality(response_text, criteria.get('keywords', []))
        scores['content_quality'] = content_score
        
        # Grammar and spelling check
        grammar_score = self._check_grammar_spelling(response_text)
        scores['grammar_spelling'] = grammar_score
        
        # Logical flow analysis
        flow_score = self._analyze_logical_flow(response_text)
        scores['logical_flow'] = flow_score
        
        # Generate feedback
        if content_score < 7:
            weaknesses.append("Content could be more comprehensive")
            feedback.append("Consider expanding on key points with more detail")
        
        if grammar_score < 8:
            weaknesses.append("Some grammar and spelling issues")
            feedback.append("Review grammar and spelling before submitting")
        
        if flow_score > 8:
            strengths.append("Excellent logical organization")
        
        # Calculate overall score
        weights = criteria.get('weights', {'content_quality': 0.5, 'grammar_spelling': 0.3, 'logical_flow': 0.2})
        overall_score = sum(scores[k] * weights.get(k, 1.0) for k in scores.keys())
        
        return {
            'overall_score': min(10.0, overall_score),
            'criteria_scores': scores,
            'feedback_text': self._generate_feedback_text(feedback, strengths, weaknesses),
            'suggestions': feedback,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'confidence_score': 0.85
        }
    
    def grade_code(self, code_text, test_cases, criteria):
        """Grade code submissions"""
        # Simulate code analysis
        scores = {}
        feedback = []
        
        # Syntax check
        syntax_score = self._check_code_syntax(code_text)
        scores['syntax'] = syntax_score
        
        # Test case execution
        test_score = self._run_test_cases(code_text, test_cases)
        scores['test_cases'] = test_score
        
        # Code quality
        quality_score = self._analyze_code_quality(code_text)
        scores['code_quality'] = quality_score
        
        # Generate feedback
        if syntax_score < 8:
            feedback.append("Check for syntax errors in your code")
        
        if test_score < 7:
            feedback.append("Some test cases are failing. Review your logic")
        
        overall_score = sum(scores.values()) / len(scores)
        
        return {
            'overall_score': min(10.0, overall_score),
            'criteria_scores': scores,
            'feedback_text': f"Code analysis complete. Score: {overall_score:.1f}/10",
            'suggestions': feedback,
            'strengths': [],
            'weaknesses': [],
            'confidence_score': 0.90
        }
    
    def _analyze_content_quality(self, text, keywords):
        """Analyze content quality based on keywords and length"""
        if not text:
            return 0.0
        
        # Simple content analysis
        word_count = len(text.split())
        keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text.lower())
        
        # Score based on length and keyword coverage
        length_score = min(10.0, word_count / 10)  # 100 words = 10 points
        keyword_score = min(10.0, keyword_matches * 2)  # 5 keywords = 10 points
        
        return (length_score + keyword_score) / 2
    
    def _check_grammar_spelling(self, text):
        """Check grammar and spelling (simplified)"""
        if not text:
            return 0.0
        
        # Simple grammar check (in real implementation, use libraries like language-tool-python)
        common_errors = ['teh', 'recieve', 'seperate', 'definately']
        error_count = sum(1 for error in common_errors if error in text.lower())
        
        # Score based on error count
        if error_count == 0:
            return 10.0
        elif error_count <= 2:
            return 8.0
        elif error_count <= 5:
            return 6.0
        else:
            return 4.0
    
    def _analyze_logical_flow(self, text):
        """Analyze logical flow of text"""
        if not text:
            return 0.0
        
        # Simple flow analysis based on paragraph structure and transition words
        paragraphs = text.split('\n\n')
        transition_words = ['however', 'therefore', 'furthermore', 'moreover', 'consequently']
        
        transition_count = sum(1 for word in transition_words if word in text.lower())
        structure_score = min(10.0, len(paragraphs) * 2)  # 5 paragraphs = 10 points
        transition_score = min(10.0, transition_count * 2)  # 5 transitions = 10 points
        
        return (structure_score + transition_score) / 2
    
    def _check_code_syntax(self, code):
        """Check code syntax (simplified)"""
        # In real implementation, use AST parsing or language-specific tools
        if 'def ' in code and 'return' in code:
            return 9.0
        elif 'def ' in code:
            return 7.0
        else:
            return 5.0
    
    def _run_test_cases(self, code, test_cases):
        """Run test cases against code (simplified)"""
        # In real implementation, execute code safely
        return 8.0  # Placeholder
    
    def _analyze_code_quality(self, code):
        """Analyze code quality metrics"""
        if not code:
            return 0.0
        
        # Simple quality metrics
        lines = code.split('\n')
        comments = sum(1 for line in lines if line.strip().startswith('#'))
        comment_ratio = comments / max(len(lines), 1)
        
        if comment_ratio > 0.1:
            return 9.0
        elif comment_ratio > 0.05:
            return 7.0
        else:
            return 5.0
    
    def _generate_feedback_text(self, suggestions, strengths, weaknesses):
        """Generate natural language feedback"""
        feedback_parts = []
        
        if strengths:
            feedback_parts.append(f"Strengths: {', '.join(strengths)}")
        
        if weaknesses:
            feedback_parts.append(f"Areas for improvement: {', '.join(weaknesses)}")
        
        if suggestions:
            feedback_parts.append(f"Suggestions: {', '.join(suggestions)}")
        
        return ". ".join(feedback_parts) if feedback_parts else "Good work! Keep practicing."

# Global grading engine instance
grading_engine = AutoGradingEngine() 