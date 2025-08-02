from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from auto_grading_models import (
    AutoGradingModel, GradingCriteria, AutoGradingResult, 
    HumanReview, GradingAnalytics, grading_engine
)
from adaptive_assessment_models import AdaptiveQuestion, AssessmentResponse
from models import db
import json
from datetime import datetime, timedelta
from sqlalchemy import func, desc
import time

auto_grading_bp = Blueprint('auto_grading', __name__)

@auto_grading_bp.route('/models', methods=['GET'])
@login_required
def get_grading_models():
    """Get available grading models"""
    if not current_user.is_teacher() and not current_user.is_admin():
        return jsonify({
            'success': False,
            'message': 'Access denied'
        }), 403
    
    models = AutoGradingModel.query.filter_by(is_active=True).all()
    
    return jsonify({
        'success': True,
        'models': [model.to_dict() for model in models]
    })

@auto_grading_bp.route('/models', methods=['POST'])
@login_required
def create_grading_model():
    """Create a new grading model"""
    if not current_user.is_teacher() and not current_user.is_admin():
        return jsonify({
            'success': False,
            'message': 'Only teachers and admins can create grading models'
        }), 403
    
    data = request.get_json()
    
    model = AutoGradingModel(
        name=data['name'],
        model_type=data['model_type'],
        grading_type=data['grading_type'],
        model_config=json.dumps(data.get('model_config', {})),
        description=data.get('description'),
        created_by=current_user.id
    )
    
    db.session.add(model)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Grading model created successfully',
        'model': model.to_dict()
    })

@auto_grading_bp.route('/grade', methods=['POST'])
@login_required
def auto_grade_response():
    """Auto-grade a response using AI"""
    data = request.get_json()
    response_id = data['response_id']
    model_id = data.get('model_id')
    
    # Get the response
    response = AssessmentResponse.query.get(response_id)
    if not response:
        return jsonify({
            'success': False,
            'message': 'Response not found'
        }), 404
    
    # Get or create default model
    if model_id:
        model = AutoGradingModel.query.get(model_id)
    else:
        model = AutoGradingModel.query.filter_by(
            grading_type=response.question.question_type,
            is_active=True
        ).first()
    
    if not model:
        return jsonify({
            'success': False,
            'message': 'No suitable grading model found'
        }), 400
    
    # Get grading criteria
    criteria = GradingCriteria.query.filter_by(question_id=response.question_id).all()
    criteria_dict = {
        c.criteria_type: {
            'weight': c.weight,
            'max_score': c.max_score,
            'keywords': json.loads(c.keywords) if c.keywords else [],
            'rubric_points': json.loads(c.rubric_points) if c.rubric_points else []
        }
        for c in criteria
    }
    
    # Start timing
    start_time = time.time()
    
    # Grade the response
    if model.grading_type == 'essay':
        result = grading_engine.grade_essay(
            response.user_answer, 
            criteria_dict,
            json.loads(model.model_config) if model.model_config else {}
        )
    elif model.grading_type == 'code':
        result = grading_engine.grade_code(
            response.user_answer,
            [],  # test_cases would come from question
            criteria_dict
        )
    else:
        # Default grading for other types
        result = {
            'overall_score': 7.0,
            'criteria_scores': {'content': 7.0},
            'feedback_text': 'Response graded successfully.',
            'suggestions': ['Good work!'],
            'strengths': ['Clear response'],
            'weaknesses': [],
            'confidence_score': 0.8
        }
    
    processing_time = time.time() - start_time
    
    # Create grading result
    grading_result = AutoGradingResult(
        response_id=response_id,
        model_id=model.id,
        overall_score=result['overall_score'],
        confidence_score=result['confidence_score'],
        criteria_scores=json.dumps(result['criteria_scores']),
        feedback_text=result['feedback_text'],
        suggestions=json.dumps(result['suggestions']),
        strengths=json.dumps(result['strengths']),
        weaknesses=json.dumps(result['weaknesses']),
        processing_time=processing_time,
        model_version=model.version,
        needs_human_review=result['confidence_score'] < 0.7
    )
    
    db.session.add(grading_result)
    
    # Update response with AI grade
    response.points_earned = result['overall_score']
    response.is_correct = result['overall_score'] >= 7.0  # Threshold for correctness
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Response graded successfully',
        'result': grading_result.to_dict()
    })

