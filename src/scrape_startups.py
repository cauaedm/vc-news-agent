# src/scrape_startups.py
import asyncio
import logging
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def scrape_startups():
    url = "https://startups.com.br/ultimas-noticias/"
    logger.info(f"Starting scrape for: {url}")
    
    news_items = []
    
    try:
        async with AsyncWebCrawler(verbose=True) as crawler:
            result = await crawler.arun(url=url)
            
            if not result.success:
                logger.error(f"Failed to crawl {url}: {result.error_message}")
                return []
            
            soup = BeautifulSoup(result.html, 'html.parser')
            
            # Select all news articles
            articles = soup.select('article.feed')
            logger.info(f"Found {len(articles)} articles")
            
            for article in articles:
                item = {}
                
                # Title
                title_tag = article.select_one('h2.feed-title')
                if title_tag:
                    item['title'] = title_tag.get_text(strip=True)
                
                # Link
                link_tag = article.select_one('a.feed-link')
                if link_tag:
                    item['link'] = link_tag.get('href')
                
                # Category
                category_tag = article.select_one('.feed-hat')
                if category_tag:
                    item['category'] = category_tag.get_text(strip=True)
                
                # Summary
                summary_tag = article.select_one('.feed-excert')
                if summary_tag:
                    item['summary'] = summary_tag.get_text(strip=True)
                
                # Image
                img_tag = article.select_one('img')
                if img_tag:
                    # Prefer lazy loaded src
                    item['image'] = img_tag.get('data-lazy-src') or img_tag.get('src')
                
                if item.get('title') and item.get('link'):
                    news_items.append(item)
                    
    except Exception as e:
        logger.error(f"An error occurred during scraping: {e}")
        
    logger.info(f"Successfully extracted {len(news_items)} items")
    return news_items

if __name__ == "__main__":
    items = asyncio.run(scrape_startups())
    print(json.dumps(items, indent=2, ensure_ascii=False))
