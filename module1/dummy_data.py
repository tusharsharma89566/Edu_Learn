import random
from faker import Faker
from module1 import app
from models import db, User
from content_models import Course, Enrollment, Assignment, AssignmentSubmission
from progress_models import LearningSession

fake = Faker()

def seed_users(n=30):
    roles = ['student', 'teacher', 'admin']
    users = []
    for _ in range(n):
        user = User(
            username=fake.user_name(),
            email=fake.email(),
            role=random.choice(roles),
            password_hash=fake.sha256(),
            is_active=True
        )
        users.append(user)
        db.session.add(user)
    db.session.commit()
    return users

def seed_courses(users, n=5):
    courses = []
    teachers = [u for u in users if u.role == 'teacher']
    for _ in range(n):
        instructor = random.choice(teachers)
        course = Course(
            title=fake.sentence(nb_words=4),
            description=fake.text(max_nb_chars=100),
            instructor_id=instructor.id,
            is_active=True
        )
        db.session.add(course)
        courses.append(course)
    db.session.commit()
    return courses

def seed_enrollments(users, courses):
    students = [u for u in users if u.role == 'student']
    for course in courses:
        selected_students = random.sample(students, k=min(10, len(students)))
        for student in selected_students:
            enrollment = Enrollment(
                course_id=course.id,
                user_id=student.id
            )
            db.session.add(enrollment)
    db.session.commit()

def seed_assignments(courses, n=10):
    assignments = []
    for course in courses:
        for _ in range(n):
            assignment = Assignment(
                title=fake.sentence(nb_words=3),
                description=fake.text(),
                due_date=fake.future_date(),
                course_id=course.id
            )
            db.session.add(assignment)
            assignments.append(assignment)
    db.session.commit()
    return assignments

def run_all():
    with app.app_context():
        users = seed_users()
        courses = seed_courses(users)
        seed_enrollments(users, courses)
        assignments = seed_assignments(courses)

if __name__ == "__main__":
    run_all()
