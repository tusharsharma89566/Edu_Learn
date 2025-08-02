from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from recommendation_models import (
    UserPreference, LearningPattern, UserRecommendation, 
    LearningCluster, ContentSimilarity, recommendation_engine
)
from models import db
import json
from datetime import datetime, timedelta

recommendation_bp = Blueprint('recommendation', __name__)

@recommendation_bp.route('/preferences', methods=['GET'])
@login_required
def get_preferences():
    """Get user preferences"""
    preferences = UserPreference.query.filter_by(user_id=current_user.id).first()
    
    if preferences:
        return jsonify({
            'success': True,
            'preferences': preferences.to_dict()
        })
    else:
        return jsonify({
            'success': False,
            'message': 'No preferences found'
        })

@recommendation_bp.route('/preferences', methods=['POST'])
@login_required
def update_preferences():
    """Update user preferences"""
    data = request.get_json()
    
    preferences = UserPreference.query.filter_by(user_id=current_user.id).first()
    
    if not preferences:
        preferences = UserPreference(user_id=current_user.id)
        db.session.add(preferences)
    
    # Update preferences
    if 'preferred_difficulty' in data:
        preferences.preferred_difficulty = data['preferred_difficulty']
    
    if 'preferred_learning_style' in data:
        preferences.preferred_learning_style = data['preferred_learning_style']
    
    if 'preferred_content_type' in data:
        preferences.preferred_content_type = data['preferred_content_type']
    
    if 'subject_interests' in data:
        preferences.subject_interests = json.dumps(data['subject_interests'])
    
    if 'topic_interests' in data:
        preferences.topic_interests = json.dumps(data['topic_interests'])
    
    if 'preferred_study_time' in data:
        preferences.preferred_study_time = data['preferred_study_time']
    
    if 'preferred_session_duration' in data:
        preferences.preferred_session_duration = data['preferred_session_duration']
    
    if 'preferred_device' in data:
        preferences.preferred_device = data['preferred_device']
    
    if 'email_notifications' in data:
        preferences.email_notifications = data['email_notifications']
    
    if 'push_notifications' in data:
        preferences.push_notifications = data['push_notifications']
    
    if 'recommendation_frequency' in data:
        preferences.recommendation_frequency = data['recommendation_frequency']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Preferences updated successfully',
        'preferences': preferences.to_dict()
    })

@recommendation_bp.route('/recommendations', methods=['GET'])
@login_required
def get_recommendations():
    """Get personalized recommendations"""
    recommendation_type = request.args.get('type', 'hybrid')  # content-based, collaborative, hybrid, gap-filling
    limit = int(request.args.get('limit', 10))
    
    # Initialize recommendation engine if needed
    if not hasattr(recommendation_engine, 'app'):
        from app import app
        recommendation_engine.init_app(app)
    
    recommendations = []
    
    if recommendation_type == 'content-based':
        recommendations = recommendation_engine.content_based_recommendations(current_user.id, limit)
    elif recommendation_type == 'collaborative':
        recommendations = recommendation_engine.collaborative_filtering_recommendations(current_user.id, limit)
    elif recommendation_type == 'gap-filling':
        recommendations = recommendation_engine.gap_filling_recommendations(current_user.id, limit)
    else:  # hybrid
        recommendations = recommendation_engine.hybrid_recommendations(current_user.id, limit)
    
    # Get content details for recommendations
    from content_models import Course, Topic, LearningMaterial
    
    detailed_recommendations = []
    for rec in recommendations:
        content_details = {}
        
        if rec['content_type'] == 'course':
            course = Course.query.get(rec['content_id'])
            if course:
                content_details = {
                    'id': course.id,
                    'title': course.title,
                    'description': course.description,
                    'instructor': course.instructor.full_name if course.instructor else None,
                    'duration': course.duration,
                    'difficulty_level': getattr(course, 'difficulty_level', 'intermediate'),
                    'thumbnail_url': course.thumbnail_url
                }
        elif rec['content_type'] == 'topic':
            topic = Topic.query.get(rec['content_id'])
            if topic:
                content_details = {
                    'id': topic.id,
                    'title': topic.title,
                    'description': topic.description,
                    'course_title': topic.course.title if topic.course else None
                }
        elif rec['content_type'] == 'material':
            material = LearningMaterial.query.get(rec['content_id'])
            if material:
                content_details = {
                    'id': material.id,
                    'title': material.title,
                    'description': material.description,
                    'content_type': material.content_type,
                    'topic_title': material.topic.title if material.topic else None
                }
        
        if content_details:
            detailed_recommendations.append({
                **rec,
                'content': content_details
            })
    
    return jsonify({
        'success': True,
        'recommendations': detailed_recommendations,
        'type': recommendation_type,
        'count': len(detailed_recommendations)
    })

