from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date
from sqlalchemy import func, and_, desc
import json

from progress_models import (
    db, LearningSession, LearningActivity, CourseProgress, 
    TopicProgress, LearningAnalytics, StudyStreak
)
from models import User
from content_models import Course, Topic, LearningMaterial

progress_bp = Blueprint('progress', __name__)

# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

@progress_bp.route('/api/sessions/start', methods=['POST'])
@login_required
def start_session():
    """Start a new learning session"""
    try:
        data = request.get_json()
        
        # Create new session
        session = LearningSession(
            user_id=current_user.id,
            course_id=data.get('course_id'),
            topic_id=data.get('topic_id'),
            session_type=data.get('session_type', 'study'),
            device_type=data.get('device_type'),
            browser=request.headers.get('User-Agent', '')[:100],
            ip_address=request.remote_addr
        )
        
        db.session.add(session)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'session_id': session.id,
            'message': 'Session started successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@progress_bp.route('/api/sessions/<int:session_id>/end', methods=['POST'])
@login_required
def end_session(session_id):
    """End a learning session"""
    try:
        session = LearningSession.query.filter_by(
            id=session_id, 
            user_id=current_user.id,
            is_active=True
        ).first()
        
        if not session:
            return jsonify({
                'success': False,
                'error': 'Session not found or already ended'
            }), 404
        
        # End session
        duration = session.end_session()
        
        # Update course progress with time spent
        if session.course_id:
            course_progress = CourseProgress.query.filter_by(
                user_id=current_user.id,
                course_id=session.course_id
            ).first()
            
            if course_progress:
                course_progress.add_time_spent(duration)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'duration_minutes': duration,
            'message': 'Session ended successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@progress_bp.route('/api/sessions/active', methods=['GET'])
