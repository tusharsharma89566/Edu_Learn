from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from adaptive_assessment_models import (
    AdaptiveQuestion, AdaptiveAssessment, AssessmentResponse, 
    AssessmentAnalytics, assessment_engine
)
from models import db
import json
from datetime import datetime, timedelta
from sqlalchemy import func, desc

adaptive_bp = Blueprint('adaptive', __name__)

@adaptive_bp.route('/questions', methods=['GET'])
@login_required
def get_questions():
    """Get questions for a topic or course"""
    topic_id = request.args.get('topic_id', type=int)
    course_id = request.args.get('course_id', type=int)
    difficulty = request.args.get('difficulty')
    question_type = request.args.get('question_type')
    limit = request.args.get('limit', 10, type=int)
    
    query = AdaptiveQuestion.query.filter_by(is_active=True)
    
    if topic_id:
        query = query.filter_by(topic_id=topic_id)
    if course_id:
        query = query.filter_by(course_id=course_id)
    if difficulty:
        query = query.filter_by(difficulty_level=difficulty)
    if question_type:
        query = query.filter_by(question_type=question_type)
    
    questions = query.limit(limit).all()
    
    return jsonify({
        'success': True,
        'questions': [q.to_dict() for q in questions]
    })

@adaptive_bp.route('/questions', methods=['POST'])
@login_required
def create_question():
    """Create a new adaptive question"""
    if not current_user.is_teacher() and not current_user.is_admin():
        return jsonify({
            'success': False,
            'message': 'Only teachers and admins can create questions'
        }), 403
    
    data = request.get_json()
    
    question = AdaptiveQuestion(
        topic_id=data['topic_id'],
        course_id=data['course_id'],
        question_text=data['question_text'],
        question_type=data['question_type'],
        difficulty_level=data['difficulty_level'],
        points=data.get('points', 1),
        options=json.dumps(data.get('options', [])),
        correct_answer=data['correct_answer'],
        explanation=data.get('explanation'),
        initial_difficulty=data.get('initial_difficulty', 0.5),
        discrimination=data.get('discrimination', 1.0),
        guessing=data.get('guessing', 0.25),
        time_limit=data.get('time_limit', 60),
        tags=json.dumps(data.get('tags', [])),
        learning_objectives=json.dumps(data.get('learning_objectives', [])),
        created_by=current_user.id
    )
    
    db.session.add(question)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Question created successfully',
        'question': question.to_dict()
    })

@adaptive_bp.route('/assessments', methods=['GET'])
@login_required
def get_assessments():
    """Get user's assessments"""
    status = request.args.get('status')
    course_id = request.args.get('course_id', type=int)
    
    query = AdaptiveAssessment.query.filter_by(user_id=current_user.id)
    
    if status:
        query = query.filter_by(status=status)
    if course_id:
        query = query.filter_by(course_id=course_id)
    
    assessments = query.order_by(desc(AdaptiveAssessment.started_at)).all()
    
    return jsonify({
        'success': True,
        'assessments': [a.to_dict() for a in assessments]
    })

@adaptive_bp.route('/assessments', methods=['POST'])
@login_required
def create_assessment():
    """Create a new adaptive assessment"""
    data = request.get_json()
    
    assessment = AdaptiveAssessment(
        user_id=current_user.id,
        course_id=data['course_id'],
        topic_id=data.get('topic_id'),
        title=data['title'],
        description=data.get('description'),
        assessment_type=data.get('assessment_type', 'adaptive'),
        max_questions=data.get('max_questions', 20),
        time_limit_minutes=data.get('time_limit_minutes', 30),
        initial_difficulty=data.get('initial_difficulty', 0.5),
        difficulty_adjustment_rate=data.get('difficulty_adjustment_rate', 0.1),
        confidence_threshold=data.get('confidence_threshold', 0.8)
    )
    
    db.session.add(assessment)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Assessment created successfully',
        'assessment': assessment.to_dict()
    })

@adaptive_bp.route('/assessments/<int:assessment_id>/start', methods=['POST'])
@login_required
def start_assessment(assessment_id):
    """Start an assessment session"""
    assessment = AdaptiveAssessment.query.filter_by(
        id=assessment_id,
        user_id=current_user.id
    ).first()
    
    if not assessment:
        return jsonify({
            'success': False,
            'message': 'Assessment not found'
        }), 404
    
    if assessment.status != 'in_progress':
        return jsonify({
            'success': False,
            'message': 'Assessment is not available'
        }), 400
    
    # Get first question
    first_question = assessment_engine.select_next_question(assessment, [])
    
    if not first_question:
        return jsonify({
            'success': False,
            'message': 'No questions available for this assessment'
        }), 400
    
    return jsonify({
        'success': True,
        'assessment': assessment.to_dict(),
        'question': first_question.to_dict()
    })

