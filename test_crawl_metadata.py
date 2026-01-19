import asyncio
import logging
import json
from crawl4ai import AsyncWebCrawler

# URL that we know had "NO DATE" from Tavily
TEST_URL = "https://startups.com.br/negocios/inovacao/brasil-domina-ranking-de-ecossistemas-de-inovacao-na-america-latina/"

logging.basicConfig(level=logging.INFO)

async def test_crawl_date():
    print(f"🕷️ Crawling {TEST_URL} to check for date metadata...")
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url=TEST_URL)
        
        with open("crawl_debug.txt", "w", encoding="utf-8") as f:
            if result.success:
                f.write("✅ Crawl Successful!\n")
                f.write(f"\n--- Metadata Attribute ---\n{json.dumps(result.metadata, indent=2, ensure_ascii=False) if result.metadata else 'None'}\n")
                
                f.write("\n--- Result Object Attributes ---\n")
                for attr in dir(result):
                    if not attr.startswith('__') and not callable(getattr(result, attr)):
                        val = getattr(result, attr)
                        if isinstance(val, (str, int, float, bool, dict, list)):
                            val_str = str(val)
                            f.write(f"{attr}: {val_str[:500]}\n") # Truncate 500 chars
            else:
                 f.write(f"❌ Crawl Failed: {result.error_message}\n")
    
    print("Done. Check crawl_debug.txt")

if __name__ == "__main__":
    asyncio.run(test_crawl_date())
