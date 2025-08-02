from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from gamification_models import (
    Badge, UserBadge, UserPoints, Leaderboard, LeaderboardEntry, 
    Achievement, Notification, gamification_engine
)
from models import db
import json
from datetime import datetime, timedelta
from sqlalchemy import func, desc

gamification_bp = Blueprint('gamification', __name__)

@gamification_bp.route('/badges', methods=['GET'])
@login_required
def get_badges():
    """Get all available badges"""
    category = request.args.get('category')
    badge_type = request.args.get('badge_type')
    
    query = Badge.query.filter_by(is_active=True)
    
    if category:
        query = query.filter_by(category=category)
    if badge_type:
        query = query.filter_by(badge_type=badge_type)
    
    badges = query.all()
    
    return jsonify({
        'success': True,
        'badges': [badge.to_dict() for badge in badges]
    })

@gamification_bp.route('/user/badges', methods=['GET'])
@login_required
def get_user_badges():
    """Get user's earned badges"""
    user_badges = UserBadge.query.filter_by(user_id=current_user.id).all()
    
    return jsonify({
        'success': True,
        'badges': [ub.to_dict() for ub in user_badges]
    })

@gamification_bp.route('/badges', methods=['POST'])
@login_required
def create_badge():
    """Create a new badge (admin only)"""
    if not current_user.is_admin():
        return jsonify({
            'success': False,
            'message': 'Only admins can create badges'
        }), 403
    
    data = request.get_json()
    
    badge = Badge(
        name=data['name'],
        description=data.get('description'),
        badge_type=data['badge_type'],
        category=data['category'],
        icon_name=data['icon_name'],
        color=data.get('color', '#007bff'),
        rarity=data.get('rarity', 'common'),
        criteria_type=data['criteria_type'],
        criteria_value=data['criteria_value'],
        criteria_config=json.dumps(data.get('criteria_config', {})),
        points_reward=data.get('points_reward', 0),
        experience_reward=data.get('experience_reward', 0)
    )
    
    db.session.add(badge)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Badge created successfully',
        'badge': badge.to_dict()
    })

@gamification_bp.route('/points', methods=['GET'])
@login_required
def get_user_points():
    """Get user's points and level information"""
    user_points = UserPoints.query.filter_by(user_id=current_user.id).first()
    
    if not user_points:
        # Create user points record if it doesn't exist
        user_points = UserPoints(user_id=current_user.id)
        db.session.add(user_points)
        db.session.commit()
    
    return jsonify({
        'success': True,
        'points': user_points.to_dict()
    })

@gamification_bp.route('/points/add', methods=['POST'])
@login_required
def add_points():
    """Add points to user (for activities)"""
    data = request.get_json()
    points = data.get('points', 0)
    experience = data.get('experience', 0)
    activity_type = data.get('activity_type', 'general')
    
    user_points = UserPoints.query.filter_by(user_id=current_user.id).first()
    if not user_points:
        user_points = UserPoints(user_id=current_user.id)
        db.session.add(user_points)
    
    # Add points and experience
    user_points.add_points(points, experience)
    
    # Update streak
    user_points.update_streak()
    
    db.session.commit()
    
    # Check for badges
    new_badges = gamification_engine.check_badges(
        current_user.id, 
        'points', 
        user_points.total_points
    )
    
    # Check for level up
    level_up_notification = None
    if user_points.experience >= user_points.experience_to_next_level:
        level_up_notification = gamification_engine.create_notification(
            current_user.id,
            f"Level Up! You're now level {user_points.level}",
            f"Congratulations! You've reached level {user_points.level}. Keep up the great work!",
            'level_up',
            {'new_level': user_points.level},
            'star',
            '#ffd700'
        )
    
    return jsonify({
        'success': True,
        'message': 'Points added successfully',
        'new_points': user_points.to_dict(),
        'new_badges': [badge.to_dict() for badge in new_badges],
        'level_up': level_up_notification.to_dict() if level_up_notification else None
    })