@adaptive_bp.route('/assessments/<int:assessment_id>/question', methods=['GET'])
@login_required
def get_current_question(assessment_id):
    """Get current question for an assessment"""
    assessment = AdaptiveAssessment.query.filter_by(
        id=assessment_id,
        user_id=current_user.id
    ).first()
    
    if not assessment:
        return jsonify({
            'success': False,
            'message': 'Assessment not found'
        }), 404
    
    if assessment.status != 'in_progress':
        return jsonify({
            'success': False,
            'message': 'Assessment is not in progress'
        }), 400
    
    # Get user responses
    user_responses = AssessmentResponse.query.filter_by(
        assessment_id=assessment_id
    ).all()
    
    # Select next question
    next_question = assessment_engine.select_next_question(assessment, user_responses)
    
    if not next_question:
        # Assessment is complete
        assessment.complete_assessment()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'assessment_complete': True,
            'assessment': assessment.to_dict()
        })
    
    return jsonify({
        'success': True,
        'question': next_question.to_dict(),
        'progress': assessment.get_progress_percentage(),
        'current_difficulty': assessment.current_difficulty
    })

@adaptive_bp.route('/assessments/<int:assessment_id>/answer', methods=['POST'])
@login_required
def submit_answer(assessment_id):
    """Submit an answer for the current question"""
    assessment = AdaptiveAssessment.query.filter_by(
        id=assessment_id,
        user_id=current_user.id
    ).first()
    
    if not assessment:
        return jsonify({
            'success': False,
            'message': 'Assessment not found'
        }), 404
    
    if assessment.status != 'in_progress':
        return jsonify({
            'success': False,
            'message': 'Assessment is not in progress'
        }), 400
    
    data = request.get_json()
    question_id = data['question_id']
    user_answer = data['user_answer']
    response_time = data.get('response_time', 0)
    
    # Get the question
    question = AdaptiveQuestion.query.get(question_id)
    if not question:
        return jsonify({
            'success': False,
            'message': 'Question not found'
        }), 404
    
    # Check if answer is correct
    is_correct = user_answer.strip().lower() == question.correct_answer.strip().lower()
    points_earned = question.points if is_correct else 0
    
    # Create response
    response = AssessmentResponse(
        assessment_id=assessment_id,
        question_id=question_id,
        user_id=current_user.id,
        user_answer=user_answer,
        is_correct=is_correct,
        points_earned=points_earned,
        response_time_seconds=response_time,
        question_difficulty=question.get_difficulty_score(),
        user_ability_estimate=assessment_engine.estimate_user_ability(
            AssessmentResponse.query.filter_by(assessment_id=assessment_id).all()
        )
    )
    
    db.session.add(response)
    
    # Update assessment progress
    assessment.questions_answered += 1
    if is_correct:
        assessment.correct_answers += 1
    
    # Adjust difficulty
    assessment.adjust_difficulty(is_correct, response_time)
    
    # Update question statistics
    question.update_statistics(is_correct, response_time)
    
    db.session.commit()
    
    # Generate feedback
    feedback = assessment_engine.generate_feedback(response)
    
    # Check if assessment should terminate early
    should_terminate = assessment_engine.should_terminate_assessment(
        assessment, 
        AssessmentResponse.query.filter_by(assessment_id=assessment_id).all()
    )
    
    if should_terminate or assessment.questions_answered >= assessment.max_questions:
        assessment.complete_assessment()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'assessment_complete': True,
            'assessment': assessment.to_dict(),
            'feedback': feedback
        })
    
    return jsonify({
        'success': True,
        'feedback': feedback,
        'progress': assessment.get_progress_percentage(),
        'current_difficulty': assessment.current_difficulty
    })