@recommendation_bp.route('/recommendations/generate', methods=['POST'])
@login_required
def generate_recommendations():
    """Generate and store new recommendations for user"""
    data = request.get_json()
    recommendation_type = data.get('type', 'hybrid')
    limit = data.get('limit', 10)
    
    # Get recommendations
    if recommendation_type == 'content-based':
        recommendations = recommendation_engine.content_based_recommendations(current_user.id, limit)
    elif recommendation_type == 'collaborative':
        recommendations = recommendation_engine.collaborative_filtering_recommendations(current_user.id, limit)
    elif recommendation_type == 'gap-filling':
        recommendations = recommendation_engine.gap_filling_recommendations(current_user.id, limit)
    else:  # hybrid
        recommendations = recommendation_engine.hybrid_recommendations(current_user.id, limit)
    
    # Store recommendations in database
    stored_recommendations = []
    for rec in recommendations:
        # Check if recommendation already exists
        existing = UserRecommendation.query.filter_by(
            user_id=current_user.id,
            content_id=rec['content_id'],
            content_type=rec['content_type'],
            is_active=True
        ).first()
        
        if not existing:
            recommendation = UserRecommendation(
                user_id=current_user.id,
                content_id=rec['content_id'],
                content_type=rec['content_type'],
                recommendation_type=rec['type'],
                confidence_score=rec['score'],
                reasoning=rec.get('reasoning', ''),
                priority=1,
                expires_at=datetime.utcnow() + timedelta(days=30)  # Expire in 30 days
            )
            db.session.add(recommendation)
            stored_recommendations.append(recommendation)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Generated {len(stored_recommendations)} new recommendations',
        'stored_count': len(stored_recommendations)
    })

@recommendation_bp.route('/recommendations/stored', methods=['GET'])
@login_required
def get_stored_recommendations():
    """Get stored recommendations for user"""
    recommendations = UserRecommendation.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).order_by(UserRecommendation.priority.desc(), UserRecommendation.confidence_score.desc()).all()
    
    return jsonify({
        'success': True,
        'recommendations': [rec.to_dict() for rec in recommendations]
    })

@recommendation_bp.route('/recommendations/<int:rec_id>/view', methods=['POST'])
@login_required
def mark_recommendation_viewed(rec_id):
    """Mark recommendation as viewed"""
    recommendation = UserRecommendation.query.filter_by(
        id=rec_id,
        user_id=current_user.id
    ).first()
    
    if recommendation:
        recommendation.mark_viewed()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Recommendation marked as viewed'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Recommendation not found'
        }), 404

@recommendation_bp.route('/recommendations/<int:rec_id>/click', methods=['POST'])
@login_required
def mark_recommendation_clicked(rec_id):
    """Mark recommendation as clicked"""
    recommendation = UserRecommendation.query.filter_by(
        id=rec_id,
        user_id=current_user.id
    ).first()
    
    if recommendation:
        recommendation.mark_clicked()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Recommendation marked as clicked'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Recommendation not found'
        }), 404

@recommendation_bp.route('/patterns', methods=['GET'])
@login_required
def get_learning_patterns():
    """Get user learning patterns"""
    patterns = LearningPattern.query.filter_by(user_id=current_user.id).first()
    
    if patterns:
        return jsonify({
            'success': True,
            'patterns': patterns.to_dict()
        })
    else:
        return jsonify({
            'success': False,
            'message': 'No learning patterns found'
        })

@recommendation_bp.route('/clusters', methods=['GET'])
@login_required
def get_user_clusters():
    """Get user cluster information"""
    clusters = LearningCluster.query.filter_by(user_id=current_user.id).all()
    
    return jsonify({
        'success': True,
        'clusters': [cluster.to_dict() for cluster in clusters]
    })

@recommendation_bp.route('/similar-content/<int:content_id>', methods=['GET'])
@login_required
def get_similar_content(content_id):
    """Get similar content based on content ID"""
    content_type = request.args.get('type', 'course')
    limit = int(request.args.get('limit', 5))
    
    # Get similar content from database
    similarities = ContentSimilarity.query.filter_by(
        content_id=content_id,
        content_type=content_type
    ).order_by(ContentSimilarity.similarity_score.desc()).limit(limit).all()
    
    similar_content = []
    for sim in similarities:
        # Get content details based on type
        content_details = {}
        
        if sim.content_type == 'course':
            from content_models import Course
            course = Course.query.get(sim.similar_content_id)
            if course:
                content_details = {
                    'id': course.id,
                    'title': course.title,
                    'description': course.description,
                    'similarity_score': sim.similarity_score
                }
        elif sim.content_type == 'topic':
            from content_models import Topic
            topic = Topic.query.get(sim.similar_content_id)
            if topic:
                content_details = {
                    'id': topic.id,
                    'title': topic.title,
                    'description': topic.description,
                    'similarity_score': sim.similarity_score
                }
        
        if content_details:
            similar_content.append(content_details)
    
    return jsonify({
        'success': True,
        'similar_content': similar_content
    })

@recommendation_bp.route('/dashboard', methods=['GET'])
@login_required
def recommendation_dashboard():
    """Recommendation dashboard page"""
    return render_template('recommendation/dashboard.html', user=current_user)

@recommendation_bp.route('/preferences-page', methods=['GET'])
@login_required
def preferences_page():
    """User preferences page"""
    return render_template('recommendation/preferences.html', user=current_user)