@gamification_bp.route('/leaderboards', methods=['GET'])
@login_required
def get_leaderboards():
    """Get available leaderboards"""
    leaderboards = Leaderboard.query.filter_by(is_active=True).all()
    
    return jsonify({
        'success': True,
        'leaderboards': [lb.to_dict() for lb in leaderboards]
    })

@gamification_bp.route('/leaderboards/<int:leaderboard_id>', methods=['GET'])
@login_required
def get_leaderboard_entries(leaderboard_id):
    """Get leaderboard entries"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    leaderboard = Leaderboard.query.get(leaderboard_id)
    if not leaderboard:
        return jsonify({
            'success': False,
            'message': 'Leaderboard not found'
        }), 404
    
    entries = LeaderboardEntry.query.filter_by(leaderboard_id=leaderboard_id).order_by(
        LeaderboardEntry.score.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'success': True,
        'leaderboard': leaderboard.to_dict(),
        'entries': [entry.to_dict() for entry in entries.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': entries.total,
            'pages': entries.pages
        }
    })

@gamification_bp.route('/leaderboards', methods=['POST'])
@login_required
def create_leaderboard():
    """Create a new leaderboard (admin only)"""
    if not current_user.is_admin():
        return jsonify({
            'success': False,
            'message': 'Only admins can create leaderboards'
        }), 403
    
    data = request.get_json()
    
    leaderboard = Leaderboard(
        name=data['name'],
        description=data.get('description'),
        category=data['category'],
        time_period=data.get('time_period', 'all_time'),
        max_entries=data.get('max_entries', 100)
    )
    
    db.session.add(leaderboard)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Leaderboard created successfully',
        'leaderboard': leaderboard.to_dict()
    })

@gamification_bp.route('/achievements', methods=['GET'])
@login_required
def get_user_achievements():
    """Get user's achievements"""
    achievements = Achievement.query.filter_by(user_id=current_user.id).all()
    
    return jsonify({
        'success': True,
        'achievements': [achievement.to_dict() for achievement in achievements]
    })

@gamification_bp.route('/achievements/update', methods=['POST'])
@login_required
def update_achievement():
    """Update achievement progress"""
    data = request.get_json()
    achievement_type = data['achievement_type']
    new_value = data['new_value']
    
    achievement = gamification_engine.check_achievements(
        current_user.id, 
        achievement_type, 
        new_value
    )
    
    # Check for completion notification
    completion_notification = None
    if achievement.is_completed and achievement.completed_at:
        completion_notification = gamification_engine.create_notification(
            current_user.id,
            f"Achievement Unlocked: {achievement_type.replace('_', ' ').title()}",
            f"Congratulations! You've completed the {achievement_type.replace('_', ' ')} achievement.",
            'achievement_completed',
            {'achievement_type': achievement_type, 'value': new_value},
            'trophy',
            '#ffd700'
        )
    
    return jsonify({
        'success': True,
        'achievement': achievement.to_dict(),
        'completion_notification': completion_notification.to_dict() if completion_notification else None
    })

@gamification_bp.route('/notifications', methods=['GET'])
@login_required
def get_notifications():
    """Get user's notifications"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    
    query = Notification.query.filter_by(user_id=current_user.id)
    
    if unread_only:
        query = query.filter_by(is_read=False)
    
    notifications = query.order_by(desc(Notification.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'success': True,
        'notifications': [notification.to_dict() for notification in notifications.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': notifications.total,
            'pages': notifications.pages
        }
    })

@gamification_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark notification as read"""
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first()
    
    if not notification:
        return jsonify({
            'success': False,
            'message': 'Notification not found'
        }), 404
    
    notification.mark_as_read()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Notification marked as read'
    })

