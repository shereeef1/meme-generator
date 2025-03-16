import requests
from bs4 import BeautifulSoup
import logging
import re
import time
import random

logger = logging.getLogger(__name__)

class DuckDuckGoSearch:
    """
    Class for scraping DuckDuckGo search results without requiring an API.
    Uses direct HTML scraping to gather brand information.
    """
    
    def __init__(self):
        self.base_url = "https://html.duckduckgo.com/html/"
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
        ]
    
    def _get_random_user_agent(self):
        """Get a random user agent to avoid detection"""
        return random.choice(self.user_agents)
    
    def _search_duckduckgo(self, query, max_results=10):
        """
        Perform a search on DuckDuckGo
        
        Args:
            query (str): The search query
            max_results (int): Maximum number of results to return
            
        Returns:
            list: List of search results
        """
        headers = {
            "User-Agent": self._get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://duckduckgo.com/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        params = {
            "q": query,
            "kl": "us-en"
        }
        
        # Add retry logic to handle temporary failures
        max_retries = 3
        retry_delay = 2  # seconds
        
        for retry in range(max_retries):
            try:
                logger.info(f"Searching DuckDuckGo for: {query} (attempt {retry + 1} of {max_retries})")
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    data=params,
                    timeout=20
                )
                
                # Handle 202 Accepted response (temporary rate limiting)
                if response.status_code == 202:
                    logger.warning(f"DuckDuckGo returned 202 status (rate limiting), attempt {retry + 1}/{max_retries}")
                    if retry < max_retries - 1:
                        logger.info(f"Waiting {retry_delay} seconds before retrying...")
                        time.sleep(retry_delay * (retry + 1))  # Exponential backoff
                        continue
                    else:
                        logger.error("DuckDuckGo search failed after maximum retries")
                        return []
                
                if response.status_code != 200:
                    logger.error(f"DuckDuckGo search failed with status code: {response.status_code}")
                    if retry < max_retries - 1:
                        logger.info(f"Waiting {retry_delay} seconds before retrying...")
                        time.sleep(retry_delay * (retry + 1))
                        continue
                    else:
                        return []
                
                # Check if the response is a bot detection page or empty
                if "Please try again" in response.text or "detected unusual activity" in response.text:
                    logger.warning("DuckDuckGo bot detection triggered")
                    if retry < max_retries - 1:
                        logger.info(f"Waiting {retry_delay} seconds before retrying with a different user agent...")
                        time.sleep(retry_delay * (retry + 1))
                        # Change user agent for next attempt
                        headers["User-Agent"] = self._get_random_user_agent()
                        continue
                    else:
                        return []
                
                soup = BeautifulSoup(response.text, "html.parser")
                results = []
                
                # Extract search results
                for result in soup.select(".result"):
                    try:
                        title_element = result.select_one(".result__a")
                        url_element = result.select_one(".result__url")
                        snippet_element = result.select_one(".result__snippet")
                        
                        if not title_element or not snippet_element:
                            continue
                        
                        title = title_element.get_text().strip()
                        url = title_element.get("href")
                        if url_element:
                            displayed_url = url_element.get_text().strip()
                        else:
                            displayed_url = url
                        
                        snippet = snippet_element.get_text().strip()
                        
                        # Clean the URL (DuckDuckGo uses redirects)
                        if url and "duckduckgo.com" in url:
                            url_match = re.search(r'uddg=([^&]+)', url)
                            if url_match:
                                url = requests.utils.unquote(url_match.group(1))
                        
                        results.append({
                            "title": title,
                            "url": url,
                            "displayed_url": displayed_url,
                            "snippet": snippet
                        })
                        
                        if len(results) >= max_results:
                            break
                            
                    except Exception as e:
                        logger.error(f"Error parsing search result: {e}")
                        continue
                
                logger.info(f"Found {len(results)} results for query: {query}")
                return results
                
            except Exception as e:
                logger.error(f"Error during DuckDuckGo search: {e}")
                if retry < max_retries - 1:
                    logger.info(f"Waiting {retry_delay} seconds before retrying...")
                    time.sleep(retry_delay * (retry + 1))
                    continue
                else:
                    return []
    
    def search_brand(self, brand_name, max_results=15):
        """
        Perform a multi-query search for brand information
        
        Args:
            brand_name (str): The name of the brand to research
            max_results (int): Maximum number of results per query
            
        Returns:
            dict: Aggregated search results
        """
        logger.info(f"Starting enhanced search for brand: {brand_name}")
        
        # Define search queries for different aspects of brand information
        queries = [
            f"{brand_name} official website",
            f"{brand_name} company about",
            f"{brand_name} history company",
            f"{brand_name} products services",
            f"{brand_name} customers reviews"
        ]
        
        all_results = []
        sources = []
        combined_text = ""
        partial_failures = []
        
        # Track if we had any successful queries
        success_count = 0
        attempts_count = 0
        
        for query in queries:
            logger.info(f"Executing query: {query}")
            attempts_count += 1
            
            # Add random delay to avoid rate limiting
            time.sleep(random.uniform(1, 3))
            
            # Search DuckDuckGo
            results = self._search_duckduckgo(query, max_results=3)
            
            if not results:
                # This query failed, record it
                partial_failures.append({
                    "query": query,
                    "error": "DuckDuckGo search failed"
                })
                continue
                
            success_count += 1
            
            for result in results:
                # Check if this result URL is already in our list
                if not any(r["url"] == result["url"] for r in all_results):
                    all_results.append(result)
                    sources.append({"type": "search", "url": result["url"], "query": query})
                    
                    # Add to combined text
                    combined_text += f"\nTitle: {result['title']}\n"
                    combined_text += f"URL: {result['url']}\n"
                    combined_text += f"Snippet: {result['snippet']}\n\n"
        
        # Sort results by relevance (containing brand name in title or URL)
        all_results.sort(
            key=lambda x: (
                brand_name.lower() in x["title"].lower(),
                brand_name.lower() in x["url"].lower(),
                "official" in x["title"].lower() or "official" in x["url"].lower()
            ),
            reverse=True
        )
        
        # Limit to top results
        all_results = all_results[:max_results]
        
        # Determine overall success based on how many queries succeeded
        if success_count == attempts_count:
            # Full success - all queries worked
            overall_success = True
        elif success_count > 0:
            # Partial success - some queries worked
            overall_success = True  # We still consider it a success if we have some results
        else:
            # Complete failure - no queries worked
            overall_success = False
        
        # Create a properly formatted text representation
        formatted_text = f"DuckDuckGo Search Results for {brand_name}:\n\n"
        
        if all_results:
            for result in all_results:
                formatted_text += f"Title: {result['title']}\n"
                formatted_text += f"URL: {result['url']}\n"
                formatted_text += f"Snippet: {result['snippet']}\n\n"
        else:
            formatted_text += f"No search results found for {brand_name}.\n"
            
        # Include information about rate limiting if that happened
        if partial_failures and success_count < attempts_count:
            formatted_text += f"\nNote: {attempts_count - success_count} out of {attempts_count} search queries failed, possibly due to rate limiting.\n"
        
        return {
            "success": overall_success,
            "error": "DuckDuckGo rate limiting" if partial_failures and not overall_success else None,
            "results": all_results,
            "text": formatted_text,
            "sources": sources,
            "partial_failures": partial_failures
        } 