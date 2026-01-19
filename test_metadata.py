import os
import sys
import logging
from dotenv import load_dotenv
from tavily import TavilyClient

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from config import TRUSTED_SOURCES, SEARCH_TOPIC

# Setup
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(message)s')

def test_source_metadata():
    tavily_key = os.getenv("TAVILY_API_KEY")
    if not tavily_key:
        print("❌ TAVILY_API_KEY not found.")
        return

    client = TavilyClient(api_key=tavily_key)
    
    print(f"🔎 Testing Metadata for {len(TRUSTED_SOURCES)} sources...")
    print(f"🔎 Topic: {SEARCH_TOPIC}\n")

    for source in TRUSTED_SOURCES:
        print(f"--- Testing Source: {source} ---")
        try:
            response = client.search(
                query=SEARCH_TOPIC,
                topic="news",
                days=5, # Look back 5 days to ensure we get SOMETHING
                include_domains=[source],
                max_results=3
            )
            
            results = response.get('results', [])
            if not results:
                print(f"   ⚠️ No results found for {source}")
                continue

            for i, article in enumerate(results):
                date = article.get('published_date')
                title = article.get('title')
                url = article.get('url')
                
                status = "✅ Has Date" if date else "❌ NO DATE"
                print(f"   [{i+1}] {status}: {date} | {title[:50]}... ({url})")
                
                # Print FULL metadata for the first item only
                if i == 0:
                    import json
                    print(f"   🔎 FULL RAW DATA (First Item):\n{json.dumps(article, indent=2, ensure_ascii=False)}\n")

        except Exception as e:
            print(f"   ❌ Error searching {source}: {e}")
        print("")

if __name__ == "__main__":
    test_source_metadata()
