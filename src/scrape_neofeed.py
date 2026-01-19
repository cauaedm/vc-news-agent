# src/scrape_neofeed.py
import asyncio
import logging
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def scrape_neofeed():
    url = "https://neofeed.com.br/noticias-sobre/venture-capital/"
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
            articles = soup.select('article.box-news')
            logger.info(f"Found {len(articles)} articles")
            
            for article in articles:
                item = {}
                
                # Title
                title_tag = article.select_one('h3.title-listagem')
                if title_tag:
                    item['title'] = title_tag.get_text(strip=True)
                
                # Link
                # The structure shows the link is on the anchor around the title or image
                # Let's target the one with rel="bookmark" in the text box area which seems most reliable
                link_tag = article.select_one('div.box-text a[rel="bookmark"]')
                if link_tag:
                    item['link'] = link_tag.get('href')
                
                # Category
                category_tag = article.select_one('span.tag')
                if category_tag:
                    item['category'] = category_tag.get_text(strip=True)
                
                # Summary
                summary_tag = article.select_one('.box-content p')
                if summary_tag:
                    item['summary'] = summary_tag.get_text(strip=True)
                
                # Image
                img_tag = article.select_one('.box-image img')
                if img_tag:
                    # NeoFeed uses lazy loading
                    item['image'] = img_tag.get('data-src') or img_tag.get('src')
                
                # Date
                date_tag = article.select_one('span.date')
                if date_tag:
                    item['date'] = date_tag.get_text(strip=True)
                
                if item.get('title') and item.get('link'):
                    news_items.append(item)
                    
    except Exception as e:
        logger.error(f"An error occurred during scraping: {e}")
        
    logger.info(f"Successfully extracted {len(news_items)} items")
    return news_items

if __name__ == "__main__":
    items = asyncio.run(scrape_neofeed())
    print(json.dumps(items, indent=2, ensure_ascii=False))
