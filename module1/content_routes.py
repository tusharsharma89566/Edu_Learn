from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
from content_models import (
    db, Course, Topic, LearningMaterial, Video, Quiz, QuizQuestion, 
    QuizOption, Assignment, Enrollment, QuizAttempt, QuizAnswer, AssignmentSubmission
)
from models import User

content_bp = Blueprint('content', __name__)

# File upload configuration
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'ppt', 'pptx', 'mp4', 'avi', 'mov'}
UPLOAD_FOLDER = 'uploads'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file, folder):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add unique identifier to prevent filename conflicts
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(UPLOAD_FOLDER, folder, unique_filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file.save(file_path)
        return f"/{file_path}"
    return None

# Course Management Routes
@content_bp.route('/courses')
@login_required
def courses():
    if current_user.is_admin():
        courses = Course.query.all()
    elif current_user.is_teacher():
        courses = Course.query.filter_by(instructor_id=current_user.id).all()
    else:
        # Students see enrolled courses
        enrollments = Enrollment.query.filter_by(student_id=current_user.id, is_active=True).all()
        courses = [enrollment.course for enrollment in enrollments]
    
    return render_template('content/courses.html', courses=courses)

@content_bp.route('/courses/create', methods=['GET', 'POST'])
@login_required
def create_course():
    if not current_user.is_teacher() and not current_user.is_admin():
        flash('Access denied. Teachers and admins only.', 'error')
        return redirect(url_for('content.courses'))
    
    if request.method == 'POST':
        data = request.form.to_dict()
        
        # Generate unique course code
        course_code = f"COURSE_{uuid.uuid4().hex[:8].upper()}"
        
        course = Course(
            title=data.get('title'),
            description=data.get('description'),
            code=course_code,
            instructor_id=current_user.id,
            category=data.get('category'),
            level=data.get('level'),
            duration_hours=float(data.get('duration_hours', 0)),
            max_students=int(data.get('max_students', 50)),
            is_public=data.get('is_public') == 'on'
        )
        
        # Handle thumbnail upload
        if 'thumbnail' in request.files:
            thumbnail_url = save_file(request.files['thumbnail'], 'thumbnails')
            if thumbnail_url:
                course.thumbnail_url = thumbnail_url
        
        db.session.add(course)
        db.session.commit()
        
        flash('Course created successfully!', 'success')
        return redirect(url_for('content.courses'))
    
    return render_template('content/create_course.html')

@content_bp.route('/courses/<int:course_id>')
@login_required
def view_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Check if user has access to this course
    if not current_user.is_admin() and not current_user.is_teacher():
        enrollment = Enrollment.query.filter_by(
            student_id=current_user.id, 
            course_id=course_id, 
            is_active=True
        ).first()
        if not enrollment:
            flash('You are not enrolled in this course.', 'error')
            return redirect(url_for('content.courses'))
    
    topics = Topic.query.filter_by(course_id=course_id, is_active=True).order_by(Topic.order_index).all()
    enrollments = Enrollment.query.filter_by(course_id=course_id, is_active=True).all()
    
    return render_template('content/view_course.html', 
                         course=course, topics=topics, enrollments=enrollments)

@content_bp.route('/courses/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Check permissions
    if not current_user.is_admin() and course.instructor_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('content.courses'))
    
    if request.method == 'POST':
        data = request.form.to_dict()
        
        course.title = data.get('title')
        course.description = data.get('description')
        course.category = data.get('category')
        course.level = data.get('level')
        course.duration_hours = float(data.get('duration_hours', 0))
        course.max_students = int(data.get('max_students', 50))
        course.is_public = data.get('is_public') == 'on'
        course.updated_at = datetime.utcnow()
        
        # Handle thumbnail upload
        if 'thumbnail' in request.files:
            thumbnail_url = save_file(request.files['thumbnail'], 'thumbnails')
            if thumbnail_url:
                course.thumbnail_url = thumbnail_url
        
        db.session.commit()
        flash('Course updated successfully!', 'success')
        return redirect(url_for('content.view_course', course_id=course_id))
    
    return render_template('content/edit_course.html', course=course)

# Topic Management Routes
@content_bp.route('/courses/<int:course_id>/topics/create', methods=['GET', 'POST'])
@login_required
def create_topic(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Check permissions
    if not current_user.is_admin() and course.instructor_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('content.view_course', course_id=course_id))
    
    if request.method == 'POST':
        data = request.form.to_dict()
        
        # Get next order index
        max_order = db.session.query(db.func.max(Topic.order_index)).filter_by(course_id=course_id).scalar() or 0
        
        topic = Topic(
            title=data.get('title'),
            description=data.get('description'),
            course_id=course_id,
            order_index=max_order + 1,
            duration_minutes=int(data.get('duration_minutes', 0))
        )
        
        db.session.add(topic)
        db.session.commit()
        
        flash('Topic created successfully!', 'success')
        return redirect(url_for('content.view_course', course_id=course_id))
    
    return render_template('content/create_topic.html', course=course)

@content_bp.route('/topics/<int:topic_id>')
@login_required
def view_topic(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    
    # Check if user has access to this topic's course
    if not current_user.is_admin() and not current_user.is_teacher():
        enrollment = Enrollment.query.filter_by(
            student_id=current_user.id, 
            course_id=topic.course_id, 
            is_active=True
        ).first()
        if not enrollment:
            flash('Access denied.', 'error')
            return redirect(url_for('content.courses'))
    
    materials = LearningMaterial.query.filter_by(topic_id=topic_id, is_active=True).order_by(LearningMaterial.order_index).all()
    quizzes = Quiz.query.filter_by(topic_id=topic_id, is_active=True).all()
    
    return render_template('content/view_topic.html', 
                         topic=topic, materials=materials, quizzes=quizzes)

# Learning Material Management Routes
@content_bp.route('/topics/<int:topic_id>/materials/create', methods=['GET', 'POST'])
@login_required
def create_material(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    course = topic.course
    
    # Check permissions
    if not current_user.is_admin() and course.instructor_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('content.view_topic', topic_id=topic_id))
    
    if request.method == 'POST':
        data = request.form.to_dict()
        
        # Get next order index
        max_order = db.session.query(db.func.max(LearningMaterial.order_index)).filter_by(topic_id=topic_id).scalar() or 0
        
        material = LearningMaterial(
            title=data.get('title'),
            description=data.get('description'),
            topic_id=topic_id,
            material_type=data.get('material_type'),
            order_index=max_order + 1,
            is_required=data.get('is_required') == 'on'
        )
        
        # Handle file upload
        if 'file' in request.files:
            file_url = save_file(request.files['file'], 'materials')
            if file_url:
                material.file_url = file_url
                material.file_size = request.files['file'].content_length
        
        # For videos, create video record
        if material.material_type == 'video' and material.file_url:
            video = Video(
                title=material.title,
                description=material.description,
                material_id=material.id,
                video_url=material.file_url
            )
            db.session.add(video)
        
        db.session.add(material)
        db.session.commit()
        
        flash('Learning material created successfully!', 'success')
        return redirect(url_for('content.view_topic', topic_id=topic_id))
    
    return render_template('content/create_material.html', topic=topic)

# Quiz Management Routes
@content_bp.route('/topics/<int:topic_id>/quizzes/create', methods=['GET', 'POST'])
@login_required
def create_quiz(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    course = topic.course
    
    # Check permissions
    if not current_user.is_admin() and course.instructor_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('content.view_topic', topic_id=topic_id))
    
    if request.method == 'POST':
        data = request.form.to_dict()
        
        quiz = Quiz(
            title=data.get('title'),
            description=data.get('description'),
            topic_id=topic_id,
            quiz_type=data.get('quiz_type'),
            time_limit_minutes=int(data.get('time_limit_minutes', 0)) if data.get('time_limit_minutes') else None,
            passing_score=int(data.get('passing_score', 70)),
            max_attempts=int(data.get('max_attempts', 3))
        )
        
        db.session.add(quiz)
        db.session.commit()
        
        flash('Quiz created successfully!', 'success')
        return redirect(url_for('content.view_topic', topic_id=topic_id))
    
    return render_template('content/create_quiz.html', topic=topic)

@content_bp.route('/quizzes/<int:quiz_id>/questions/add', methods=['GET', 'POST'])
@login_required
def add_question(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    topic = quiz.topic
    course = topic.course
    
    # Check permissions
    if not current_user.is_admin() and course.instructor_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('content.view_topic', topic_id=topic.id))
    
    if request.method == 'POST':
        data = request.form.to_dict()
        
        # Get next order index
        max_order = db.session.query(db.func.max(QuizQuestion.order_index)).filter_by(quiz_id=quiz_id).scalar() or 0
        
        question = QuizQuestion(
            quiz_id=quiz_id,
            question_text=data.get('question_text'),
            question_type=data.get('question_type'),
            points=int(data.get('points', 1)),
            order_index=max_order + 1
        )
        
        db.session.add(question)
        db.session.flush()  # Get the question ID
        
        # Add options for multiple choice questions
        if question.question_type == 'multiple_choice':
            options_data = request.form.getlist('options[]')
            correct_option = int(data.get('correct_option', 0))
            
            for i, option_text in enumerate(options_data):
                if option_text.strip():
                    option = QuizOption(
                        question_id=question.id,
                        option_text=option_text.strip(),
                        is_correct=(i == correct_option),
                        order_index=i
                    )
                    db.session.add(option)
        
        db.session.commit()
        flash('Question added successfully!', 'success')
        return redirect(url_for('content.view_quiz', quiz_id=quiz_id))
    
    return render_template('content/add_question.html', quiz=quiz)

@content_bp.route('/quizzes/<int:quiz_id>')
@login_required
def view_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    topic = quiz.topic
    course = topic.course
    
    # Check if user has access to this quiz's course
    if not current_user.is_admin() and not current_user.is_teacher():
        enrollment = Enrollment.query.filter_by(
            student_id=current_user.id, 
            course_id=course.id, 
            is_active=True
        ).first()
        if not enrollment:
            flash('Access denied.', 'error')
            return redirect(url_for('content.courses'))
    
    questions = QuizQuestion.query.filter_by(quiz_id=quiz_id, is_active=True).order_by(QuizQuestion.order_index).all()
    
    return render_template('content/view_quiz.html', quiz=quiz, questions=questions)

# Assignment Management Routes
@content_bp.route('/courses/<int:course_id>/assignments/create', methods=['GET', 'POST'])
@login_required
def create_assignment(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Check permissions
    if not current_user.is_admin() and course.instructor_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('content.view_course', course_id=course_id))
    
    if request.method == 'POST':
        data = request.form.to_dict()
        
        assignment = Assignment(
            title=data.get('title'),
            description=data.get('description'),
            course_id=course_id,
            topic_id=int(data.get('topic_id')) if data.get('topic_id') else None,
            assignment_type=data.get('assignment_type'),
            due_date=datetime.strptime(data.get('due_date'), '%Y-%m-%dT%H:%M'),
            max_points=int(data.get('max_points', 100)),
            instructions=data.get('instructions')
        )
        
        # Handle attachment upload
        if 'attachment' in request.files:
            attachment_url = save_file(request.files['attachment'], 'assignments')
            if attachment_url:
                assignment.attachment_url = attachment_url
        
        db.session.add(assignment)
        db.session.commit()
        
        flash('Assignment created successfully!', 'success')
        return redirect(url_for('content.view_course', course_id=course_id))
    
    topics = Topic.query.filter_by(course_id=course_id, is_active=True).all()
    return render_template('content/create_assignment.html', course=course, topics=topics)

# Student Routes
@content_bp.route('/enroll/<int:course_id>', methods=['POST'])
@login_required
def enroll_course(course_id):
    if not current_user.is_student():
        flash('Only students can enroll in courses.', 'error')
        return redirect(url_for('content.courses'))
    
    course = Course.query.get_or_404(course_id)
    
    # Check if already enrolled
    existing_enrollment = Enrollment.query.filter_by(
        student_id=current_user.id, 
        course_id=course_id, 
        is_active=True
    ).first()
    
    if existing_enrollment:
        flash('You are already enrolled in this course.', 'info')
        return redirect(url_for('content.view_course', course_id=course_id))
    
    # Check if course is full
    current_enrollments = Enrollment.query.filter_by(course_id=course_id, is_active=True).count()
    if current_enrollments >= course.max_students:
        flash('This course is full.', 'error')
        return redirect(url_for('content.courses'))
    
    enrollment = Enrollment(
        student_id=current_user.id,
        course_id=course_id
    )
    
    db.session.add(enrollment)
    db.session.commit()
    
    flash(f'Successfully enrolled in {course.title}!', 'success')
    return redirect(url_for('content.view_course', course_id=course_id))

@content_bp.route('/quizzes/<int:quiz_id>/take', methods=['GET', 'POST'])
@login_required
def take_quiz(quiz_id):
    if not current_user.is_student():
        flash('Only students can take quizzes.', 'error')
        return redirect(url_for('content.courses'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    topic = quiz.topic
    course = topic.course
    
    # Check if enrolled
    enrollment = Enrollment.query.filter_by(
        student_id=current_user.id, 
        course_id=course.id, 
        is_active=True
    ).first()
    if not enrollment:
        flash('You must be enrolled in this course to take the quiz.', 'error')
        return redirect(url_for('content.courses'))
    
    # Check attempts
    attempts = QuizAttempt.query.filter_by(
        student_id=current_user.id, 
        quiz_id=quiz_id
    ).count()
    
    if attempts >= quiz.max_attempts:
        flash(f'You have reached the maximum number of attempts ({quiz.max_attempts}) for this quiz.', 'error')
        return redirect(url_for('content.view_quiz', quiz_id=quiz_id))
    
    if request.method == 'POST':
        # Create new attempt
        attempt = QuizAttempt(
            student_id=current_user.id,
            quiz_id=quiz_id,
            attempt_number=attempts + 1
        )
        db.session.add(attempt)
        db.session.flush()
        
        # Process answers
        total_score = 0
        max_score = 0
        
        for question in quiz.questions:
            max_score += question.points
            
            if question.question_type == 'multiple_choice':
                selected_option_id = request.form.get(f'question_{question.id}')
                if selected_option_id:
                    selected_option = QuizOption.query.get(selected_option_id)
                    is_correct = selected_option and selected_option.is_correct
                    points_earned = question.points if is_correct else 0
                    
                    answer = QuizAnswer(
                        attempt_id=attempt.id,
                        question_id=question.id,
                        selected_option_id=selected_option_id,
                        is_correct=is_correct,
                        points_earned=points_earned
                    )
                    db.session.add(answer)
                    total_score += points_earned
        
        # Update attempt
        attempt.score = total_score
        attempt.max_score = max_score
        attempt.percentage = (total_score / max_score * 100) if max_score > 0 else 0
        attempt.passed = attempt.percentage >= quiz.passing_score
        attempt.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Quiz completed! Score: {attempt.percentage:.1f}%', 'success')
        return redirect(url_for('content.view_quiz', quiz_id=quiz_id))
    
    questions = QuizQuestion.query.filter_by(quiz_id=quiz_id, is_active=True).order_by(QuizQuestion.order_index).all()
    return render_template('content/take_quiz.html', quiz=quiz, questions=questions)

# API Routes for AJAX requests
@content_bp.route('/api/courses')
@login_required
def api_courses():
    if current_user.is_admin():
        courses = Course.query.all()
    elif current_user.is_teacher():
        courses = Course.query.filter_by(instructor_id=current_user.id).all()
    else:
        enrollments = Enrollment.query.filter_by(student_id=current_user.id, is_active=True).all()
        courses = [enrollment.course for enrollment in enrollments]
    
    return jsonify([course.to_dict() for course in courses])

@content_bp.route('/api/courses/<int:course_id>/topics')
@login_required
def api_course_topics(course_id):
    topics = Topic.query.filter_by(course_id=course_id, is_active=True).order_by(Topic.order_index).all()
    return jsonify([topic.to_dict() for topic in topics])

@content_bp.route('/api/topics/<int:topic_id>/materials')
@login_required
def api_topic_materials(topic_id):
    materials = LearningMaterial.query.filter_by(topic_id=topic_id, is_active=True).order_by(LearningMaterial.order_index).all()
    return jsonify([material.to_dict() for material in materials]) 