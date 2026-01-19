
import asyncio
import json
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler

async def scrape_pegn():
    url = "https://revistapegn.globo.com/startups/"
    formatted_data = []

    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url=url)
        
        if not result.success:
            print(f"Failed to crawl {url}")
            return []

        soup = BeautifulSoup(result.html, 'html.parser')
        articles = soup.select("div.feed-post")

        print(f"Found {len(articles)} articles")

        for article in articles:
            try:
                # Title
                title_tag = article.select_one("a.feed-post-link")
                title = title_tag.get_text(strip=True) if title_tag else "No Title"
                
                # Link
                link = title_tag['href'] if title_tag and title_tag.has_attr('href') else ""
                
                # Category
                category_tag = article.select_one("span.feed-post-metadata-section")
                category = category_tag.get_text(strip=True) if category_tag else "General"
                
                # Summary
                summary_tag = article.select_one("p.feed-post-body-resumo")
                summary = summary_tag.get_text(strip=True) if summary_tag else ""
                
                # Image
                image_tag = article.select_one("img.bstn-fd-picture-image")
                image_url = image_tag['src'] if image_tag and image_tag.has_attr('src') else ""
                
                # Date
                date_tag = article.select_one("span.feed-post-datetime")
                date_str = date_tag.get_text(strip=True) if date_tag else ""

                formatted_data.append({
                    "title": title,
                    "link": link,
                    "category": category,
                    "summary": summary,
                    "image": image_url,
                    "date": date_str,
                    "source": "PEGN"
                })

            except Exception as e:
                print(f"Error parsing article: {e}")
                continue

    return formatted_data

if __name__ == "__main__":
    data = asyncio.run(scrape_pegn())
    print(json.dumps(data, indent=4, ensure_ascii=False))
