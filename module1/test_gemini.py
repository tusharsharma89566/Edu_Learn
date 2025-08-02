import os
import google.generativeai as genai
from config import Config

# Load config
config = Config()

# Configure Gemini API
genai.configure(api_key=config.GEMINI_API_KEY)

# List available models
try:
    print("Available models:")
    for model in genai.list_models():
        print(f"  - {model.name}")
except Exception as e:
    print("Error listing models:", str(e))

# Test the API with a valid model
try:
    # Try different model names
    model_names = ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro', 'models/gemini-1.5-pro', 'models/gemini-1.5-flash']
    model = None
    response = None
    
    for model_name in model_names:
        try:
            print(f"Trying model: {model_name}")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Hello, how are you?")
            print(f"Successfully connected with model: {model_name}")
            break
        except Exception as e:
            print(f"Failed with model {model_name}: {str(e)}")
            continue
    
    if response:
        print("Gemini API is working correctly!")
        print("Response:", response.text)
    else:
        print("Could not connect to any Gemini model")
except Exception as e:
    print("Error connecting to Gemini API:", str(e))
