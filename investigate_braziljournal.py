
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url="https://braziljournal.com/tag/startups/")
        with open("braziljournal_raw.txt", "w", encoding="utf-8") as f:
            f.write(result.html)
        print("HTML saved to braziljournal_raw.txt")

if __name__ == "__main__":
    asyncio.run(main())