@gamification_bp.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read"""
    Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).update({'is_read': True, 'read_at': datetime.utcnow()})
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'All notifications marked as read'
    })

@gamification_bp.route('/dashboard', methods=['GET'])
@login_required
def gamification_dashboard():
    """Gamification dashboard page"""
    return render_template('gamification/dashboard.html', user=current_user)

@gamification_bp.route('/leaderboards-page', methods=['GET'])
@login_required
def leaderboards_page():
    """Leaderboards page"""
    return render_template('gamification/leaderboards.html', user=current_user)

@gamification_bp.route('/badges-page', methods=['GET'])
@login_required
def badges_page():
    """Badges page"""
    return render_template('gamification/badges.html', user=current_user)

# API endpoints for frontend integration
@gamification_bp.route('/api/user-stats', methods=['GET'])
@login_required
def get_user_stats():
    """Get comprehensive user statistics"""
    # Get user points
    user_points = UserPoints.query.filter_by(user_id=current_user.id).first()
    if not user_points:
        user_points = UserPoints(user_id=current_user.id)
        db.session.add(user_points)
        db.session.commit()
    
    # Get user badges
    user_badges = UserBadge.query.filter_by(user_id=current_user.id).all()
    total_badges = len(user_badges)
    
    # Get recent achievements
    recent_achievements = Achievement.query.filter_by(
        user_id=current_user.id,
        is_completed=True
    ).order_by(desc(Achievement.completed_at)).limit(5).all()
    
    # Get unread notifications count
    unread_count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()
    
    # Get leaderboard rankings
    user_rankings = []
    leaderboards = Leaderboard.query.filter_by(is_active=True).all()
    for lb in leaderboards:
        entry = LeaderboardEntry.query.filter_by(
            leaderboard_id=lb.id,
            user_id=current_user.id
        ).first()
        if entry:
            user_rankings.append({
                'leaderboard': lb.to_dict(),
                'rank': entry.rank,
                'score': entry.score
            })
    
    return jsonify({
        'success': True,
        'points': user_points.to_dict(),
        'total_badges': total_badges,
        'recent_achievements': [achievement.to_dict() for achievement in recent_achievements],
        'unread_notifications': unread_count,
        'leaderboard_rankings': user_rankings
    })

@gamification_bp.route('/api/activity', methods=['POST'])
@login_required
def record_activity():
    """Record user activity and award points"""
    data = request.get_json()
    activity_type = data['activity_type']
    points = data.get('points', 0)
    experience = data.get('experience', 0)
    metadata = data.get('metadata', {})
    
    # Add points
    user_points = UserPoints.query.filter_by(user_id=current_user.id).first()
    if not user_points:
        user_points = UserPoints(user_id=current_user.id)
        db.session.add(user_points)
    
    user_points.add_points(points, experience)
    user_points.update_streak()
    
    # Update activity count
    user_points.total_activities += 1
    
    db.session.commit()
    
    # Check for badges based on activity type
    new_badges = []
    if activity_type == 'assessment_completed':
        new_badges = gamification_engine.check_badges(
            current_user.id, 'completion', user_points.total_assessments_completed
        )
        user_points.total_assessments_completed += 1
    elif activity_type == 'course_completed':
        new_badges = gamification_engine.check_badges(
            current_user.id, 'completion', user_points.total_courses_completed
        )
        user_points.total_courses_completed += 1
    elif activity_type == 'streak':
        new_badges = gamification_engine.check_badges(
            current_user.id, 'streak', user_points.current_streak
        )
    
    db.session.commit()
    
    # Create activity notification
    activity_notification = gamification_engine.create_notification(
        current_user.id,
        f"Activity: {activity_type.replace('_', ' ').title()}",
        f"You earned {points} points for {activity_type.replace('_', ' ')}!",
        'activity',
        {'activity_type': activity_type, 'points': points, 'metadata': metadata},
        'star',
        '#28a745'
    )
    
    return jsonify({
        'success': True,
        'message': 'Activity recorded successfully',
        'new_points': user_points.to_dict(),
        'new_badges': [badge.to_dict() for badge in new_badges],
        'notification': activity_notification.to_dict()
    }) 