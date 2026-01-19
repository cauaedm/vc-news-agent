import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url="https://revistapegn.globo.com/startups/")
        with open("pegn_raw.txt", "w", encoding="utf-8") as f:
            f.write(result.html)

if __name__ == "__main__":
    asyncio.run(main())