@adaptive_bp.route('/assessments/<int:assessment_id>/results', methods=['GET'])
@login_required
def get_assessment_results(assessment_id):
    """Get detailed results for a completed assessment"""
    assessment = AdaptiveAssessment.query.filter_by(
        id=assessment_id,
        user_id=current_user.id
    ).first()
    
    if not assessment:
        return jsonify({
            'success': False,
            'message': 'Assessment not found'
        }), 404
    
    if assessment.status != 'completed':
        return jsonify({
            'success': False,
            'message': 'Assessment is not completed'
        }), 400
    
    # Get all responses
    responses = AssessmentResponse.query.filter_by(assessment_id=assessment_id).all()
    
    # Calculate detailed statistics
    question_types = {}
    difficulty_breakdown = {}
    time_analysis = {}
    
    for response in responses:
        # Question type analysis
        q_type = response.question.question_type
        if q_type not in question_types:
            question_types[q_type] = {'total': 0, 'correct': 0}
        question_types[q_type]['total'] += 1
        if response.is_correct:
            question_types[q_type]['correct'] += 1
        
        # Difficulty analysis
        diff_level = response.question.difficulty_level
        if diff_level not in difficulty_breakdown:
            difficulty_breakdown[diff_level] = {'total': 0, 'correct': 0}
        difficulty_breakdown[diff_level]['total'] += 1
        if response.is_correct:
            difficulty_breakdown[diff_level]['correct'] += 1
        
        # Time analysis
        time_range = 'fast' if response.response_time_seconds < 30 else 'medium' if response.response_time_seconds < 60 else 'slow'
        if time_range not in time_analysis:
            time_analysis[time_range] = {'total': 0, 'correct': 0}
        time_analysis[time_range]['total'] += 1
        if response.is_correct:
            time_analysis[time_range]['correct'] += 1
    
    return jsonify({
        'success': True,
        'assessment': assessment.to_dict(),
        'responses': [r.to_dict() for r in responses],
        'statistics': {
            'question_types': question_types,
            'difficulty_breakdown': difficulty_breakdown,
            'time_analysis': time_analysis,
            'total_questions': len(responses),
            'correct_answers': sum(1 for r in responses if r.is_correct),
            'average_time': sum(r.response_time_seconds for r in responses) / len(responses) if responses else 0
        }
    })

@adaptive_bp.route('/analytics', methods=['GET'])
@login_required
def get_user_analytics():
    """Get user's assessment analytics"""
    course_id = request.args.get('course_id', type=int)
    topic_id = request.args.get('topic_id', type=int)
    
    query = AssessmentAnalytics.query.filter_by(user_id=current_user.id)
    
    if course_id:
        query = query.filter_by(course_id=course_id)
    if topic_id:
        query = query.filter_by(topic_id=topic_id)
    
    analytics = query.first()
    
    if not analytics:
        # Create analytics record if it doesn't exist
        analytics = AssessmentAnalytics(
            user_id=current_user.id,
            course_id=course_id,
            topic_id=topic_id
        )
        db.session.add(analytics)
        db.session.commit()
    
    return jsonify({
        'success': True,
        'analytics': analytics.to_dict()
    })

@adaptive_bp.route('/analytics/update', methods=['POST'])
@login_required
def update_analytics():
    """Update user analytics after assessment completion"""
    data = request.get_json()
    assessment_id = data['assessment_id']
    
    assessment = AdaptiveAssessment.query.get(assessment_id)
    if not assessment or assessment.user_id != current_user.id:
        return jsonify({
            'success': False,
            'message': 'Assessment not found'
        }), 404
    
    # Get or create analytics record
    analytics = AssessmentAnalytics.query.filter_by(
        user_id=current_user.id,
        course_id=assessment.course_id,
        topic_id=assessment.topic_id
    ).first()
    
    if not analytics:
        analytics = AssessmentAnalytics(
            user_id=current_user.id,
            course_id=assessment.course_id,
            topic_id=assessment.topic_id
        )
        db.session.add(analytics)
    
    # Update analytics
    analytics.total_assessments += 1
    if assessment.status == 'completed':
        analytics.completed_assessments += 1
        analytics.last_assessment_date = datetime.utcnow()
    
    # Update scores
    if assessment.final_score:
        if analytics.average_score == 0:
            analytics.average_score = assessment.final_score
        else:
            total_score = analytics.average_score * (analytics.completed_assessments - 1) + assessment.final_score
            analytics.average_score = total_score / analytics.completed_assessments
        
        if assessment.final_score > analytics.best_score:
            analytics.best_score = assessment.final_score
    
    # Update question statistics
    responses = AssessmentResponse.query.filter_by(assessment_id=assessment_id).all()
    analytics.total_questions_answered += len(responses)
    analytics.total_correct_answers += sum(1 for r in responses if r.is_correct)
    
    # Update time statistics
    total_time = sum(r.response_time_seconds for r in responses)
    if analytics.average_time_per_question == 0:
        analytics.average_time_per_question = total_time / len(responses) if responses else 0
    else:
        total_avg_time = analytics.average_time_per_question * (analytics.total_questions_answered - len(responses))
        analytics.average_time_per_question = (total_avg_time + total_time) / analytics.total_questions_answered
    
    analytics.total_time_spent_minutes += assessment.time_spent_minutes
    
    # Update proficiency level
    if assessment.proficiency_level:
        analytics.current_proficiency_level = assessment.proficiency_level
    
    # Update difficulty progression
    difficulty_progression = json.loads(analytics.difficulty_progression) if analytics.difficulty_progression else []
    difficulty_progression.append(assessment.current_difficulty)
    analytics.difficulty_progression = json.dumps(difficulty_progression[-10:])  # Keep last 10
    
    analytics.last_updated = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Analytics updated successfully',
        'analytics': analytics.to_dict()
    })

