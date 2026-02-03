import asyncio
import os
import logging
import sys
import google.generativeai as genai
from crawl4ai import AsyncWebCrawler
from datetime import datetime, timedelta
from dateutil import parser
from config import TRUSTED_SOURCES, SEARCH_TOPIC, EMAIL_TO, EMAIL_SUBJECT
from email_service import send_daily_briefing
from dotenv import load_dotenv
import textwrap

# Import Scrapers
from scrape_startups import scrape_startups
from scrape_neofeed import scrape_neofeed
from scrape_pegn import scrape_pegn
from scrape_braziljournal import scrape_braziljournal

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
    return genai.GenerativeModel('gemma-3-12b')

def parse_relative_date(date_str):
    """
    Parses various date formats including relative ones (PT-BR).
    Returns datetime.date or None.
    """
    if not date_str:
        return None
        
    today = datetime.now().date()
    date_str = date_str.lower().strip()
    
    try:
        if date_str == "hoje":
            return today
        if date_str == "ontem":
            return today - timedelta(days=1)
        
        # "Há X horas" / "Há X minutos" -> Today
        if "hora" in date_str or "minuto" in date_str:
             return today
             
        # "Há X dias" -> Today - X
        if "dia" in date_str and "há" in date_str:
            parts = date_str.split()
            # find the number, usually second word "Há 2 dias"
            for p in parts:
                if p.isdigit():
                    return today - timedelta(days=int(p))
                    
        # DD/MM/YY or DD/MM/YYYY
        return parser.parse(date_str, dayfirst=True).date()
        
    except Exception as e:
        logging.debug(f"Date parse error '{date_str}': {e}")
        return None

async def gather_news_from_scrapers():
    """
    Runs all scrapers in parallel and normalizes data.
    """
    logging.info("🕷️ Running all scrapers in parallel...")
    
    # Run all async
    results = await asyncio.gather(
        scrape_startups(),
        scrape_neofeed(),
        scrape_pegn(),
        scrape_braziljournal(),
        return_exceptions=True
    )
    
    all_articles = []
    
    # Process results
    sources = ["Startups.com.br", "NeoFeed", "PEGN", "Brazil Journal"]
    
    for i, res in enumerate(results):
        source_name = sources[i]
        if isinstance(res, list):
            logging.info(f"✅ {source_name}: Found {len(res)} items.")
            # Normalize keys
            for item in res:
                # Scrapers use 'link', main uses 'url'
                # Scrapers use 'date', main uses 'published_date'
                normalized = {
                    "title": item.get('title'),
                    "url": item.get('link'),
                    "published_date": item.get('date', ''), # raw string
                    "source": source_name,
                    "summary_feed": item.get('summary', ''),
                    "image": item.get('image', '')
                }
                all_articles.append(normalized)
        else:
            logging.error(f"❌ {source_name}: Failed with error {res}")
            
    return all_articles

def filter_by_date_scraped(results):
    """
    Filters using the 'date' field from scrapers.
    Logic:
    - If date is found and recent (Today/Yesterday) -> KEEP.
    - If date is found and OLD -> DROP.
    - If date is MISSING or Parse Error -> KEEP (Fall back to AI/Metadata check).
    """
    logging.info(f"🕵️ Filtering {len(results)} articles by scraped date...")
    
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    valid_articles = []
    
    for article in results:
        raw_date = article.get('published_date')
        title = article.get('title', 'No Title')
        
        parsed_date = parse_relative_date(raw_date)
        
        if parsed_date:
            # We have a valid date
            if parsed_date >= yesterday:
                logging.info(f"   ✅ Keep (Recent {parsed_date}): {title}")
                valid_articles.append(article)
            else:
                logging.info(f"   🗑️ Drop (Old {parsed_date}): {title}")
        else:
            # No date or error -> Keep for deep check
            logging.info(f"   ⚠️ Keep (No Date/Parse Error): {title}")
            valid_articles.append(article)

    logging.info(f"✅ Kept {len(valid_articles)} candidates for crawling.")
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
                    article['crawled_metadata'] = result.metadata
                    crawled_results.append(article)
                    logging.info(f"   ✅ Crawled: {url}")
                else:
                    logging.error(f"   ❌ Failed to crawl {url}: {result.error_message}")
            except Exception as e:
                logging.error(f"   ⚠️ Error processing {url}: {e}")
    return crawled_results