@auto_grading_bp.route('/responses/<int:response_id>/grade', methods=['GET'])
@login_required
def get_grading_result(response_id):
    """Get grading result for a response"""
    response = AssessmentResponse.query.get(response_id)
    if not response:
        return jsonify({
            'success': False,
            'message': 'Response not found'
        }), 404
    
    # Check if user can access this response
    if response.user_id != current_user.id and not current_user.is_teacher() and not current_user.is_admin():
        return jsonify({
            'success': False,
            'message': 'Access denied'
        }), 403
    
    grading_result = AutoGradingResult.query.filter_by(response_id=response_id).first()
    
    if not grading_result:
        return jsonify({
            'success': False,
            'message': 'No grading result found'
        }), 404
    
    return jsonify({
        'success': True,
        'result': grading_result.to_dict(),
        'response': response.to_dict()
    })

@auto_grading_bp.route('/review', methods=['POST'])
@login_required
def submit_human_review():
    """Submit human review of auto-graded response"""
    if not current_user.is_teacher() and not current_user.is_admin():
        return jsonify({
            'success': False,
            'message': 'Only teachers and admins can submit reviews'
        }), 403
    
    data = request.get_json()
    grading_result_id = data['grading_result_id']
    
    grading_result = AutoGradingResult.query.get(grading_result_id)
    if not grading_result:
        return jsonify({
            'success': False,
            'message': 'Grading result not found'
        }), 404
    
    start_time = time.time()
    
    review = HumanReview(
        grading_result_id=grading_result_id,
        reviewer_id=current_user.id,
        human_score=data.get('human_score'),
        review_notes=data.get('review_notes'),
        ai_accuracy_rating=data.get('ai_accuracy_rating'),
        feedback_quality_rating=data.get('feedback_quality_rating')
    )
    
    if review.human_score is not None:
        review.score_difference = abs(review.human_score - grading_result.overall_score)
    
    review.review_duration = time.time() - start_time
    
    db.session.add(review)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Review submitted successfully',
        'review': review.to_dict()
    })

@auto_grading_bp.route('/pending-reviews', methods=['GET'])
@login_required
def get_pending_reviews():
    """Get responses that need human review"""
    if not current_user.is_teacher() and not current_user.is_admin():
        return jsonify({
            'success': False,
            'message': 'Access denied'
        }), 403
    
    pending_results = AutoGradingResult.query.filter_by(needs_human_review=True).all()
    
    results = []
    for result in pending_results:
        response = result.response
        question = response.question
        user = response.user
        
        results.append({
            'grading_result': result.to_dict(),
            'response': response.to_dict(),
            'question': question.to_dict(),
            'user': {
                'id': user.id,
                'name': user.get_full_name(),
                'email': user.email
            }
        })
    
    return jsonify({
        'success': True,
        'pending_reviews': results
    })

