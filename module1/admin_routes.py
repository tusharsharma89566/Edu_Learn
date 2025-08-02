from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required
from models import db, User
from werkzeug.security import generate_password_hash
import csv
import io

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/bulk-upload', methods=['GET', 'POST'])
@login_required
def bulk_upload():
    """Handle bulk user upload"""
    # This would be protected by role check in a real implementation
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if file and file.filename.endswith('.csv'):
            try:
                # Read CSV file
                stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
                csv_input = csv.reader(stream)
                
                # Skip header row
                next(csv_input, None)
                
                created_users = 0
                for row in csv_input:
                    if len(row) >= 3:  # username, email, role
                        username = row[0].strip()
                        email = row[1].strip().lower()
                        role = row[2].strip().lower()
                        
                        # Optional fields
                        first_name = row[3].strip() if len(row) > 3 else ''
                        last_name = row[4].strip() if len(row) > 4 else ''
                        
                        # Validate role
                        if role not in ['student', 'teacher', 'admin']:
                            role = 'student'
                        
                        # Check if user already exists
                        if User.query.filter_by(email=email).first():
                            continue
                            
                        # Create user with default password
                        user = User(
                            username=username,
                            email=email,
                            role=role,
                            first_name=first_name,
                            last_name=last_name
                        )
                        user.set_password('Password123!')  # Default password, should be changed by user
                        
                        db.session.add(user)
                        created_users += 1
                
                db.session.commit()
                flash(f'Successfully created {created_users} users', 'success')
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error processing file: {str(e)}', 'error')
        else:
            flash('Please upload a CSV file', 'error')
    
    return render_template('admin/bulk_upload.html')
