import asyncio
import os
import json
import logging
import sys
import google.generativeai as genai
from tavily import TavilyClient
from crawl4ai import AsyncWebCrawler
from datetime import datetime
from config import TRUSTED_SOURCES, SEARCH_TOPIC, EMAIL_TO, EMAIL_SUBJECT
from email_service import send_daily_briefing
from dotenv import load_dotenv
import textwrap

# Load environment variables
load_dotenv()

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("output.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def configure_gemini():
    """Configures the Gemini API."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logging.error("GEMINI_API_KEY not found in environment variables.")
        sys.exit(1)
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemma-3-12b-it')

def search_per_source(client, topic, sources, days=1):
    """
    Searches for the topic in each trusted source individually to ensure variety.
    Returns a list of candidate articles.
    """
    candidates = []
    logging.info(f"🔍 Starting Per-Source Search for topic: '{topic}'")

    for source in sources:
        try:
            # Construct a site-specific query
            query = f"site:{source} {topic}"
            logging.info(f"   👉 Searching in: {source}...")
            
            response = client.search(
                query=query,
                topic="news",
                days=days,
                max_results=5  # Get top 5 per source
            )
            
            for result in response.get('results', []):
                # Add source metadata to help the filter agent
                result['source_domain'] = source
                candidates.append(result)
                
        except Exception as e:
            logging.warning(f"⚠️ Error searching {source}: {e}")
            continue

    logging.info(f"✅ Aggregated {len(candidates)} candidate articles from {len(sources)} sources.")
    return candidates

def filter_candidates(model, candidates):
    """
    Agent 1: The Editor.
    Uses Gemini to select the top 5 distinct stories based on title and snippet.
    """
    logging.info("🕵️ Agent 1 (Editor): Filtering top 5 candidates...")
    
    # Prepare the list for the LLM
    candidates_list_str = ""
    for i, c in enumerate(candidates):
        candidates_list_str += f"ID {i}: Title: {c['title']} | Source: {c['source_domain']} | Snippet: {c['content']} | URL: {c['url']}\n\n"

    prompt = f"""
    You are a Senior Venture Capital Editor specializing in the Brazilian market.
    Your task is to select the **5 most important and distinct** news stories from the list below.

    **Selection Criteria:**
    1.  **Relevance**: Must be about **New Investments (Seed/Pre-Seed)**, **New Startups**, or **M&A** in Brazil/LatAm.
    2.  **Variety**: Prioritize selecting stories from **different sources**. Do not pick multiple stories about the exact same deal unless it adds significant new info.
    3.  **Freshness**: Ensure they look like recent news.

    **Candidates:**
    {candidates_list_str}

    **Output Format:**
    Return ONLY a raw JSON array of integers representing the IDs of the selected articles.
    Example: [0, 5, 12, 18, 22]
    """

    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        selected_ids = json.loads(response.text)
        
        # Validate selection
        if not isinstance(selected_ids, list):
            raise ValueError("Output is not a list")
            
        selected_articles = [candidates[i] for i in selected_ids if 0 <= i < len(candidates)]
        logging.info(f"✅ Editor selected {len(selected_articles)} articles.")
        return selected_articles

    except Exception as e:
        logging.error(f"❌ Filtering Agent failed: {e}")
        # Fallback: Just return the first 5 unique URLs
        logging.info("⚠️ Fallback: Selecting first 5 unique articles.")
        seen_urls = set()
        selected = []
        for c in candidates:
            if c['url'] not in seen_urls:
                selected.append(c)
                seen_urls.add(c['url'])
            if len(selected) >= 5:
                break
        return selected

async def crawl_urls(urls):
    """Crawls specific URLs using Crawl4AI."""
    logging.info(f"🕷️ Crawling {len(urls)} selected URLs...")
    results = []
    async with AsyncWebCrawler(verbose=True) as crawler:
        for url in urls:
            try:
                result = await crawler.arun(url=url)
                if result.success:
                    # Limit content size for LLM context
                    content_snippet = result.markdown[:6000] 
                    results.append({"url": url, "content": content_snippet})
                    logging.info(f"   ✅ Crawled: {url}")
                else:
                    logging.error(f"   ❌ Failed to crawl {url}: {result.error_message}")
            except Exception as e:
                logging.error(f"   ⚠️ Error processing {url}: {e}")
    return results

def generate_newsletter(model, articles):
    """
    Agent 2: The Reporter.
    Summarizes the crawled content into a structured newsletter.
    """
    logging.info("✍️ Agent 2 (Reporter): Generating newsletter...")
    
    articles_text = ""
    for i, article in enumerate(articles):
        articles_text += f"\n\n--- Article {i+1} ({article['url']}) ---\n{article['content']}"

    prompt = f"""
    Act as a senior VC analyst for the Brazilian market.
    Analyze the following articles and write a Weekly Daily Briefing.

    **Format constraints:**
    - Use Markdown.
    - Group by Deal/Startup.
    - Extract: Founders, VCs, Valuation (if available).
    - If a story is not about a deal (e.g. general market analysis), summarize the key insight.
    
    **Output Style:**
    ### 🇧🇷 [Startup Name] - [Round Type / News Type]
    - **The Deal:** 1-line summary.
    - **Business:** What they do.
    - **Founders:** Names.
    - **Investors:** VC funds involved.
    - **Valuation:** Value or "Not disclosed".
    - **Why it matters:** 1 sentence analysis.
    - [Read Source](URL)

    ARTICLES:
    {articles_text}
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logging.error(f"❌ Writer Agent failed: {e}")
        return "⚠️ Error generating summary. See raw links below."

async def run_pipeline(dry_run=False):
    logging.info(f"🚀 Starting Agentic VC News Pipeline {'[DRY RUN]' if dry_run else ''}")
    
    # Setup
    model = configure_gemini()
    tavily_key = os.getenv("TAVILY_API_KEY")
    if not tavily_key and not dry_run:
         logging.error("TAVILY_API_KEY missing.")
         return

    # 1. Search (Per Source)
    if dry_run:
        logging.info("🔍 [DRY RUN] Skipping Search.")
        candidates = [
            {"title": "Startup A Raises Seed", "url": "http://mock.com/a", "content": "Startup A receives $2M", "source_domain": "mock.com"},
            {"title": "Startup B Pre-Seed", "url": "http://mock.com/b", "content": "Startup B launched", "source_domain": "mock.com"},
            # Add more mocks to test filter if needed
        ]
    else:
        tavily = TavilyClient(api_key=tavily_key)
        candidates = search_per_source(tavily, SEARCH_TOPIC, TRUSTED_SOURCES)

    if not candidates:
        logging.warning("❌ No candidates found.")
        return

    # 2. Filter (Agent 1)
    if dry_run:
        logging.info("🕵️ [DRY RUN] Skipping Filter.")
        selected_candidates = candidates[:2]
    else:
        selected_candidates = filter_candidates(model, candidates)

    if not selected_candidates:
        logging.warning("❌ No candidates selected by Editor.")
        return

    # 3. Crawl
    urls_to_crawl = [c['url'] for c in selected_candidates]
    if dry_run:
        logging.info("🕷️ [DRY RUN] Skipping Crawl.")
        crawled_data = [{"url": u, "content": "Mock content for summary."} for u in urls_to_crawl]
    else:
        crawled_data = await crawl_urls(urls_to_crawl)

    # 4. Write (Agent 2)
    if dry_run:
        newsletter_md = textwrap.dedent("""
            ### 🇧🇷 [MOCK] Startup A - Seed
            - **The Deal:** Raises $2M.
            - **Business:** Something AI.
            - [Read Source](http://mock.com/a)
        """)
    else:
        newsletter_md = generate_newsletter(model, crawled_data)

    # 5. Send
    logging.info("📧 Sending Email...")
    if send_daily_briefing(newsletter_md, EMAIL_TO):
        logging.info("🎉 Success!")
    else:
        logging.error("❌ Email failed.")
        if not dry_run:
            sys.exit(1)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(run_pipeline(args.dry_run))