@login_required
def get_active_session():
    """Get user's currently active session"""
    try:
        session = LearningSession.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).order_by(desc(LearningSession.session_start)).first()
        
        if session:
            return jsonify({
                'success': True,
                'session': session.to_dict()
            })
        else:
            return jsonify({
                'success': True,
                'session': None
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# ACTIVITY TRACKING
# ============================================================================

@progress_bp.route('/api/activities/start', methods=['POST'])
@login_required
def start_activity():
    """Start a new learning activity"""
    try:
        data = request.get_json()
        
        # Get or create active session
        session = LearningSession.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).first()
        
        if not session:
            # Create new session if none active
            session = LearningSession(
                user_id=current_user.id,
                course_id=data.get('course_id'),
                topic_id=data.get('topic_id'),
                session_type='study'
            )
            db.session.add(session)
            db.session.flush()
        
        # Create activity
        activity = LearningActivity(
            session_id=session.id,
            user_id=current_user.id,
            course_id=data.get('course_id'),
            topic_id=data.get('topic_id'),
            material_id=data.get('material_id'),
            activity_type=data.get('activity_type'),
            activity_name=data.get('activity_name'),
            description=data.get('description'),
            metadata=json.dumps(data.get('metadata', {}))
        )
        
        db.session.add(activity)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'activity_id': activity.id,
            'session_id': session.id,
            'message': 'Activity started successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@progress_bp.route('/api/activities/<int:activity_id>/update', methods=['POST'])
@login_required
def update_activity(activity_id):
    """Update activity progress"""
    try:
        data = request.get_json()
        activity = LearningActivity.query.filter_by(
            id=activity_id,
            user_id=current_user.id
        ).first()
        
        if not activity:
            return jsonify({
                'success': False,
                'error': 'Activity not found'
            }), 404
        
        # Update progress
        if 'progress_percentage' in data:
            activity.update_progress(data['progress_percentage'])
        
        # Complete activity if requested
        if data.get('complete', False):
            activity.complete_activity(
                progress=data.get('progress_percentage', 100),
                score=data.get('score'),
                max_score=data.get('max_score')
            )
            
            # Update topic progress
            if activity.topic_id:
                update_topic_progress(current_user.id, activity.topic_id)
            
            # Update course progress
            if activity.course_id:
                update_course_progress(current_user.id, activity.course_id)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Activity updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@progress_bp.route('/api/activities/<int:activity_id>/complete', methods=['POST'])
@login_required
def complete_activity(activity_id):
    """Complete a learning activity"""
    try:
        data = request.get_json()
        activity = LearningActivity.query.filter_by(
            id=activity_id,
            user_id=current_user.id
        ).first()
        
        if not activity:
            return jsonify({
                'success': False,
                'error': 'Activity not found'
            }), 404
        
        # Complete activity
        activity.complete_activity(
            progress=data.get('progress_percentage', 100),
            score=data.get('score'),
            max_score=data.get('max_score')
        )
        
        # Update related progress
        if activity.topic_id:
            update_topic_progress(current_user.id, activity.topic_id)
        
        if activity.course_id:
            update_course_progress(current_user.id, activity.course_id)
        
        # Update study streak
        update_study_streak(current_user.id)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Activity completed successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# PROGRESS TRACKING
# ============================================================================

@progress_bp.route('/api/progress/course/<int:course_id>', methods=['GET'])
@login_required
def get_course_progress(course_id):
    """Get course progress for current user"""
    try:
        progress = CourseProgress.query.filter_by(
            user_id=current_user.id,
            course_id=course_id
        ).first()
        
        if not progress:
            # Initialize progress if not exists
            progress = initialize_course_progress(current_user.id, course_id)
        
        return jsonify({
            'success': True,
            'progress': progress.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@progress_bp.route('/api/progress/topic/<int:topic_id>', methods=['GET'])
@login_required
def get_topic_progress(topic_id):
    """Get topic progress for current user"""
    try:
        progress = TopicProgress.query.filter_by(
            user_id=current_user.id,
            topic_id=topic_id
        ).first()
        
        if not progress:
            # Initialize progress if not exists
            progress = initialize_topic_progress(current_user.id, topic_id)
        
        return jsonify({
            'success': True,
            'progress': progress.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@progress_bp.route('/api/progress/overview', methods=['GET'])
@login_required
def get_progress_overview():
    """Get overall progress overview for current user"""
    try:
        # Get all course progress
        course_progress = CourseProgress.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).all()
        
        # Get study streak
        streak = StudyStreak.query.filter_by(user_id=current_user.id).first()
        if not streak:
            streak = StudyStreak(user_id=current_user.id)
            db.session.add(streak)
            db.session.commit()
        
        # Calculate overall stats
        total_courses = len(course_progress)
        completed_courses = len([p for p in course_progress if p.overall_progress >= 100])
        average_progress = sum(p.overall_progress for p in course_progress) / max(total_courses, 1)
        total_time = sum(p.total_time_spent_minutes for p in course_progress)
        
        # Get recent activities
        recent_activities = LearningActivity.query.filter_by(
            user_id=current_user.id
        ).order_by(desc(LearningActivity.started_at)).limit(10).all()
        
        return jsonify({
            'success': True,
            'overview': {
                'total_courses': total_courses,
                'completed_courses': completed_courses,
                'average_progress': round(average_progress, 2),
                'total_time_hours': round(total_time / 60, 1),
                'current_streak': streak.current_streak,
                'longest_streak': streak.longest_streak
            },
            'course_progress': [p.to_dict() for p in course_progress],
            'recent_activities': [a.to_dict() for a in recent_activities]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# ANALYTICS
# ============================================================================

@progress_bp.route('/api/analytics/daily', methods=['GET'])
@login_required
def get_daily_analytics():
    """Get daily learning analytics"""
    try:
        today = date.today()
        
        # Get today's analytics
        analytics = LearningAnalytics.query.filter_by(
            user_id=current_user.id,
            period_type='daily',
            period_start=today
        ).first()
        
        if not analytics:
            # Generate analytics for today
            analytics = generate_daily_analytics(current_user.id, today)
        
        return jsonify({
            'success': True,
            'analytics': analytics.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@progress_bp.route('/api/analytics/weekly', methods=['GET'])
@login_required
def get_weekly_analytics():
    """Get weekly learning analytics"""
    try:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        # Get this week's analytics
        analytics = LearningAnalytics.query.filter_by(
            user_id=current_user.id,
            period_type='weekly',
            period_start=week_start
        ).first()
        
        if not analytics:
            # Generate analytics for this week
            analytics = generate_weekly_analytics(current_user.id, week_start, week_end)
        
        return jsonify({
            'success': True,
            'analytics': analytics.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@progress_bp.route('/api/analytics/monthly', methods=['GET'])
@login_required
def get_monthly_analytics():
    """Get monthly learning analytics"""
    try:
        today = date.today()
        month_start = today.replace(day=1)
        if today.month == 12:
            month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        
        # Get this month's analytics
        analytics = LearningAnalytics.query.filter_by(
            user_id=current_user.id,
            period_type='monthly',
            period_start=month_start
        ).first()
        
        if not analytics:
            # Generate analytics for this month
            analytics = generate_monthly_analytics(current_user.id, month_start, month_end)
        
        return jsonify({
            'success': True,
            'analytics': analytics.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def initialize_course_progress(user_id, course_id):
    """Initialize course progress for a user"""
    course = Course.query.get(course_id)
    if not course:
        return None
    
    # Count total topics and materials
    total_topics = course.topics.count()
    total_materials = 0
    for topic in course.topics:
        total_materials += topic.materials.count()
    
    progress = CourseProgress(
        user_id=user_id,
        course_id=course_id,
        total_topics=total_topics,
        total_materials=total_materials
    )
    
    db.session.add(progress)
    db.session.commit()
    return progress

def initialize_topic_progress(user_id, topic_id):
    """Initialize topic progress for a user"""
    topic = Topic.query.get(topic_id)
    if not topic:
        return None
    
    total_materials = topic.materials.count()
    
    progress = TopicProgress(
        user_id=user_id,
        topic_id=topic_id,
        course_id=topic.course_id,
        total_materials=total_materials
    )
    
    db.session.add(progress)
    db.session.commit()
    return progress

def update_topic_progress(user_id, topic_id):
    """Update topic progress based on completed activities"""
    progress = TopicProgress.query.filter_by(
        user_id=user_id,
        topic_id=topic_id
    ).first()
    
    if not progress:
        progress = initialize_topic_progress(user_id, topic_id)
    
    if progress:
        # Count completed materials
        completed_activities = LearningActivity.query.filter_by(
            user_id=user_id,
            topic_id=topic_id,
            status='completed'
        ).distinct(LearningActivity.material_id).count()
        
        progress.materials_completed = completed_activities
        progress.update_progress()
        
        db.session.commit()

def update_course_progress(user_id, course_id):
    """Update course progress based on completed activities"""
    progress = CourseProgress.query.filter_by(
        user_id=user_id,
        course_id=course_id
    ).first()
    
    if not progress:
        progress = initialize_course_progress(user_id, course_id)
    
    if progress:
        # Count completed topics
        completed_topics = TopicProgress.query.filter_by(
            user_id=user_id,
            course_id=course_id,
            is_completed=True
        ).count()
        
        # Count completed materials
        completed_materials = LearningActivity.query.filter_by(
            user_id=user_id,
            course_id=course_id,
            status='completed'
        ).distinct(LearningActivity.material_id).count()
        
        progress.topics_completed = completed_topics
        progress.materials_completed = completed_materials
        progress.update_progress()
        
        db.session.commit()

def update_study_streak(user_id):
    """Update study streak for user"""
    streak = StudyStreak.query.filter_by(user_id=user_id).first()
    if not streak:
        streak = StudyStreak(user_id=user_id)
        db.session.add(streak)
    
    streak.update_streak()
    db.session.commit()

def generate_daily_analytics(user_id, date):
    """Generate daily analytics for a user"""
    # Get sessions for the day
    sessions = LearningSession.query.filter(
        and_(
            LearningSession.user_id == user_id,
            func.date(LearningSession.session_start) == date
        )
    ).all()
    
    # Get activities for the day
    activities = LearningActivity.query.filter(
        and_(
            LearningActivity.user_id == user_id,
            func.date(LearningActivity.started_at) == date
        )
    ).all()
    
    # Calculate metrics
    total_time = sum(s.duration_minutes for s in sessions)
    activities_completed = len([a for a in activities if a.status == 'completed'])
    materials_accessed = len(set(a.material_id for a in activities if a.material_id))
    
    # Calculate average score
    completed_activities = [a for a in activities if a.status == 'completed' and a.score is not None]
    average_score = sum(a.score for a in completed_activities) / len(completed_activities) if completed_activities else 0
    
    analytics = LearningAnalytics(
        user_id=user_id,
        period_type='daily',
        period_start=date,
        period_end=date,
        sessions_count=len(sessions),
        total_time_minutes=total_time,
        activities_completed=activities_completed,
        materials_accessed=materials_accessed,
        average_score=average_score,
        quizzes_taken=len([a for a in activities if a.activity_type == 'quiz_take']),
        assignments_submitted=len([a for a in activities if a.activity_type == 'assignment_submit'])
    )
    
    db.session.add(analytics)
    db.session.commit()
    return analytics

def generate_weekly_analytics(user_id, week_start, week_end):
    """Generate weekly analytics for a user"""
    # Similar to daily but for week range
    sessions = LearningSession.query.filter(
        and_(
            LearningSession.user_id == user_id,
            func.date(LearningSession.session_start) >= week_start,
            func.date(LearningSession.session_start) <= week_end
        )
    ).all()
    
    activities = LearningActivity.query.filter(
        and_(
            LearningActivity.user_id == user_id,
            func.date(LearningActivity.started_at) >= week_start,
            func.date(LearningActivity.started_at) <= week_end
        )
    ).all()
    
    # Calculate metrics (similar to daily)
    total_time = sum(s.duration_minutes for s in sessions)
    activities_completed = len([a for a in activities if a.status == 'completed'])
    materials_accessed = len(set(a.material_id for a in activities if a.material_id))
    
    completed_activities = [a for a in activities if a.status == 'completed' and a.score is not None]
    average_score = sum(a.score for a in completed_activities) / len(completed_activities) if completed_activities else 0
    
    analytics = LearningAnalytics(
        user_id=user_id,
        period_type='weekly',
        period_start=week_start,
        period_end=week_end,
        sessions_count=len(sessions),
        total_time_minutes=total_time,
        activities_completed=activities_completed,
        materials_accessed=materials_accessed,
        average_score=average_score,
        quizzes_taken=len([a for a in activities if a.activity_type == 'quiz_take']),
        assignments_submitted=len([a for a in activities if a.activity_type == 'assignment_submit'])
    )
    
    db.session.add(analytics)
    db.session.commit()
    return analytics

def generate_monthly_analytics(user_id, month_start, month_end):
    """Generate monthly analytics for a user"""
    # Similar to weekly but for month range
    sessions = LearningSession.query.filter(
        and_(
            LearningSession.user_id == user_id,
            func.date(LearningSession.session_start) >= month_start,
            func.date(LearningSession.session_start) <= month_end
        )
    ).all()
    
    activities = LearningActivity.query.filter(
        and_(
            LearningActivity.user_id == user_id,
            func.date(LearningActivity.started_at) >= month_start,
            func.date(LearningActivity.started_at) <= month_end
        )
    ).all()
    
    # Calculate metrics (similar to daily/weekly)
    total_time = sum(s.duration_minutes for s in sessions)
    activities_completed = len([a for a in activities if a.status == 'completed'])
    materials_accessed = len(set(a.material_id for a in activities if a.material_id))
    
    completed_activities = [a for a in activities if a.status == 'completed' and a.score is not None]
    average_score = sum(a.score for a in completed_activities) / len(completed_activities) if completed_activities else 0
    
    analytics = LearningAnalytics(
        user_id=user_id,
        period_type='monthly',
        period_start=month_start,
        period_end=month_end,
        sessions_count=len(sessions),
        total_time_minutes=total_time,
        activities_completed=activities_completed,
        materials_accessed=materials_accessed,
        average_score=average_score,
        quizzes_taken=len([a for a in activities if a.activity_type == 'quiz_take']),
        assignments_submitted=len([a for a in activities if a.activity_type == 'assignment_submit'])
    )
    
    db.session.add(analytics)
    db.session.commit()
    return analytics 