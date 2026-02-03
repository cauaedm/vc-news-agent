import sys
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# Setup basic logging
logging.basicConfig(level=logging.INFO)
sys.stdout.reconfigure(encoding='utf-8')

# Load env variables (similar to main.py logic)
basedir = os.path.dirname(os.path.abspath(__file__))
# Try parent dir
parent_dir = os.path.dirname(basedir)
load_dotenv(os.path.join(parent_dir, '.env'))
# Try current dir
load_dotenv(os.path.join(basedir, '.env'))

# Ensure OpenAI API key is present
configure_openai = lambda: OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Mock generate_newsletter function (copy-pasted for isolation or imported if possible)
# I will import it to test the ACTUAL code
sys.path.append(os.path.join(basedir, 'src'))

try:
    from src.main import generate_newsletter, configure_openai
except ImportError:
    # If src is not a package or path issue, try manual import workaround
    sys.path.append(basedir) 
    from src.main import generate_newsletter, configure_openai

def test_summarization():
    print("Starting Summarization Test...")
    
    # 1. Configure OpenAI
    try:
        client = configure_openai()
        print("Client configured.")
    except Exception as e:
        print(f"Failed to configure client: {e}")
        return

    # 2. Mock Data
    mock_articles = [
        {
            "title": "Startup X Raises $10M Series A",
            "url": "https://example.com/startup-x",
            "published_date": datetime.now().strftime("%Y-%m-%d"),
            "content": "Startup X, a Brazilian fintech, has raised $10 million in a Series A round led by Valor Capital. The company plans to expand its credit operations."
        }
    ]

    # 3. Run Generation
    print("Calling generate_newsletter...")
    try:
        summary = generate_newsletter(client, mock_articles)
        print("\n--- GENERATED SUMMARY ---\n")
        # Print first 500 chars to verify
        print(summary.encode('utf-8', errors='ignore').decode('utf-8')) 
        print("\n-------------------------")
        if "Valor Capital" in summary or "Startup X" in summary:
            print("SUCCESS: Summary contains expected keywords.")
        else:
            print("WARNING: Summary might be generic.")
            
    except Exception as e:
        print(f"ERROR during generation: {e}")

if __name__ == "__main__":
    test_summarization()
