from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from models import db
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import pickle
import os

class UserPreference(db.Model):
    """Store user preferences and interests"""
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Learning preferences
    preferred_difficulty = db.Column(db.String(20), default='intermediate')  # beginner, intermediate, advanced
    preferred_learning_style = db.Column(db.String(50), nullable=True)  # visual, auditory, kinesthetic, reading
    preferred_content_type = db.Column(db.String(50), nullable=True)  # video, text, interactive, quiz
    
    # Subject interests (JSON array)
    subject_interests = db.Column(db.Text, nullable=True)  # ["math", "science", "history"]
    topic_interests = db.Column(db.Text, nullable=True)  # ["algebra", "physics", "world-war-2"]
    
    # Time preferences
    preferred_study_time = db.Column(db.String(20), nullable=True)  # morning, afternoon, evening, night
    preferred_session_duration = db.Column(db.Integer, default=30)  # minutes
    
    # Device preferences
    preferred_device = db.Column(db.String(20), nullable=True)  # desktop, mobile, tablet
    
    # Notification preferences
    email_notifications = db.Column(db.Boolean, default=True)
    push_notifications = db.Column(db.Boolean, default=True)
    recommendation_frequency = db.Column(db.String(20), default='daily')  # daily, weekly, monthly
    
    # Relationships
    user = db.relationship('User', backref='preferences')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'preferred_difficulty': self.preferred_difficulty,
            'preferred_learning_style': self.preferred_learning_style,
            'preferred_content_type': self.preferred_content_type,
            'subject_interests': json.loads(self.subject_interests) if self.subject_interests else [],
            'topic_interests': json.loads(self.topic_interests) if self.topic_interests else [],
            'preferred_study_time': self.preferred_study_time,
            'preferred_session_duration': self.preferred_session_duration,
            'preferred_device': self.preferred_device,
            'email_notifications': self.email_notifications,
            'push_notifications': self.push_notifications,
            'recommendation_frequency': self.recommendation_frequency
        }
    
    def update_interests(self, subjects=None, topics=None):
        """Update user interests"""
        if subjects:
            self.subject_interests = json.dumps(subjects)
        if topics:
            self.topic_interests = json.dumps(topics)

class LearningPattern(db.Model):
    """Track user learning patterns and behaviors"""
    __tablename__ = 'learning_patterns'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Learning behavior patterns
    avg_session_duration = db.Column(db.Float, default=0.0)  # minutes
    sessions_per_week = db.Column(db.Float, default=0.0)
    completion_rate = db.Column(db.Float, default=0.0)  # percentage
    retention_rate = db.Column(db.Float, default=0.0)  # percentage
    
    # Content interaction patterns
    preferred_content_types = db.Column(db.Text, nullable=True)  # JSON dict of content type preferences
    interaction_frequency = db.Column(db.Float, default=0.0)  # interactions per session
    time_of_day_preference = db.Column(db.Text, nullable=True)  # JSON dict of time preferences
    
    # Performance patterns
    quiz_performance_trend = db.Column(db.Text, nullable=True)  # JSON array of recent scores
    assignment_completion_time = db.Column(db.Float, default=0.0)  # average hours to complete
    
    # Learning gaps
    weak_subjects = db.Column(db.Text, nullable=True)  # JSON array of subjects with low performance
    missed_concepts = db.Column(db.Text, nullable=True)  # JSON array of concepts to review
    
    # Last updated
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='learning_patterns')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'avg_session_duration': self.avg_session_duration,
            'sessions_per_week': self.sessions_per_week,
            'completion_rate': self.completion_rate,
            'retention_rate': self.retention_rate,
            'preferred_content_types': json.loads(self.preferred_content_types) if self.preferred_content_types else {},
            'interaction_frequency': self.interaction_frequency,
            'time_of_day_preference': json.loads(self.time_of_day_preference) if self.time_of_day_preference else {},
            'quiz_performance_trend': json.loads(self.quiz_performance_trend) if self.quiz_performance_trend else [],
            'assignment_completion_time': self.assignment_completion_time,
            'weak_subjects': json.loads(self.weak_subjects) if self.weak_subjects else [],
            'missed_concepts': json.loads(self.missed_concepts) if self.missed_concepts else [],
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
    
    def update_patterns(self, session_data=None, performance_data=None):
        """Update learning patterns based on new data"""
        if session_data:
            # Update session-related patterns
            pass
        
        if performance_data:
            # Update performance-related patterns
            pass
        
        self.last_updated = datetime.utcnow()

