from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, login_required, current_user
from config import Config
from models import db, User
from auth import auth_bp
from content_routes import content_bp
from progress_routes import progress_bp
from recommendation_routes import recommendation_bp
from adaptive_assessment_routes import adaptive_bp
from auto_grading_routes import auto_grading_bp
from gamification_routes import gamification_bp
from chatbot_routes import chatbot_bp
from admin_routes import admin_bp
from analytics_routes import analytics_bp
from moderation_routes import moderation_bp

def create_app():
    app = Flask(__name__, template_folder='templates')
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    
    # Configure Gemini API
    import google.generativeai as genai
    try:
        genai.configure(api_key=app.config['GEMINI_API_KEY'])
        print("Gemini API configured successfully")
    except Exception as e:
        print(f"Error configuring Gemini API: {e}")
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(content_bp, url_prefix='/content')
    app.register_blueprint(progress_bp, url_prefix='/progress')
    app.register_blueprint(recommendation_bp, url_prefix='/recommendation')
    app.register_blueprint(adaptive_bp, url_prefix='/adaptive')
    app.register_blueprint(auto_grading_bp, url_prefix='/auto_grading')
    app.register_blueprint(gamification_bp, url_prefix='/gamification')
    app.register_blueprint(chatbot_bp, url_prefix='/chatbot')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(analytics_bp, url_prefix='/admin')
    app.register_blueprint(moderation_bp, url_prefix='/admin')
    
    # Main routes
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.is_admin():
                return redirect(url_for('admin_dashboard'))
            elif current_user.is_teacher():
                return redirect(url_for('teacher_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        return redirect(url_for('auth.login'))
    
    # Dashboard routes with real data
    @app.route('/student-dashboard')
    @login_required
    def student_dashboard():
        if not current_user.is_student():
            return redirect(url_for('index'))
        
        # Import content models for data
        from content_models import Enrollment, Course
        
        # Get student statistics
        enrolled_courses = Enrollment.query.filter_by(student_id=current_user.id, is_active=True).all()
        total_courses = len(enrolled_courses)
        
        # Calculate progress for each enrollment
        for enrollment in enrolled_courses:
            if enrollment.course:
                topics_count = enrollment.course.topics.count()
                if topics_count > 0:
                    # Simple progress calculation (can be enhanced)
                    enrollment.progress_percentage = min(100, int((topics_count / 10) * 100))
                else:
                    enrollment.progress_percentage = 0
        
        stats = {
            'enrolled_courses': total_courses,
            'pending_assignments': 0,  # Can be enhanced with assignment data
            'average_grade': 0,  # Can be enhanced with grade data
            'study_hours': 0,  # Can be enhanced with tracking
            'course_completion': sum(e.progress_percentage for e in enrolled_courses) // max(total_courses, 1),
            'assignment_submission': 90  # Placeholder
        }
        
        return render_template('student_dashboard.html', 
                             user=current_user, 
                             stats=stats, 
                             enrolled_courses=enrolled_courses)
    
    @app.route('/teacher-dashboard')
    @login_required
    def teacher_dashboard():
        if not current_user.is_teacher():
            return redirect(url_for('index'))
        
        # Import content models for data
        from content_models import Course, Enrollment
        
        # Get teacher's courses
        courses = Course.query.filter_by(instructor_id=current_user.id, is_active=True).all()
        
        # Calculate statistics
        total_students = sum(course.enrollments.count() for course in courses)
        total_courses = len(courses)
        
        stats = {
            'total_courses': total_courses,
            'total_students': total_students,
            'pending_reviews': 0,  # Can be enhanced with assignment data
            'avg_performance': 85  # Placeholder
        }
        
        return render_template('teacher_dashboard.html', 
                             user=current_user, 
                             stats=stats, 
                             courses=courses)
    
    @app.route('/admin-dashboard')
    @login_required
    def admin_dashboard():
        if not current_user.is_admin():
            return redirect(url_for('index'))
        
        # Get system statistics
        total_users = User.query.count()
        total_teachers = User.query.filter_by(role='teacher').count()
        total_students = User.query.filter_by(role='student').count()
        total_admins = User.query.filter_by(role='admin').count()
        
        # Import content models for course data
        from content_models import Course
        total_courses = Course.query.filter_by(is_active=True).count()
        
        # Calculate percentages
        total_active_users = total_teachers + total_students + total_admins
        students_percentage = round((total_students / max(total_active_users, 1)) * 100)
        teachers_percentage = round((total_teachers / max(total_active_users, 1)) * 100)
        admins_percentage = round((total_admins / max(total_active_users, 1)) * 100)
        
        stats = {
            'total_users': total_users,
            'total_teachers': total_teachers,
            'total_students': total_students,
            'total_admins': total_admins,
            'total_courses': total_courses,
            'students_percentage': students_percentage,
            'teachers_percentage': teachers_percentage,
            'admins_percentage': admins_percentage
        }
        
        return render_template('admin_dashboard.html', 
                             user=current_user, 
                             stats=stats)
    
    # Progress tracking routes
    @app.route('/progress/dashboard')
    @login_required
    def progress_dashboard():
        """Progress tracking dashboard page"""
        return render_template('progress/dashboard.html', user=current_user)
    
    @app.route('/progress/tracking')
    @login_required
    def progress_tracking():
        """Real-time progress tracking page"""
        return render_template('progress/tracking.html', user=current_user)
    
    # Create database tables
    with app.app_context():
        # Import content models to register them with the database
        from content_models import Course, Topic, LearningMaterial, Video, Quiz, QuizQuestion, QuizOption, Assignment, Enrollment, QuizAttempt, QuizAnswer, AssignmentSubmission
        
        # Import progress tracking models to register them with the database
        from progress_models import LearningSession, LearningActivity, CourseProgress, TopicProgress, LearningAnalytics, StudyStreak
        
        # Import recommendation models to register them with the database
        from recommendation_models import UserPreference, LearningPattern, UserRecommendation, LearningCluster, ContentSimilarity
        
        # Import adaptive assessment models to register them with the database
        from adaptive_assessment_models import AdaptiveQuestion, AdaptiveAssessment, AssessmentResponse, AssessmentAnalytics
        
        # Import auto-grading models to register them with the database
        from auto_grading_models import AutoGradingModel, GradingCriteria, AutoGradingResult, HumanReview, GradingAnalytics
        
        # Import gamification models to register them with the database
        from gamification_models import Badge, UserBadge, UserPoints, Leaderboard, LeaderboardEntry, Achievement, Notification
        
        # Import chatbot models to register them with the database
        from chatbot_models import ChatMessage, FAQ, StudyReminder
        
        db.create_all()
        
        # Create default admin user if none exists
        if not User.query.filter_by(role='admin').first():
            admin = User(
                username='admin',
                email='admin@example.com',
                role='admin',
                first_name='System',
                last_name='Administrator'
            )
            admin.set_password('Admin123!')
            db.session.add(admin)
            db.session.commit()
            print("Default admin created: admin@example.com / Admin123!")
        
        # Create default FAQs
        if not FAQ.query.first():
            default_faqs = [
                {
                    "question": "How do I enroll in a course?",
                    "answer": "You can browse available courses in the Course section and click 'Enroll' on any course you're interested in. You'll be automatically enrolled and can start learning immediately.",
                    "category": "Courses"
                },
                {
                    "question": "How do I track my progress?",
                    "answer": "Visit the Progress section to see detailed analytics of your learning journey, including completion rates, grades, and time spent on different topics.",
                    "category": "Progress"
                },
                {
                    "question": "How do I get help with assignments?",
                    "answer": "You can ask questions about assignments in the Chat Support section, or contact your instructor directly through the messaging system.",
                    "category": "Assignments"
                }
            ]
            
            for faq_data in default_faqs:
                faq = FAQ(
                    question=faq_data["question"],
                    answer=faq_data["answer"],
                    category=faq_data["category"]
                )
                db.session.add(faq)
            
            db.session.commit()
            print("Default FAQs created")
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