def filter_crawled_by_date(articles):
    """
    Second layer of date filtering using metadata extracted by Crawl4AI.
    Useful when Tavily fails to provide a date.
    """
    logging.info(f"🕵️ Filtering {len(articles)} crawled articles by METADATA date...")
    
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    valid_articles = []
    
    for article in articles:
        metadata = article.get('crawled_metadata', {})
        if not metadata:
             logging.info(f"   ⚠️ No Metadata: Keeping {article['title']}")
             valid_articles.append(article)
             continue

        # Try to find date in common metadata fields
        # 'article:published_time' is common in OG tags
        pub_date_str = metadata.get('article:published_time')
        
        if not pub_date_str:
            logging.info(f"   ⚠️ No Date in Metadata: Keeping {article['title']}")
            valid_articles.append(article)
            continue
            
        try:
            # Parse date
            article_date = parser.parse(pub_date_str).date()
            
            if article_date == today or article_date == yesterday:
                logging.info(f"   ✅ Keep (Metadata {article_date}): {article['title']}")
                valid_articles.append(article)
            else:
                logging.info(f"   🗑️ Dropped (Metadata Old {article_date}): {article['title']}")
                
        except Exception as e:
             logging.warning(f"   ⚠️ Metadata Date Parse Error ({pub_date_str}): {e}")
             valid_articles.append(article)

    return valid_articles

def analyze_relevance(model, article):
    """
    Uses LLM to check if the article is TRULY relevant for VC/Startup deals in Brazil.
    Returns: (bool, reason)
    """
    title = article.get('title')
    content_snippet = article.get('content', '')[:2000] # Check first 2000 chars

    logging.info(f"   🤖 Analyzing relevance: {title}")

    prompt = f"""
    Analyze if this article is relevant for a Venture Capital analyst focused on BRAZIL.
    
    CRITERIA for RELEVANCE (Must meet at least one):
    1. A Brazilian startup raising funds (Pre-seed, Seed, Series A+).
    2. A new venture capital fund being announced in Brazil.
    3. M&A involving Brazilian startups.
    4. Major regulatory changes affecting Brazilian tech startups.
    
    IMPORTANT: CHECK FRESHNESS!
    - If the article content clearly mentions dates from LAST YEAR or OLDER, mark as IRRELEVANT.
    - We are looking for news from the last 48 hours. If unsure, lean towards RELEVANT.
    
    EXCLUDE:
    - Global news without specific Brazil angle (unless it's a massive global shift).
    - Generic "how to" articles.
    - Public company earnings (unless relevant to tech ecosystem).
    - Sponsored content/Ads.

    ARTICLE TITLE: {title}
    ARTICLE CONTENT START:
    {content_snippet}

    Respond strictly in JSON format:
    {{
        "is_relevant": true/false,
        "reason": "Short explanation"
    }}
    """
    
    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        import json
        result = json.loads(response.text)
        return result.get("is_relevant", False), result.get("reason", "No reason provided")
    except Exception as e:
        logging.warning(f"   ⚠️ Relevance check failed (assuming relevant): {e}")
        # Fail safe: keep it if we can't check
        return True, "Error in check"

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
    # 1. Gather (Scrapers)
    if dry_run:
        logging.info("🔍 [DRY RUN] Mocking Scrapers.")
        today_str = datetime.now().strftime("%d/%m/%Y")
        raw_results = [
            {"title": "Fresh Startup Raise", "link": "http://mock.com/fresh", "date": today_str, "source": "Mock"},
            {"title": "Old Startup News", "link": "http://mock.com/old", "date": "01/01/2023", "source": "Mock"}
        ]
        # Normalize mock
        raw_results = [{"title": x["title"], "url": x["link"], "published_date": x["date"], "source": x["source"]} for x in raw_results]
    else:
        raw_results = await gather_news_from_scrapers()

    if not raw_results:
        logging.warning("❌ No results found from Scrapers.")
        return

    # 2. Strict Date Filter (Pre-Crawl)
    valid_articles = filter_by_date_scraped(raw_results)
    
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

    # 3.5 Post-Crawl Date Filter (Metadata)
    if not dry_run and crawled_data:
        crawled_data = filter_crawled_by_date(crawled_data)

    # 4. Relevance Check (AI)
    if dry_run:
        logging.info("🤖 [DRY RUN] Mocking Relevance Check.")
        final_articles = crawled_data
    else:
        logging.info("🧠 Running AI Relevance Filter...")
        final_articles = []
        for article in crawled_data:
            is_relevant, reason = analyze_relevance(model, article)
            if is_relevant:
                logging.info(f"   ✅ Relevant: {article['title']} ({reason})")
                final_articles.append(article)
            else:
                logging.info(f"   🚫 Irrelevant: {article['title']} ({reason})")

    if not final_articles:
        logging.warning("❌ No articles passed the relevance filter.")
        return

    # 5. Write
    newsletter_md = generate_newsletter(model, final_articles)

    # 6. Send
    if not dry_run and not args.no_email:
        logging.info("📧 Sending Email...")
        if send_daily_briefing(newsletter_md, EMAIL_TO):
            logging.info("🎉 Success!")
        else:
            logging.error("❌ Email failed.")
            sys.exit(1)
    else:
        logging.info("📧 [SKIP] Email sending skipped (--dry-run or --no-email).")
        logging.info("📄 Newsletter Content:\n" + newsletter_md)

if __name__ == "__main__":
    import argparse
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--dry-run", action="store_true")
    arg_parser.add_argument("--no-email", action="store_true", help="Skip sending email")
    args = arg_parser.parse_args()
    asyncio.run(run_pipeline(args.dry_run))
