import google.generativeai as genai
import os
from dotenv import load_dotenv

basedir = os.path.dirname(os.path.abspath(__file__))
# Try to look for .env in parent dir as main.py does
parent_dir = os.path.dirname(basedir)
load_dotenv(os.path.join(parent_dir, '.env'))

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    # Try looking in current dir .env
    load_dotenv(os.path.join(basedir, '.env'))
    api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("No API Key found")
else:
    genai.configure(api_key=api_key)
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(m.name)
    except Exception as e:
        print(f"Error listing models: {e}")
