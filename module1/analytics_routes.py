from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from models import db, User
from content_models import Course, Enrollment, Assignment, AssignmentSubmission
from progress_models import LearningSession
from datetime import datetime, timedelta
import json

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/admin/analytics')
@login_required
def system_analytics():
    """Display system-wide analytics"""
    if not current_user.is_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get user statistics
    total_users = User.query.count()
    total_students = User.query.filter_by(role='student').count()
    total_teachers = User.query.filter_by(role='teacher').count()
    total_admins = User.query.filter_by(role='admin').count()
    
    # Get course statistics
    total_courses = Course.query.count()
    total_enrollments = Enrollment.query.count()
    
    # Get assignment statistics
    total_assignments = Assignment.query.count()
    total_submissions = AssignmentSubmission.query.count()
    
    # Get recent activity (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_sessions = LearningSession.query.filter(
        LearningSession.session_start >= thirty_days_ago
    ).count()
    
    # User registration trend (last 7 days)
    user_trend = []
    for i in range(7):
        date = datetime.utcnow() - timedelta(days=i)
        count = User.query.filter(
            db.func.date(User.created_at) == date.date()
        ).count()
        user_trend.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    
    # Course enrollment trend (last 7 days)
    enrollment_trend = []
    for i in range(7):
        date = datetime.utcnow() - timedelta(days=i)
        count = Enrollment.query.filter(
            db.func.date(Enrollment.enrollment_date) == date.date()
        ).count()
        enrollment_trend.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    
    stats = {
        'total_users': total_users,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_admins': total_admins,
        'total_courses': total_courses,
        'total_enrollments': total_enrollments,
        'total_assignments': total_assignments,
        'total_submissions': total_submissions,
        'recent_sessions': recent_sessions,
        'user_trend': user_trend,
        'enrollment_trend': enrollment_trend
    }
    
    return render_template('admin/analytics.html', user=current_user, stats=stats)

@analytics_bp.route('/admin/analytics/data')
@login_required
def analytics_data():
    """API endpoint for analytics data"""
    if not current_user.is_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get user statistics
    total_users = User.query.count()
    total_students = User.query.filter_by(role='student').count()
    total_teachers = User.query.filter_by(role='teacher').count()
    total_admins = User.query.filter_by(role='admin').count()
    
    # Get course statistics
    total_courses = Course.query.count()
    total_enrollments = Enrollment.query.count()
    
    # Get assignment statistics
    total_assignments = Assignment.query.count()
    total_submissions = AssignmentSubmission.query.count()
    
    # Get recent activity (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_sessions = LearningSession.query.filter(
        LearningSession.session_start >= thirty_days_ago
    ).count()
    
    # User registration trend (last 7 days)
    user_trend = []
    for i in range(7):
        date = datetime.utcnow() - timedelta(days=i)
        count = User.query.filter(
            db.func.date(User.created_at) == date.date()
        ).count()
        user_trend.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    
    # Course enrollment trend (last 7 days)
    enrollment_trend = []
    for i in range(7):
        date = datetime.utcnow() - timedelta(days=i)
        count = Enrollment.query.filter(
            db.func.date(Enrollment.enrollment_date) == date.date()
        ).count()
        enrollment_trend.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    
    return jsonify({
        'total_users': total_users,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_admins': total_admins,
        'total_courses': total_courses,
        'total_enrollments': total_enrollments,
        'total_assignments': total_assignments,
        'total_submissions': total_submissions,
        'recent_sessions': recent_sessions,
        'user_trend': user_trend,
        'enrollment_trend': enrollment_trend
    })
