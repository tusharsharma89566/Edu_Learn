# Edu Learn - Educational Platform

## Overview
Edu Learn is a comprehensive educational platform built with Flask that provides features for students, teachers, and administrators. The platform includes:

- User authentication and role-based access control
- Course management system
- Progress tracking and analytics
- Adaptive assessments
- Auto-grading capabilities
- Gamification elements
- AI-powered chatbot support
- Content recommendation system

## Features
- **Student Dashboard**: Personalized learning experience with progress tracking
- **Teacher Dashboard**: Course management and student performance monitoring
- **Admin Dashboard**: System-wide analytics and user management
- **Adaptive Assessments**: Personalized quizzes that adjust to student performance
- **Auto-Grading**: Automated grading for assignments and quizzes
- **Gamification**: Badges, points, and leaderboards to encourage learning
- **Chatbot Support**: AI-powered assistance for students
- **Content Recommendations**: Personalized course recommendations based on learning patterns

## Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

## Local Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/tusharsharma89566/Edu_Learn.git
   cd Edu_Learn
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r module1/requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the `module1` directory with the following variables:
   ```
   SECRET_KEY=your_secret_key_here
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

5. Run the application:
   ```bash
   python module1/app.py
   ```

6. Visit `http://localhost:5000` in your browser

## Deployment on Render (Recommended)

1. Fork this repository to your GitHub account
2. Sign up for a Render account at https://render.com
3. Click "New Web Service"
4. Connect your GitHub account and select this repository
5. Configure the service with the following settings:
   - **Name**: Edu-Learn (or any name you prefer)
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r module1/requirements.txt`
   - **Start Command**: `gunicorn --chdir module1 app:app`
   - **Environment Variables**:
     - `SECRET_KEY`: your_secret_key_here
     - `GEMINI_API_KEY`: your_gemini_api_key_here (optional)

6. Click "Create Web Service"

Note: The SQLite database will not persist with this setup. For production use, consider using a PostgreSQL database.

## Database Migration
To migrate the database to a PostgreSQL database for production:

1. Update the `config.py` file to use PostgreSQL:
   ```python
   SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://user:password@localhost/dbname'
   ```

2. Set the `DATABASE_URL` environment variable on Render

## Contributing
Contributions are welcome! Please fork the repository and create a pull request with your changes.

## License
This project is licensed under the MIT License.
