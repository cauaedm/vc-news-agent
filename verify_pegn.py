
import asyncio
import json
from src.scrape_pegn import scrape_pegn

async def main():
    items = await scrape_pegn()
    with open("pegn_data.json", "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    print("Verification complete. Data saved to pegn_data.json")

if __name__ == "__main__":
    asyncio.run(main())
