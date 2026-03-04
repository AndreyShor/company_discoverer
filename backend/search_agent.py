from typing import List, Dict
from ddgs import DDGS
import time

class SearchAgent:
    def __init__(self):
        self.ddgs = DDGS()

    def search_company_info(self, company_name: str, country: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Searches for business overviews and recent news about a company in a specific country.
        """
        queries = [
            f"{company_name} {country} business overview",
            f"{company_name} {country} recent news"
        ]
        
        all_results = []
        for query in queries:
            try:
                # Add a small delay to avoid rate limiting
                time.sleep(1)
                results = self.ddgs.text(query, max_results=max_results)
                for r in results:
                    all_results.append({
                        "title": r.get("title", ""),
                        "href": r.get("href", ""),
                        "body": r.get("body", "")
                    })
            except Exception as e:
                print(f"Error querying DDGS for '{query}': {e}")
                
        # Deduplicate by URL
        unique_results = []
        seen_urls = set()
        for res in all_results:
            url = res["href"]
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(res)
                
        return unique_results
