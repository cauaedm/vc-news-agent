import asyncio
import os
import logging
import sys
import google.generativeai as genai
from tavily import TavilyClient
from crawl4ai import AsyncWebCrawler
from datetime import datetime, timedelta
from dateutil import parser
from config import TRUSTED_SOURCES, SEARCH_TOPIC, EMAIL_TO, EMAIL_SUBJECT
from email_service import send_daily_briefing
from dotenv import load_dotenv
import textwrap

# Load environment variables
# Assumes .env is in the parent directory (project root)
basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(basedir, '.env'))

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
    return genai.GenerativeModel('gemini-2.5-flash')

def search_news(client, topic, sources):
    """
    Performs a single search restricted to trusted domains and strict date limits.
    """
    logging.info(f"🔍 Searching for topic: '{topic}' in {len(sources)} sources...")
    
    try:
        response = client.search(
            query=topic,
            topic="news",
            days=2, # Ask Tavily for last 48h
            include_domains=sources,
            max_results=20 # Get a good pool to filter from
        )
        return response.get('results', [])
    except Exception as e:
        logging.error(f"❌ Search failed: {e}")
        return []

def filter_by_date(results):
    """
    Strictly filters articles to only match Today or Yesterday's date.
    Parses 'published_date' from Tavily.
    """
    logging.info(f"🕵️ Filtering {len(results)} articles by date (Today/Yesterday only)...")
    
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    valid_articles = []
    
    for article in results:
        pub_date_str = article.get('published_date')
        title = article.get('title', 'No Title')
        
        if not pub_date_str:
            logging.info(f"   🗑️ Skipped (No Date): {title}")
            continue
            
        try:
            # Robust parsing with dateutil
            article_date = parser.parse(pub_date_str).date()
            
            if article_date == today or article_date == yesterday:
                logging.info(f"   ✅ Keep ({article_date}): {title}")
                valid_articles.append(article)
            else:
                logging.info(f"   🗑️ Skipped (Old: {article_date}): {title}")
                
        except (ValueError, TypeError) as e:
            logging.warning(f"   ⚠️ Date Parse Error ({pub_date_str}): {e}")
            continue

    logging.info(f"✅ Kept {len(valid_articles)} fresh articles.")
    return valid_articles

async def crawl_urls(articles):
    """Crawls valid articles using Crawl4AI."""
    if not articles:
        return []

    urls = [a['url'] for a in articles]
    logging.info(f"🕷️ Crawling {len(urls)} selected URLs...")
    
    crawled_results = []
    async with AsyncWebCrawler(verbose=True) as crawler:
        for article in articles:
            url = article['url']
            try:
                result = await crawler.arun(url=url)
                if result.success:
                    # Limit content size for LLM context
                    content_snippet = result.markdown[:6000] 
                    # Merge crawl content with metadata
                    article['content'] = content_snippet
                    crawled_results.append(article)
                    logging.info(f"   ✅ Crawled: {url}")
                else:
                    logging.error(f"   ❌ Failed to crawl {url}: {result.error_message}")
            except Exception as e:
                logging.error(f"   ⚠️ Error processing {url}: {e}")
    return crawled_results

def generate_newsletter(model, articles):
    """
    Summarizes the crawled content.
    """
    logging.info("✍️ Write Agent: Generating newsletter...")
    
    if not articles:
        return "⚠️ No fresh news found today."

    articles_text = ""
    for i, article in enumerate(articles):
        # We trust the date pre-filter, but provide context just in case
        articles_text += f"\n\n--- Article {i+1} ---\nTitle: {article['title']}\nDate: {article.get('published_date')}\nURL: {article['url']}\nContent: {article.get('content', '')[:3000]}"

    today_str = datetime.now().strftime("%Y-%m-%d")

    prompt = f"""
    Act as a senior VC analyst for the Brazilian market.
    **TODAY'S DATE:** {today_str}

    Analyze the following **FRESH** articles and write a Weekly Daily Briefing.
    
    **Instructions:**
    - These articles have already been filtered for date. Assume they are relevant.
    - If an article turns out to be irrelevant (ads, privacy policies), ignore it.
    
    **Format constraints:**
    - Use Markdown.
    - Group by Deal/Startup.
    - Extract: Founders, VCs, Valuation (if available).
    
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
        return "⚠️ Error generating summary."

async def run_pipeline(dry_run=False):
    logging.info(f"🚀 Starting Simplified VC News Pipeline {'[DRY RUN]' if dry_run else ''}")
    
    # Setup
    model = configure_gemini()
    tavily_key = os.getenv("TAVILY_API_KEY")
    
    if not tavily_key and not dry_run:
         logging.error("TAVILY_API_KEY missing.")
         return

    # 1. Search (Single Call)
    if dry_run:
        logging.info("🔍 [DRY RUN] Mocking Search.")
        # Mocking 1 fresh and 1 old article
        today_str = datetime.now().strftime("%Y-%m-%d")
        old_str = "2023-01-01"
        raw_results = [
            {"title": "Fresh Startup Raise", "url": "http://mock.com/fresh", "published_date": today_str},
            {"title": "Old Startup News", "url": "http://mock.com/old", "published_date": old_str}
        ]
    else:
        tavily = TavilyClient(api_key=tavily_key)
        raw_results = search_news(tavily, SEARCH_TOPIC, TRUSTED_SOURCES)

    if not raw_results:
        logging.warning("❌ No results found from Tavily.")
        return

    # 2. Strict Date Filter
    valid_articles = filter_by_date(raw_results)
    
    if not valid_articles:
        logging.warning("❌ No articles matched the date criteria (Today/Yesterday).")
        # In production, we might want to send a "No News" email, or just exit.
        # For now, let's exit but log loudly.
        return

    # 3. Crawl
    if dry_run:
        logging.info("🕷️ [DRY RUN] Mocking Crawl.")
        crawled_data = valid_articles
        for a in crawled_data:
            a['content'] = "Mock content about a $5M seed round."
    else:
        crawled_data = await crawl_urls(valid_articles)

    # 4. Write
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
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--dry-run", action="store_true")
    args = arg_parser.parse_args()
    asyncio.run(run_pipeline(args.dry_run))
