from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from models import db, User
import re

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    """Simple email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Password validation - at least 8 characters, 1 uppercase, 1 lowercase, 1 number"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Valid password"

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Handle both form data and JSON
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        role = data.get('role', 'student')
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        
        # Validation
        if not username or len(username) < 3:
            error = "Username must be at least 3 characters long"
            if request.is_json:
                return jsonify({'error': error}), 400
            flash(error, 'error')
            return render_template('register.html')
        
        if not validate_email(email):
            error = "Please enter a valid email address"
            if request.is_json:
                return jsonify({'error': error}), 400
            flash(error, 'error')
            return render_template('register.html')
        
        is_valid_password, password_message = validate_password(password)
        if not is_valid_password:
            if request.is_json:
                return jsonify({'error': password_message}), 400
            flash(password_message, 'error')
            return render_template('register.html')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            error = "Username already exists"
            if request.is_json:
                return jsonify({'error': error}), 400
            flash(error, 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            error = "Email already registered"
            if request.is_json:
                return jsonify({'error': error}), 400
            flash(error, 'error')
            return render_template('register.html')
        
        # Validate role
        if role not in ['student', 'teacher', 'admin']:
            role = 'student'
        
        # Create new user
        try:
            user = User(
                username=username,
                email=email,
                role=role,
                first_name=first_name,
                last_name=last_name
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            if request.is_json:
                return jsonify({
                    'message': 'Registration successful',
                    'user': user.to_dict()
                }), 201
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            error = "Registration failed. Please try again."
            if request.is_json:
                return jsonify({'error': error}), 500
            flash(error, 'error')
            return render_template('register.html')
    
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Handle both form data and JSON
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        remember_me = data.get('remember_me', False)
        
        if not email or not password:
            error = "Please enter both email and password"
            if request.is_json:
                return jsonify({'error': error}), 400
            flash(error, 'error')
            return render_template('login.html')
        
        # Find user by email
        user = User.query.filter_by(email=email.lower()).first()
        
        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=remember_me)
            user.update_last_login()
            
            if request.is_json:
                return jsonify({
                    'message': 'Login successful',
                    'user': user.to_dict()
                }), 200
            
            # Redirect based on role
            next_page = request.args.get('next')
            if not next_page:
                if user.is_admin():
                    next_page = url_for('admin_dashboard')
                elif user.is_teacher():
                    next_page = url_for('teacher_dashboard')
                else:
                    next_page = url_for('student_dashboard')
            
            return redirect(next_page)
        else:
            error = "Invalid credentials or account inactive"
            if request.is_json:
                return jsonify({'error': error}), 401
            flash(error, 'error')
            return render_template('login.html')
    
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    if request.is_json:
        return jsonify({'message': 'Logged out successfully'}), 200
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Handle both form data and JSON
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        bio = data.get('bio', '').strip()
        
        try:
            current_user.first_name = first_name
            current_user.last_name = last_name
            current_user.bio = bio
            
            db.session.commit()
            
            if request.is_json:
                return jsonify({
                    'message': 'Profile updated successfully',
                    'user': current_user.to_dict()
                }), 200
            
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('auth.profile'))
            
        except Exception as e:
            db.session.rollback()
            error = "Failed to update profile"
            if request.is_json:
                return jsonify({'error': error}), 500
            flash(error, 'error')
    
    if request.is_json:
        return jsonify({'user': current_user.to_dict()}), 200
    
    return render_template('profile.html', user=current_user)

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    # Handle both form data and JSON
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()
    
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')
    
    if not current_user.check_password(current_password):
        error = "Current password is incorrect"
        if request.is_json:
            return jsonify({'error': error}), 400
        flash(error, 'error')
        return redirect(url_for('auth.profile'))
    
    if new_password != confirm_password:
        error = "New passwords do not match"
        if request.is_json:
            return jsonify({'error': error}), 400
        flash(error, 'error')
        return redirect(url_for('auth.profile'))
    
    is_valid, message = validate_password(new_password)
    if not is_valid:
        if request.is_json:
            return jsonify({'error': message}), 400
        flash(message, 'error')
        return redirect(url_for('auth.profile'))
    
    try:
        current_user.set_password(new_password)
        db.session.commit()
        
        if request.is_json:
            return jsonify({'message': 'Password changed successfully'}), 200
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('auth.profile'))
        
    except Exception as e:
        db.session.rollback()
        error = "Failed to change password"
        if request.is_json:
            return jsonify({'error': error}), 500
        flash(error, 'error')
        return redirect(url_for('auth.profile'))
