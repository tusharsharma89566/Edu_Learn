from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify, session, current_app
import google.generativeai as genai
from flask_login import login_required, current_user
from models import db, User
from chatbot_models import ChatMessage, FAQ, StudyReminder
from datetime import datetime, timedelta
import json

chatbot_bp = Blueprint('chatbot', __name__)

# Rule-based chatbot responses
FAQ_RESPONSES = {
    "course": "You can browse and enroll in courses from the Course section. Each course has detailed materials and assessments.",
    "assessment": "You can take assessments in the Adaptive Assessment section. The system will adjust difficulty based on your performance.",
    "grading": "Your assignments are automatically graded in the Auto Grading section. You can also view feedback from instructors.",
    "progress": "Track your learning progress in the Progress section. You can see detailed analytics of your performance.",
    "recommendation": "The system recommends courses based on your interests and learning history in the Recommendation section.",
    "gamification": "Earn badges and points through the Gamification system as you complete courses and assessments.",
    "help": "I can help you with questions about courses, assessments, progress tracking, and more. What would you like to know?",
    "support": "For technical support, please contact our support team at support@edulearn.com or use the feedback form."
}

STUDY_REMINDERS = {
    "daily": "Don't forget to complete your daily learning goal!",
    "weekly": "Review your weekly progress and set new learning objectives.",
    "assignment": "Your assignment deadline is approaching. Make sure to submit on time!",
    "assessment": "Take some time to review material before your next assessment."
}

@chatbot_bp.route('/chat')
@login_required
def chat():
    """Render the chat interface"""
    # Get recent chat history
    recent_messages = ChatMessage.query.filter_by(user_id=current_user.id)\
        .order_by(ChatMessage.timestamp.desc())\
        .limit(20)\
        .all()
    
    # Get FAQs
    faqs = FAQ.query.filter_by(is_active=True).all()
    
    return render_template('chatbot/chat.html', 
                          user=current_user, 
                          messages=reversed(recent_messages),
                          faqs=faqs)

@chatbot_bp.route('/chat/send', methods=['POST'])
@login_required
def send_message():
    """Process user message and generate response"""
    data = request.get_json()
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({'error': 'Message is required'}), 400
    
    # Save user message
    chat_message = ChatMessage(
        user_id=current_user.id,
        message=user_message,
        message_type='user'
    )
    db.session.add(chat_message)
    db.session.commit()
    
    # Generate bot response
    bot_response = generate_response(user_message)
    
    # Save bot response
    response_message = ChatMessage(
        user_id=current_user.id,
        message=user_message,
        response=bot_response,
        message_type='bot'
    )
    db.session.add(response_message)
    db.session.commit()
    
    return jsonify({
        'user_message': chat_message.to_dict(),
        'bot_response': response_message.to_dict()
    })

@chatbot_bp.route('/chat/reminders')
@login_required
def get_reminders():
    """Get active study reminders for the user"""
    reminders = StudyReminder.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).filter(StudyReminder.reminder_time >= datetime.utcnow()).all()
    
    return jsonify([reminder.to_dict() for reminder in reminders])

@chatbot_bp.route('/chat/reminders/create', methods=['POST'])
@login_required
def create_reminder():
    """Create a new study reminder"""
    data = request.get_json()
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    reminder_time = data.get('reminder_time')
    
    if not title or not reminder_time:
        return jsonify({'error': 'Title and reminder time are required'}), 400
    
    try:
        reminder_datetime = datetime.fromisoformat(reminder_time.replace('Z', '+00:00'))
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    
    reminder = StudyReminder(
        user_id=current_user.id,
        title=title,
        description=description,
        reminder_time=reminder_datetime
    )
    
    db.session.add(reminder)
    db.session.commit()
    
    return jsonify({
        'message': 'Reminder created successfully',
        'reminder': reminder.to_dict()
    })

import google.generativeai as genai

def generate_response(user_message):
    # First, check for rule-based responses
    for keyword, response in FAQ_RESPONSES.items():
        if keyword in user_message.lower():
            return response

    # If no rule-based response, use Gemini
    try:
        # Use the newer gemini-1.5-flash model which is more reliable
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(user_message)
        return response.text
    except Exception as e:
        print(f"Error generating Gemini response: {e}")
        return "I'm sorry, I'm having trouble connecting to my brain right now. Please try again later."


@chatbot_bp.route('/chat/faq')
@login_required
def get_faqs():
    """Get all active FAQs"""
    faqs = FAQ.query.filter_by(is_active=True).all()
    return jsonify([faq.to_dict() for faq in faqs])

# Admin routes for managing FAQs
@chatbot_bp.route('/admin/faqs')
@login_required
def admin_faqs():
    """Admin interface for managing FAQs"""
    if not current_user.is_admin():
        return redirect(url_for('index'))
    
    faqs = FAQ.query.all()
    return render_template('chatbot/admin_faqs.html', user=current_user, faqs=faqs)

@chatbot_bp.route('/admin/faqs/create', methods=['POST'])
@login_required
def create_faq():
    """Create a new FAQ"""
    if not current_user.is_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    question = data.get('question', '').strip()
    answer = data.get('answer', '').strip()
    category = data.get('category', '').strip()
    
    if not question or not answer:
        return jsonify({'error': 'Question and answer are required'}), 400
    
    faq = FAQ(
        question=question,
        answer=answer,
        category=category
    )
    
    db.session.add(faq)
    db.session.commit()
    
    return jsonify({
        'message': 'FAQ created successfully',
        'faq': faq.to_dict()
    })

@chatbot_bp.route('/admin/faqs/<int:faq_id>/update', methods=['POST'])
@login_required
def update_faq(faq_id):
    """Update an existing FAQ"""
    if not current_user.is_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    faq = FAQ.query.get_or_404(faq_id)
    
    data = request.get_json()
    question = data.get('question', '').strip()
    answer = data.get('answer', '').strip()
    category = data.get('category', '').strip()
    is_active = data.get('is_active', faq.is_active)
    
    if question:
        faq.question = question
    if answer:
        faq.answer = answer
    if category is not None:
        faq.category = category
    faq.is_active = is_active
    
    db.session.commit()
    
    return jsonify({
        'message': 'FAQ updated successfully',
        'faq': faq.to_dict()
    })

@chatbot_bp.route('/admin/faqs/<int:faq_id>/delete', methods=['DELETE'])
@login_required
def delete_faq(faq_id):
    """Delete an FAQ"""
    if not current_user.is_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    faq = FAQ.query.get_or_404(faq_id)
    db.session.delete(faq)
    db.session.commit()
    
    return jsonify({'message': 'FAQ deleted successfully'})
