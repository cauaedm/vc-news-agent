import asyncio
import json
from src.scrape_startups import scrape_startups

async def main():
    items = await scrape_startups()
    with open("scraped_data.json", "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    print("Verification complete. Data saved to scraped_data.json")

if __name__ == "__main__":
    asyncio.run(main())