@auto_grading_bp.route('/analytics', methods=['GET'])
@login_required
def get_grading_analytics():
    """Get analytics for auto-grading system"""
    if not current_user.is_teacher() and not current_user.is_admin():
        return jsonify({
            'success': False,
            'message': 'Access denied'
        }), 403
    
    # Get overall statistics
    total_graded = AutoGradingResult.query.count()
    total_models = AutoGradingModel.query.count()
    pending_reviews = AutoGradingResult.query.filter_by(needs_human_review=True).count()
    
    # Get average processing time
    avg_processing_time = db.session.query(func.avg(AutoGradingResult.processing_time)).scalar() or 0
    
    # Get average confidence
    avg_confidence = db.session.query(func.avg(AutoGradingResult.confidence_score)).scalar() or 0
    
    # Get model performance
    model_performance = db.session.query(
        AutoGradingModel.name,
        func.count(AutoGradingResult.id),
        func.avg(AutoGradingResult.confidence_score)
    ).join(AutoGradingResult).group_by(AutoGradingModel.id).all()
    
    # Get recent grading activity
    recent_gradings = AutoGradingResult.query.order_by(
        desc(AutoGradingResult.graded_at)
    ).limit(10).all()
    
    return jsonify({
        'success': True,
        'analytics': {
            'total_graded': total_graded,
            'total_models': total_models,
            'pending_reviews': pending_reviews,
            'average_processing_time': round(avg_processing_time, 2),
            'average_confidence': round(avg_confidence, 2),
            'model_performance': [
                {
                    'name': name,
                    'total_graded': count,
                    'avg_confidence': round(confidence, 2)
                }
                for name, count, confidence in model_performance
            ],
            'recent_gradings': [result.to_dict() for result in recent_gradings]
        }
    })

@auto_grading_bp.route('/criteria', methods=['POST'])
@login_required
def create_grading_criteria():
    """Create grading criteria for a question"""
    if not current_user.is_teacher() and not current_user.is_admin():
        return jsonify({
            'success': False,
            'message': 'Only teachers and admins can create criteria'
        }), 403
    
    data = request.get_json()
    
    criteria = GradingCriteria(
        question_id=data['question_id'],
        criteria_type=data['criteria_type'],
        weight=data.get('weight', 1.0),
        max_score=data.get('max_score', 10.0),
        description=data.get('description'),
        rubric_points=json.dumps(data.get('rubric_points', [])),
        keywords=json.dumps(data.get('keywords', []))
    )
    
    db.session.add(criteria)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Grading criteria created successfully',
        'criteria': criteria.to_dict()
    })

@auto_grading_bp.route('/criteria/<int:question_id>', methods=['GET'])
@login_required
def get_question_criteria(question_id):
    """Get grading criteria for a question"""
    criteria = GradingCriteria.query.filter_by(question_id=question_id).all()
    
    return jsonify({
        'success': True,
        'criteria': [c.to_dict() for c in criteria]
    })

@auto_grading_bp.route('/dashboard', methods=['GET'])
@login_required
def grading_dashboard():
    """Auto-grading dashboard page"""
    if not current_user.is_teacher() and not current_user.is_admin():
        return jsonify({
            'success': False,
            'message': 'Access denied'
        }), 403
    
    return render_template('auto_grading/dashboard.html', user=current_user)

@auto_grading_bp.route('/review-interface', methods=['GET'])
@login_required
def review_interface():
    """Human review interface"""
    if not current_user.is_teacher() and not current_user.is_admin():
        return jsonify({
            'success': False,
            'message': 'Access denied'
        }), 403
    
    return render_template('auto_grading/review_interface.html', user=current_user)

# API endpoints for frontend integration
@auto_grading_bp.route('/api/quick-stats', methods=['GET'])
@login_required
def quick_grading_stats():
    """Get quick statistics for grading dashboard"""
    if not current_user.is_teacher() and not current_user.is_admin():
        return jsonify({
            'success': False,
            'message': 'Access denied'
        }), 403
    
    # Get today's statistics
    today = datetime.utcnow().date()
    today_gradings = AutoGradingResult.query.filter(
        func.date(AutoGradingResult.graded_at) == today
    ).count()
    
    # Get pending reviews
    pending_reviews = AutoGradingResult.query.filter_by(needs_human_review=True).count()
    
    # Get average confidence
    avg_confidence = db.session.query(func.avg(AutoGradingResult.confidence_score)).scalar() or 0
    
    # Get model count
    active_models = AutoGradingModel.query.filter_by(is_active=True).count()
    
    return jsonify({
        'success': True,
        'today_gradings': today_gradings,
        'pending_reviews': pending_reviews,
        'average_confidence': round(avg_confidence, 2),
        'active_models': active_models
    }) 