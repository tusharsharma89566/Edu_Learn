from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from models import db, User
from content_models import Course, Topic, LearningMaterial, Assignment, AssignmentSubmission
from datetime import datetime

moderation_bp = Blueprint('moderation', __name__)

@moderation_bp.route('/admin/moderation')
@login_required
def content_moderation():
    """Display content moderation dashboard"""
    if not current_user.is_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get pending moderation items
    pending_courses = Course.query.filter_by(is_approved=False).all()
    pending_materials = LearningMaterial.query.filter_by(is_approved=False).all()
    pending_assignments = Assignment.query.filter_by(is_approved=False).all()
    
    # Get reported content
    reported_courses = Course.query.filter_by(is_reported=True).all()
    reported_materials = LearningMaterial.query.filter_by(is_reported=True).all()
    
    moderation_stats = {
        'pending_courses': len(pending_courses),
        'pending_materials': len(pending_materials),
        'pending_assignments': len(pending_assignments),
        'reported_courses': len(reported_courses),
        'reported_materials': len(reported_materials)
    }
    
    return render_template('admin/moderation.html', 
                          user=current_user, 
                          stats=moderation_stats,
                          pending_courses=pending_courses,
                          pending_materials=pending_materials,
                          pending_assignments=pending_assignments,
                          reported_courses=reported_courses,
                          reported_materials=reported_materials)

@moderation_bp.route('/admin/moderation/approve/<int:content_id>/<content_type>')
@login_required
def approve_content(content_id, content_type):
    """Approve content"""
    if not current_user.is_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        if content_type == 'course':
            content = Course.query.get_or_404(content_id)
        elif content_type == 'material':
            content = LearningMaterial.query.get_or_404(content_id)
        elif content_type == 'assignment':
            content = Assignment.query.get_or_404(content_id)
        else:
            return jsonify({'error': 'Invalid content type'}), 400
        
        content.is_approved = True
        content.approved_by = current_user.id
        content.approved_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'message': 'Content approved successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to approve content'}), 500

@moderation_bp.route('/admin/moderation/reject/<int:content_id>/<content_type>')
@login_required
def reject_content(content_id, content_type):
    """Reject content"""
    if not current_user.is_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        if content_type == 'course':
            content = Course.query.get_or_404(content_id)
        elif content_type == 'material':
            content = LearningMaterial.query.get_or_404(content_id)
        elif content_type == 'assignment':
            content = Assignment.query.get_or_404(content_id)
        else:
            return jsonify({'error': 'Invalid content type'}), 400
        
        content.is_approved = False
        content.is_rejected = True
        content.rejected_by = current_user.id
        content.rejected_at = datetime.utcnow()
        content.rejection_reason = request.args.get('reason', 'Content did not meet platform standards')
        
        db.session.commit()
        
        return jsonify({'message': 'Content rejected successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to reject content'}), 500

@moderation_bp.route('/admin/moderation/resolve-report/<int:content_id>/<content_type>')
@login_required
def resolve_report(content_id, content_type):
    """Resolve reported content"""
    if not current_user.is_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        if content_type == 'course':
            content = Course.query.get_or_404(content_id)
        elif content_type == 'material':
            content = LearningMaterial.query.get_or_404(content_id)
        else:
            return jsonify({'error': 'Invalid content type'}), 400
        
        content.is_reported = False
        content.report_resolved_by = current_user.id
        content.report_resolved_at = datetime.utcnow()
        content.report_resolution = request.args.get('resolution', 'Report resolved after review')
        
        db.session.commit()
        
        return jsonify({'message': 'Report resolved successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to resolve report'}), 500

@moderation_bp.route('/admin/moderation/remove/<int:content_id>/<content_type>')
@login_required
def remove_content(content_id, content_type):
    """Remove content"""
    if not current_user.is_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        if content_type == 'course':
            content = Course.query.get_or_404(content_id)
        elif content_type == 'material':
            content = LearningMaterial.query.get_or_404(content_id)
        elif content_type == 'assignment':
            content = Assignment.query.get_or_404(content_id)
        else:
            return jsonify({'error': 'Invalid content type'}), 400
        
        # Mark as removed rather than deleting
        content.is_removed = True
        content.removed_by = current_user.id
        content.removed_at = datetime.utcnow()
        content.removal_reason = request.args.get('reason', 'Content violates platform policies')
        
        db.session.commit()
        
        return jsonify({'message': 'Content removed successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to remove content'}), 500
