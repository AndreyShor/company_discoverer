import httpx
from bs4 import BeautifulSoup
from typing import List, Dict
import asyncio

class WebScraper:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    async def fetch_and_parse(self, url: str) -> str:
        """Fetches a URL and extracts readable text using BeautifulSoup."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove unneeded tags
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()
                    
                text = soup.get_text(separator=' ', strip=True)
                return text
        except Exception as e:
            print(f"Failed to scrape {url}: {e}")
            return ""

    async def scrape_urls(self, search_results: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Scrapes multiple URLs concurrently and attaches the text to the search results."""
        tasks = []
        for res in search_results:
            tasks.append(self.fetch_and_parse(res["href"]))
            
        scraped_texts = await asyncio.gather(*tasks)
        
        enriched_results = []
        for res, content in zip(search_results, scraped_texts):
            # Only include results where we successfully extracted significant text
            if content and len(content) > 100:
                res["scraped_content"] = content
                enriched_results.append(res)
            else:
                # Fallback to the DDGS snippet if scraping failed or returned too little content
                res["scraped_content"] = res.get("body", "")
                enriched_results.append(res)
                
        return enriched_results