class ContentSimilarity(db.Model):
    """Store pre-computed content similarity scores"""
    __tablename__ = 'content_similarities'
    
    id = db.Column(db.Integer, primary_key=True)
    content_id = db.Column(db.Integer, nullable=False)
    content_type = db.Column(db.String(50), nullable=False)  # course, topic, material
    similar_content_id = db.Column(db.Integer, nullable=False)
    similarity_score = db.Column(db.Float, nullable=False)
    similarity_type = db.Column(db.String(50), nullable=False)  # content-based, collaborative, hybrid
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'content_id': self.content_id,
            'content_type': self.content_type,
            'similar_content_id': self.similar_content_id,
            'similarity_score': self.similarity_score,
            'similarity_type': self.similarity_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class UserRecommendation(db.Model):
    """Store personalized recommendations for users"""
    __tablename__ = 'user_recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Recommendation details
    content_id = db.Column(db.Integer, nullable=False)
    content_type = db.Column(db.String(50), nullable=False)  # course, topic, material, quiz
    recommendation_type = db.Column(db.String(50), nullable=False)  # content-based, collaborative, hybrid, gap-filling
    
    # Recommendation metadata
    confidence_score = db.Column(db.Float, nullable=False)  # 0-1
    reasoning = db.Column(db.Text, nullable=True)  # Why this was recommended
    priority = db.Column(db.Integer, default=1)  # 1-5, higher is more important
    
    # User interaction
    is_viewed = db.Column(db.Boolean, default=False)
    is_clicked = db.Column(db.Boolean, default=False)
    is_completed = db.Column(db.Boolean, default=False)
    viewed_at = db.Column(db.DateTime, nullable=True)
    clicked_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Recommendation lifecycle
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    user = db.relationship('User', backref='recommendations')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'content_id': self.content_id,
            'content_type': self.content_type,
            'recommendation_type': self.recommendation_type,
            'confidence_score': self.confidence_score,
            'reasoning': self.reasoning,
            'priority': self.priority,
            'is_viewed': self.is_viewed,
            'is_clicked': self.is_clicked,
            'is_completed': self.is_completed,
            'viewed_at': self.viewed_at.isoformat() if self.viewed_at else None,
            'clicked_at': self.clicked_at.isoformat() if self.clicked_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active
        }
    
    def mark_viewed(self):
        """Mark recommendation as viewed"""
        self.is_viewed = True
        self.viewed_at = datetime.utcnow()
    
    def mark_clicked(self):
        """Mark recommendation as clicked"""
        self.is_clicked = True
        self.clicked_at = datetime.utcnow()
    
    def mark_completed(self):
        """Mark recommendation as completed"""
        self.is_completed = True
        self.completed_at = datetime.utcnow()

