import os
from openai import OpenAI
from dotenv import load_dotenv

# Load env from parent dir
basedir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(basedir)
load_dotenv(os.path.join(parent_dir, '.env'))

# Also try current dir
load_dotenv(os.path.join(basedir, '.env'))

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("OPENAI_API_KEY not found")
else:
    print(f"Found API Key: {api_key[:5]}...")
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        print(f"API Success: {response.choices[0].message.content}")
    except Exception as e:
        print(f"API Error: {e}")
