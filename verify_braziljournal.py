
import asyncio
import json
from src.scrape_braziljournal import scrape_braziljournal

async def main():
    items = await scrape_braziljournal()
    print(f"Scraped {len(items)} items.")
    with open("braziljournal_data.json", "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    print("Verification complete. Data saved to braziljournal_data.json")

if __name__ == "__main__":
    asyncio.run(main())