class LearningCluster(db.Model):
    """Store user clusters for collaborative filtering"""
    __tablename__ = 'learning_clusters'
    
    id = db.Column(db.Integer, primary_key=True)
    cluster_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Cluster characteristics
    cluster_type = db.Column(db.String(50), nullable=False)  # learning_style, performance_level, interest_area
    cluster_center = db.Column(db.Text, nullable=True)  # JSON representation of cluster center
    distance_to_center = db.Column(db.Float, nullable=True)
    
    # Cluster metadata
    cluster_size = db.Column(db.Integer, default=0)
    cluster_quality = db.Column(db.Float, default=0.0)  # silhouette score or similar
    
    # Timestamps
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='learning_clusters')
    
    def to_dict(self):
        return {
            'id': self.id,
            'cluster_id': self.cluster_id,
            'user_id': self.user_id,
            'cluster_type': self.cluster_type,
            'cluster_center': json.loads(self.cluster_center) if self.cluster_center else None,
            'distance_to_center': self.distance_to_center,
            'cluster_size': self.cluster_size,
            'cluster_quality': self.cluster_quality,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

class RecommendationEngine:
    """Main recommendation engine class"""
    
    def __init__(self, app=None):
        self.app = app
        self.tfidf_vectorizer = None
        self.content_embeddings = {}
        self.user_embeddings = {}
        self.clustering_models = {}
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the recommendation engine with Flask app"""
        self.app = app
        
        # Load or create TF-IDF vectorizer
        self._load_or_create_vectorizer()
        
        # Load or create clustering models
        self._load_or_create_clustering_models()
    
    def _load_or_create_vectorizer(self):
        """Load or create TF-IDF vectorizer for content analysis"""
        vectorizer_path = os.path.join(self.app.instance_path, 'tfidf_vectorizer.pkl')
        
        if os.path.exists(vectorizer_path):
            with open(vectorizer_path, 'rb') as f:
                self.tfidf_vectorizer = pickle.load(f)
        else:
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
    
    def _load_or_create_clustering_models(self):
        """Load or create clustering models for user segmentation"""
        models_path = os.path.join(self.app.instance_path, 'clustering_models.pkl')
        
        if os.path.exists(models_path):
            with open(models_path, 'rb') as f:
                self.clustering_models = pickle.load(f)
        else:
            self.clustering_models = {
                'learning_style': KMeans(n_clusters=4, random_state=42),
                'performance_level': KMeans(n_clusters=3, random_state=42),
                'interest_area': KMeans(n_clusters=5, random_state=42)
            }
    
    def save_models(self):
        """Save trained models to disk"""
        # Save TF-IDF vectorizer
        vectorizer_path = os.path.join(self.app.instance_path, 'tfidf_vectorizer.pkl')
        with open(vectorizer_path, 'wb') as f:
            pickle.dump(self.tfidf_vectorizer, f)
        
        # Save clustering models
        models_path = os.path.join(self.app.instance_path, 'clustering_models.pkl')
        with open(models_path, 'wb') as f:
            pickle.dump(self.clustering_models, f)
    
    def content_based_recommendations(self, user_id, limit=10):
        """Generate content-based recommendations"""
        from content_models import Course, Topic, LearningMaterial
        from progress_models import LearningActivity, CourseProgress
        
        # Get user preferences
        user_pref = UserPreference.query.filter_by(user_id=user_id).first()
        if not user_pref:
            return []
        
        # Get user's learning history
        user_activities = LearningActivity.query.filter_by(user_id=user_id).all()
        completed_content = [act.material_id for act in user_activities if act.status == 'completed']
        
        # Get all available content
        all_courses = Course.query.filter_by(is_active=True).all()
        all_topics = Topic.query.filter_by(is_active=True).all()
        all_materials = LearningMaterial.query.filter_by(is_active=True).all()
        
        recommendations = []
        
        # Score content based on user preferences
        for course in all_courses:
            if course.id not in completed_content:
                score = self._calculate_content_score(course, user_pref)
                recommendations.append({
                    'content_id': course.id,
                    'content_type': 'course',
                    'title': course.title,
                    'score': score,
                    'type': 'content-based'
                })
        
        # Sort by score and return top recommendations
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:limit]
    
    def collaborative_filtering_recommendations(self, user_id, limit=10):
        """Generate collaborative filtering recommendations"""
        from content_models import Course, Topic, LearningMaterial
        from progress_models import LearningActivity, CourseProgress
        
        # Get user's cluster
        user_cluster = LearningCluster.query.filter_by(
            user_id=user_id, 
            cluster_type='learning_style'
        ).first()
        
        if not user_cluster:
            return []
        
        # Get other users in the same cluster
        cluster_users = LearningCluster.query.filter_by(
            cluster_id=user_cluster.cluster_id,
            cluster_type='learning_style'
        ).all()
        
        cluster_user_ids = [cu.user_id for cu in cluster_users if cu.user_id != user_id]
        
        # Get content that cluster users have completed
        cluster_activities = LearningActivity.query.filter(
            LearningActivity.user_id.in_(cluster_user_ids),
            LearningActivity.status == 'completed'
        ).all()
        
        # Count content popularity in cluster
        content_popularity = {}
        for activity in cluster_activities:
            content_id = activity.material_id or activity.course_id or activity.topic_id
            if content_id:
                content_popularity[content_id] = content_popularity.get(content_id, 0) + 1
        
        # Get user's completed content
        user_activities = LearningActivity.query.filter_by(user_id=user_id).all()
        user_completed = [act.material_id for act in user_activities if act.status == 'completed']
        
        # Generate recommendations
        recommendations = []
        for content_id, popularity in content_popularity.items():
            if content_id not in user_completed:
                recommendations.append({
                    'content_id': content_id,
                    'content_type': 'material',  # Default, could be enhanced
                    'score': popularity,
                    'type': 'collaborative'
                })
        
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:limit]
    
    def gap_filling_recommendations(self, user_id, limit=10):
        """Generate recommendations to fill learning gaps"""
        from progress_models import LearningActivity, CourseProgress
        from content_models import Course, Topic, LearningMaterial
        
        # Get user's weak areas
        user_pattern = LearningPattern.query.filter_by(user_id=user_id).first()
        if not user_pattern or not user_pattern.weak_subjects:
            return []
        
        weak_subjects = json.loads(user_pattern.weak_subjects)
        
        # Get content related to weak subjects
        recommendations = []
        for subject in weak_subjects:
            # Find courses/topics related to weak subject
            related_courses = Course.query.filter(
                Course.title.ilike(f'%{subject}%')
            ).all()
            
            for course in related_courses:
                recommendations.append({
                    'content_id': course.id,
                    'content_type': 'course',
                    'title': course.title,
                    'score': 0.9,  # High priority for gap filling
                    'type': 'gap-filling',
                    'reasoning': f'Recommended to improve {subject} skills'
                })
        
        return recommendations[:limit]
    
    def hybrid_recommendations(self, user_id, limit=10):
        """Generate hybrid recommendations combining multiple approaches"""
        content_based = self.content_based_recommendations(user_id, limit=limit//2)
        collaborative = self.collaborative_filtering_recommendations(user_id, limit=limit//2)
        gap_filling = self.gap_filling_recommendations(user_id, limit=limit//4)
        
        # Combine and deduplicate
        all_recommendations = content_based + collaborative + gap_filling
        seen_content = set()
        unique_recommendations = []
        
        for rec in all_recommendations:
            content_key = f"{rec['content_id']}_{rec['content_type']}"
            if content_key not in seen_content:
                seen_content.add(content_key)
                unique_recommendations.append(rec)
        
        # Sort by score and return
        unique_recommendations.sort(key=lambda x: x['score'], reverse=True)
        return unique_recommendations[:limit]
    
    def _calculate_content_score(self, content, user_pref):
        """Calculate content relevance score based on user preferences"""
        score = 0.0
        
        # Difficulty matching
        if hasattr(content, 'difficulty_level'):
            if content.difficulty_level == user_pref.preferred_difficulty:
                score += 0.3
        
        # Subject interest matching
        if user_pref.subject_interests:
            subject_interests = json.loads(user_pref.subject_interests)
            content_subjects = self._extract_subjects(content)
            
            for subject in subject_interests:
                if subject.lower() in content_subjects:
                    score += 0.4
        
        # Content type preference
        if user_pref.preferred_content_type:
            if hasattr(content, 'content_type'):
                if content.content_type == user_pref.preferred_content_type:
                    score += 0.2
        
        # Topic interest matching
        if user_pref.topic_interests:
            topic_interests = json.loads(user_pref.topic_interests)
            content_topics = self._extract_topics(content)
            
            for topic in topic_interests:
                if topic.lower() in content_topics:
                    score += 0.3
        
        return min(score, 1.0)
    
    def _extract_subjects(self, content):
        """Extract subjects from content"""
        subjects = []
        
        if hasattr(content, 'title'):
            subjects.append(content.title.lower())
        if hasattr(content, 'description'):
            subjects.append(content.description.lower())
        if hasattr(content, 'tags'):
            subjects.extend(content.tags.lower().split(','))
        
        return subjects
    
    def _extract_topics(self, content):
        """Extract topics from content"""
        topics = []
        
        if hasattr(content, 'title'):
            topics.append(content.title.lower())
        if hasattr(content, 'description'):
            topics.append(content.description.lower())
        
        return topics
    
    def update_user_clusters(self):
        """Update user clustering based on recent data"""
        from progress_models import LearningActivity, CourseProgress
        from content_models import Course, Topic, LearningMaterial
        
        # Get all users with sufficient data
        users = User.query.all()
        user_features = []
        user_ids = []
        
        for user in users:
            features = self._extract_user_features(user.id)
            if features is not None:
                user_features.append(features)
                user_ids.append(user.id)
        
        if len(user_features) < 3:
            return  # Need at least 3 users for clustering
        
        user_features = np.array(user_features)
        
        # Update clustering models
        for cluster_type, model in self.clustering_models.items():
            # Fit model
            clusters = model.fit_predict(user_features)
            
            # Update cluster assignments
            for i, user_id in enumerate(user_ids):
                cluster_id = int(clusters[i])
                
                # Update or create cluster assignment
                existing_cluster = LearningCluster.query.filter_by(
                    user_id=user_id,
                    cluster_type=cluster_type
                ).first()
                
                if existing_cluster:
                    existing_cluster.cluster_id = cluster_id
                    existing_cluster.last_updated = datetime.utcnow()
                else:
                    new_cluster = LearningCluster(
                        user_id=user_id,
                        cluster_id=cluster_id,
                        cluster_type=cluster_type,
                        cluster_size=len(set(clusters)),
                        cluster_quality=0.8  # Placeholder
                    )
                    db.session.add(new_cluster)
        
        db.session.commit()
    
    def _extract_user_features(self, user_id):
        """Extract features for user clustering"""
        from progress_models import LearningActivity, CourseProgress
        
        # Get user activities
        activities = LearningActivity.query.filter_by(user_id=user_id).all()
        
        if len(activities) < 5:
            return None  # Not enough data
        
        # Extract features
        features = []
        
        # Session duration patterns
        session_durations = [act.duration_seconds for act in activities if act.duration_seconds]
        if session_durations:
            features.extend([
                np.mean(session_durations),
                np.std(session_durations),
                len(session_durations)
            ])
        else:
            features.extend([0, 0, 0])
        
        # Completion patterns
        completion_rate = len([act for act in activities if act.status == 'completed']) / len(activities)
        features.append(completion_rate)
        
        # Performance patterns
        scores = [act.score for act in activities if act.score is not None]
        if scores:
            features.extend([np.mean(scores), np.std(scores)])
        else:
            features.extend([0, 0])
        
        # Activity frequency
        features.append(len(activities))
        
        return features

# Global recommendation engine instance
recommendation_engine = RecommendationEngine() 