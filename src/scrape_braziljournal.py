
import asyncio
import json
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler

async def scrape_braziljournal():
    url = "https://braziljournal.com/tag/startups/"
    formatted_data = []

    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url=url)
        
        if not result.success:
            print(f"Failed to crawl {url}")
            return []

        soup = BeautifulSoup(result.html, 'html.parser')
        # Select all articles
        articles = soup.select("article.boxarticle")

        print(f"Found {len(articles)} articles")

        for article in articles:
            try:
                # Title & Link from the same anchor usually
                title_tag = article.select_one("h2.boxarticle-infos-title a")
                title = title_tag.get_text(strip=True) if title_tag else "No Title"
                link = title_tag['href'] if title_tag and title_tag.has_attr('href') else ""
                
                # Category
                # The tag might be inside p.boxarticle-infos-tag. 
                # Sometimes there's an img and an 'a' tag. We want the text of the 'a' tag.
                category_tag = article.select_one("p.boxarticle-infos-tag a")
                category = category_tag.get_text(strip=True) if category_tag else "Startups"
                
                # Summary
                summary_tag = article.select_one("p.boxarticle-infos-text")
                summary = summary_tag.get_text(strip=True) if summary_tag else ""
                
                # Image
                # Usually inside a.boxarticle-img -> picture -> img
                image_tag = article.select_one("a.boxarticle-img img")
                image_url = image_tag['src'] if image_tag and image_tag.has_attr('src') else ""
                
                # Date
                # Not available in the list view for Brazil Journal based on analysis
                date_str = ""

                formatted_data.append({
                    "title": title,
                    "link": link,
                    "category": category,
                    "summary": summary,
                    "image": image_url,
                    "date": date_str,
                    "source": "Brazil Journal"
                })

            except Exception as e:
                print(f"Error parsing article: {e}")
                continue

    return formatted_data

if __name__ == "__main__":
    data = asyncio.run(scrape_braziljournal())
    print(json.dumps(data, indent=4, ensure_ascii=False))
