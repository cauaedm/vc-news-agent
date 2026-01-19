import asyncio
import json
from src.scrape_neofeed import scrape_neofeed

async def main():
    items = await scrape_neofeed()
    with open("neofeed_data.json", "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    print("Verification complete. Data saved to neofeed_data.json")

if __name__ == "__main__":
    asyncio.run(main())
