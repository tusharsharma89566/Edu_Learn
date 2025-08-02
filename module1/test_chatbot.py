import os
import sys
import google.generativeai as genai
from config import Config

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the generate_response function from chatbot_routes
from chatbot_routes import generate_response

# Load config
config = Config()

# Configure Gemini API
genai.configure(api_key=config.GEMINI_API_KEY)

# Test the chatbot response generation
try:
    test_message = "Hello, how can you help me with my studies?"
    response = generate_response(test_message)
    print("Chatbot response test successful!")
    print("Test message:", test_message)
    print("Response:", response)
except Exception as e:
    print("Error testing chatbot response:", str(e))