# Admin routes for recommendation management
@recommendation_bp.route('/admin/update-clusters', methods=['POST'])
@login_required
def update_user_clusters():
    """Update user clustering (admin only)"""
    if not current_user.is_admin():
        return jsonify({
            'success': False,
            'message': 'Admin access required'
        }), 403
    
    try:
        recommendation_engine.update_user_clusters()
        return jsonify({
            'success': True,
            'message': 'User clusters updated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error updating clusters: {str(e)}'
        }), 500

@recommendation_bp.route('/admin/analytics', methods=['GET'])
@login_required
def recommendation_analytics():
    """Get recommendation analytics (admin only)"""
    if not current_user.is_admin():
        return jsonify({
            'success': False,
            'message': 'Admin access required'
        }), 403
    
    # Get recommendation statistics
    total_recommendations = UserRecommendation.query.count()
    active_recommendations = UserRecommendation.query.filter_by(is_active=True).count()
    viewed_recommendations = UserRecommendation.query.filter_by(is_viewed=True).count()
    clicked_recommendations = UserRecommendation.query.filter_by(is_clicked=True).count()
    completed_recommendations = UserRecommendation.query.filter_by(is_completed=True).count()
    
    # Calculate engagement rates
    view_rate = (viewed_recommendations / total_recommendations * 100) if total_recommendations > 0 else 0
    click_rate = (clicked_recommendations / total_recommendations * 100) if total_recommendations > 0 else 0
    completion_rate = (completed_recommendations / total_recommendations * 100) if total_recommendations > 0 else 0
    
    # Get recommendations by type
    from sqlalchemy import func
    recommendations_by_type = db.session.query(
        UserRecommendation.recommendation_type,
        func.count(UserRecommendation.id)
    ).group_by(UserRecommendation.recommendation_type).all()
    
    return jsonify({
        'success': True,
        'analytics': {
            'total_recommendations': total_recommendations,
            'active_recommendations': active_recommendations,
            'viewed_recommendations': viewed_recommendations,
            'clicked_recommendations': clicked_recommendations,
            'completed_recommendations': completed_recommendations,
            'view_rate': round(view_rate, 2),
            'click_rate': round(click_rate, 2),
            'completion_rate': round(completion_rate, 2),
            'recommendations_by_type': dict(recommendations_by_type)
        }
    })

# API endpoints for frontend integration
@recommendation_bp.route('/api/recommendations/quick', methods=['GET'])
@login_required
def quick_recommendations():
    """Get quick recommendations for dashboard"""
    limit = int(request.args.get('limit', 5))
    
    # Get stored recommendations first
    stored_recs = UserRecommendation.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).order_by(UserRecommendation.priority.desc(), UserRecommendation.confidence_score.desc()).limit(limit).all()
    
    if len(stored_recs) < limit:
        # Generate new recommendations if needed
        new_recs = recommendation_engine.hybrid_recommendations(current_user.id, limit - len(stored_recs))
        
        # Store new recommendations
        for rec in new_recs:
            recommendation = UserRecommendation(
                user_id=current_user.id,
                content_id=rec['content_id'],
                content_type=rec['content_type'],
                recommendation_type=rec['type'],
                confidence_score=rec['score'],
                priority=1,
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            db.session.add(recommendation)
        
        db.session.commit()
        
        # Get updated stored recommendations
        stored_recs = UserRecommendation.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).order_by(UserRecommendation.priority.desc(), UserRecommendation.confidence_score.desc()).limit(limit).all()
    
    # Get content details
    recommendations = []
    for rec in stored_recs:
        content_details = get_content_details(rec.content_id, rec.content_type)
        if content_details:
            recommendations.append({
                'id': rec.id,
                'content': content_details,
                'type': rec.recommendation_type,
                'confidence': rec.confidence_score,
                'reasoning': rec.reasoning,
                'priority': rec.priority,
                'is_viewed': rec.is_viewed,
                'is_clicked': rec.is_clicked
            })
    
    return jsonify({
        'success': True,
        'recommendations': recommendations
    })

def get_content_details(content_id, content_type):
    """Helper function to get content details"""
    if content_type == 'course':
        from content_models import Course
        course = Course.query.get(content_id)
        if course:
            return {
                'id': course.id,
                'title': course.title,
                'description': course.description,
                'type': 'course',
                'instructor': course.instructor.full_name if course.instructor else None,
                'thumbnail_url': course.thumbnail_url
            }
    elif content_type == 'topic':
        from content_models import Topic
        topic = Topic.query.get(content_id)
        if topic:
            return {
                'id': topic.id,
                'title': topic.title,
                'description': topic.description,
                'type': 'topic',
                'course_title': topic.course.title if topic.course else None
            }
    elif content_type == 'material':
        from content_models import LearningMaterial
        material = LearningMaterial.query.get(content_id)
        if material:
            return {
                'id': material.id,
                'title': material.title,
                'description': material.description,
                'type': 'material',
                'content_type': material.content_type,
                'topic_title': material.topic.title if material.topic else None
            }
    
    return None 