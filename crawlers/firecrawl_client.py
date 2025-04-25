import requests
import os
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
API_KEY = os.getenv("FIRECRAWL_API_KEY")
BASE_URL = "https://api.firecrawl.dev/search"

def crawl_web(query: str, limit: int = 5, retries: int = 3, delay: int = 2) -> List[Dict[str, Any]]:
    """
    Search the web using FireCrawl API and return results.
    
    Args:
        query: Search query string
        limit: Maximum number of results to return
        retries: Number of retry attempts if request fails
        delay: Delay between retries in seconds
        
    Returns:
        List of search result dictionaries
    """
    if not API_KEY:
        print("[ERROR] FIRECRAWL_API_KEY not found in environment variables")
        return []
        
    headers = {"Authorization": f"Bearer {API_KEY}"}
    params = {"query": query, "limit": limit}
    
    for attempt in range(retries):
        try:
            print(f"[REQUEST] Sending query: {query}")
            response = requests.get(BASE_URL, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            results = response.json().get("results", [])
            print(f"[SUCCESS] Retrieved {len(results)} results for query: {query}")
            return results
            
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                print(f"[WARNING] Request failed (attempt {attempt+1}/{retries}): {e}")
                time.sleep(delay)
            else:
                print(f"[ERROR] FireCrawl request failed after {retries} attempts: {e}")
                return []
        except Exception as e:
            print(f"[ERROR] Unexpected error in FireCrawl request: {e}")
            return []
            
    return []