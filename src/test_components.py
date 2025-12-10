# src/test_components.py
import os
import google.generativeai as genai
from tavily import TavilyClient
import resend
from dotenv import load_dotenv

load_dotenv()

def test_tavily():
    print("\n🔍 Testing Tavily API...")
    try:
        tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
        response = tavily.search(query="Test", max_results=1)
        if response.get('results'):
             print("✅ Tavily OK! Found:", response['results'][0]['title'])
        else:
             print("⚠️ Tavily returned no results (but no error).")
    except Exception as e:
        print(f"❌ Tavily Error: {e}")

def test_gemini():
    print("\n🧠 Testing Gemini API...")
    try:
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content("Say 'Hello' if you are working.")
        print(f"✅ Gemini OK! Response: {response.text}")
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        # Log error to file for inspection
        with open("gemini_error.txt", "w", encoding="utf-8") as f:
            f.write(str(e))

def test_resend_config():
    print("\n📧 Testing Resend Configuration...")
    # Just checking if key exists, not sending to save quota/avoid spam
    key = os.environ.get("RESEND_API_KEY")
    if key and key.startswith("re_"):
        print("✅ Resend Key format looks correct.")
    else:
        print("❌ Resend Key missing or invalid format.")

if __name__ == "__main__":
    print("🚀 Starting Component Tests...")
    test_tavily()
    test_gemini()
    test_resend_config()