@adaptive_bp.route('/dashboard', methods=['GET'])
@login_required
def assessment_dashboard():
    """Assessment dashboard page"""
    return render_template('adaptive/dashboard.html', user=current_user)

@adaptive_bp.route('/take-assessment', methods=['GET'])
@login_required
def take_assessment_page():
    """Take assessment page"""
    return render_template('adaptive/take_assessment.html', user=current_user)

@adaptive_bp.route('/results', methods=['GET'])
@login_required
def results_page():
    """Results page"""
    return render_template('adaptive/results.html', user=current_user)

# Admin routes
@adaptive_bp.route('/admin/questions', methods=['GET'])
@login_required
def admin_get_questions():
    """Admin: Get all questions"""
    if not current_user.is_admin():
        return jsonify({
            'success': False,
            'message': 'Admin access required'
        }), 403
    
    questions = AdaptiveQuestion.query.all()
    
    return jsonify({
        'success': True,
        'questions': [q.to_dict() for q in questions]
    })

@adaptive_bp.route('/admin/analytics', methods=['GET'])
@login_required
def admin_analytics():
    """Admin: Get system-wide analytics"""
    if not current_user.is_admin():
        return jsonify({
            'success': False,
            'message': 'Admin access required'
        }), 403
    
    # Get system statistics
    total_questions = AdaptiveQuestion.query.count()
    total_assessments = AdaptiveAssessment.query.count()
    completed_assessments = AdaptiveAssessment.query.filter_by(status='completed').count()
    total_responses = AssessmentResponse.query.count()
    
    # Get average scores
    avg_score = db.session.query(func.avg(AdaptiveAssessment.final_score)).scalar() or 0
    
    # Get question type distribution
    question_types = db.session.query(
        AdaptiveQuestion.question_type,
        func.count(AdaptiveQuestion.id)
    ).group_by(AdaptiveQuestion.question_type).all()
    
    # Get difficulty distribution
    difficulty_dist = db.session.query(
        AdaptiveQuestion.difficulty_level,
        func.count(AdaptiveQuestion.id)
    ).group_by(AdaptiveQuestion.difficulty_level).all()
    
    return jsonify({
        'success': True,
        'statistics': {
            'total_questions': total_questions,
            'total_assessments': total_assessments,
            'completed_assessments': completed_assessments,
            'total_responses': total_responses,
            'average_score': round(avg_score, 2),
            'completion_rate': round((completed_assessments / total_assessments * 100) if total_assessments > 0 else 0, 2)
        },
        'question_types': dict(question_types),
        'difficulty_distribution': dict(difficulty_dist)
    })

# API endpoints for frontend integration
@adaptive_bp.route('/api/quick-stats', methods=['GET'])
@login_required
def quick_stats():
    """Get quick statistics for dashboard"""
    # Get recent assessments
    recent_assessments = AdaptiveAssessment.query.filter_by(
        user_id=current_user.id
    ).order_by(desc(AdaptiveAssessment.started_at)).limit(5).all()
    
    # Get analytics
    analytics = AssessmentAnalytics.query.filter_by(user_id=current_user.id).first()
    
    # Get current proficiency level
    current_level = analytics.current_proficiency_level if analytics else 'beginner'
    
    # Get improvement trend
    improvement_trend = 0
    if analytics and analytics.improvement_rate:
        improvement_trend = analytics.improvement_rate
    
    return jsonify({
        'success': True,
        'recent_assessments': [a.to_dict() for a in recent_assessments],
        'current_proficiency': current_level,
        'improvement_trend': improvement_trend,
        'total_assessments': analytics.total_assessments if analytics else 0,
        'average_score': analytics.average_score if analytics else 0
    }) 