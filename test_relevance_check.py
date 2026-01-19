import os
import logging
from dotenv import load_dotenv
import google.generativeai as genai
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from src.main import analyze_relevance

# Setup
load_dotenv()
logging.basicConfig(level=logging.INFO)
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

# Test Cases
articles = [
    {
        "title": "Startup Brasileira 'AgroTech' levanta R$ 5 milhões em Seed",
        "content": "A startup de tecnologia agrícola AgroTech anunciou hoje uma rodada Seed de 5 milhões liderada pela Crivo Ventures. A empresa foca em pequenos produtores no Brasil...",
        "expected": True
    },
    {
        "title": "Microsoft announces new AI feature for Word",
        "content": "Microsoft today revealed Copilot for Word, a global update available to all users. The feature allows...",
        "expected": False
    },
    {
        "title": "Ambev reports quarterly earnings",
        "content": "Ambev (ABEV3) reported net income of R$ 3bn in the last quarter. The volume of beer sales increased...",
        "expected": False
    }
]

print("--- Starting Relevance Test ---")
for art in articles:
    print(f"\nTesting: {art['title']}")
    is_relevant, reason = analyze_relevance(model, art)
    print(f"Result: {is_relevant}")
    print(f"Reason: {reason}")
    
    if is_relevant == art['expected']:
        print("✅ PASS")
    else:
        print(f"❌ FAIL (Expected {art['expected']})")

print("\n--- Test Complete ---")
