import requests
from bs4 import BeautifulSoup
import logging
import re
import time
import random

logger = logging.getLogger(__name__)

class WikipediaScraper:
    """
    Class for scraping Wikipedia pages to extract brand information
    without requiring an API. Uses direct HTML scraping.
    """
    
    def __init__(self):
        self.base_url = "https://en.wikipedia.org/wiki/"
        self.search_url = "https://en.wikipedia.org/w/index.php"
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
        ]
    
    def _get_random_user_agent(self):
        """Get a random user agent to avoid detection"""
        return random.choice(self.user_agents)
    
    def _format_wiki_url(self, title):
        """Format a string for use in a Wikipedia URL"""
        return title.replace(" ", "_")
    
    def _search_wikipedia(self, query):
        """
        Search Wikipedia for a term and return the best match
        
        Args:
            query (str): The search query
            
        Returns:
            str: The best match page title, or None if no match
        """
        headers = {
            "User-Agent": self._get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }
        
        params = {
            "search": query,
            "title": "Special:Search"
        }
        
        try:
            logger.info(f"Searching Wikipedia for: {query}")
            response = requests.get(
                self.search_url,
                headers=headers,
                params=params,
                timeout=20
            )
            
            if response.status_code != 200:
                logger.error(f"Wikipedia search failed with status code: {response.status_code}")
                return None
            
            # If we're redirected directly to a page, that's our best match
            if "/wiki/" in response.url and "Special:Search" not in response.url:
                page_title = response.url.split("/wiki/")[1]
                
                # Validate that this is actually relevant to our query
                # Split the query and the page title into words for comparison
                query_words = query.lower().split()
                title_words = page_title.lower().replace('_', ' ').split()
                
                # Check if at least 50% of query words are in the title
                # This helps prevent completely unrelated redirects
                matches = sum(1 for word in query_words if any(word in title for title in title_words))
                if matches / len(query_words) >= 0.5:
                    return page_title
                else:
                    logger.warning(f"Wikipedia redirected to an unrelated page: {page_title}")
                    return None
            
            # Otherwise, parse the search results
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Look for the first search result
            search_results = soup.select(".mw-search-result-heading a")
            if search_results:
                # Check multiple results for the best match
                for result in search_results[:3]:  # Check top 3 results
                    best_match = result.get("title")
                    
                    # Make sure this is actually about our brand (not just any company)
                    query_terms = query.lower().split()
                    title_terms = best_match.lower().split()
                    
                    # Ensure strong relevance - main brand name must be in the title
                    if query_terms[0] in title_terms:
                        logger.info(f"Found matching Wikipedia page: {best_match}")
                        return self._format_wiki_url(best_match)
                
                # If we get here, no strong matches were found
                logger.warning(f"No closely matching Wikipedia pages found for: {query}")
                return None
            
            return None
            
        except Exception as e:
            logger.error(f"Error during Wikipedia search: {e}")
            return None
    
    def _extract_infobox(self, soup):
        """
        Extract information from the Wikipedia infobox
        
        Args:
            soup (BeautifulSoup): BeautifulSoup object of the page
            
        Returns:
            dict: Extracted infobox information
        """
        infobox = {}
        infobox_table = soup.select_one(".infobox")
        
        if not infobox_table:
            return infobox
        
        # Extract rows from the infobox
        rows = infobox_table.select("tr")
        for row in rows:
            # Look for header and data cells
            header = row.select_one("th")
            data = row.select_one("td")
            
            if header and data:
                key = header.get_text().strip()
                
                # Remove citations and note numbers
                value = re.sub(r'\[\d+\]', '', data.get_text().strip())
                
                # Clean up whitespace
                value = re.sub(r'\s+', ' ', value).strip()
                
                infobox[key] = value
        
        return infobox
    
    def _extract_sections(self, soup):
        """
        Extract key sections from the Wikipedia page
        
        Args:
            soup (BeautifulSoup): BeautifulSoup object of the page
            
        Returns:
            dict: Extracted sections
        """
        sections = {}
        
        # Get all headings
        headings = soup.select("#content h2, #content h3")
        
        for heading in headings:
            # Get the heading text without the edit button
            heading_text = heading.select_one(".mw-headline")
            if not heading_text:
                continue
                
            section_name = heading_text.get_text().strip()
            
            # Skip references and external links
            if section_name.lower() in ["references", "external links", "see also", "further reading"]:
                continue
            
            # Get all paragraphs until the next heading
            section_content = []
            current = heading.next_sibling
            
            while current and not (current.name in ["h2", "h3", "h4"]):
                if current.name == "p":
                    # Remove citations
                    text = re.sub(r'\[\d+\]', '', current.get_text().strip())
                    if text:
                        section_content.append(text)
                current = current.next_sibling
            
            if section_content:
                sections[section_name] = "\n".join(section_content)
        
        return sections
    
    def _extract_first_paragraph(self, soup):
        """
        Extract the first paragraph from the Wikipedia page,
        which typically contains a summary of the topic.
        
        Args:
            soup (BeautifulSoup): BeautifulSoup object of the page
            
        Returns:
            str: The first paragraph text
        """
        # Find the first paragraph after the heading
        paragraphs = soup.select("#mw-content-text > div.mw-parser-output > p")
        
        for p in paragraphs:
            # Skip empty paragraphs
            if not p.get_text().strip():
                continue
                
            # Remove citations
            text = re.sub(r'\[\d+\]', '', p.get_text().strip())
            
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text
        
        return ""
    
    def scrape_wikipedia(self, brand_name):
        """
        Scrape Wikipedia for information about a brand
        
        Args:
            brand_name (str): The name of the brand to research
            
        Returns:
            dict: Structured information about the brand
        """
        # Add retry logic
        max_retries = 3
        retry_delay = 2  # seconds
        
        for retry in range(max_retries):
            try:
                logger.info(f"Scraping Wikipedia for: {brand_name} (attempt {retry + 1} of {max_retries})")
                
                # Step 1: Find the most relevant Wikipedia page
                page_title = self._search_wikipedia(brand_name)
                
                if not page_title:
                    logger.warning(f"No Wikipedia page found for: {brand_name}")
                    return {
                        "success": False,
                        "error": "No Wikipedia page found",
                        "data": {},
                        "text": f"No Wikipedia page found for {brand_name}. Consider checking for alternative spellings or company names.",
                        "url": ""
                    }
                
                # Step 2: Get the Wikipedia page content
                wiki_url = f"{self.base_url}{page_title}"
                
                headers = {
                    "User-Agent": self._get_random_user_agent(),
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5"
                }
                
                response = requests.get(
                    wiki_url,
                    headers=headers,
                    timeout=20
                )
                
                if response.status_code != 200:
                    logger.error(f"Wikipedia page fetch failed with status code: {response.status_code}")
                    if retry < max_retries - 1:
                        logger.info(f"Waiting {retry_delay} seconds before retrying...")
                        time.sleep(retry_delay * (retry + 1))
                        continue
                    else:
                        return {
                            "success": False,
                            "error": f"Failed to fetch Wikipedia page: {response.status_code}",
                            "data": {},
                            "text": f"Wikipedia information for {brand_name} is currently unavailable.",
                            "url": wiki_url
                        }
                
                # Check if the response is a redirect page or disambiguation page
                if "may refer to:" in response.text or "disambig" in response.text:
                    logger.warning(f"Wikipedia disambiguation page found for: {brand_name}")
                    
                    # Try to extract a more specific term
                    soup = BeautifulSoup(response.text, "html.parser")
                    links = soup.select("div.mw-parser-output ul li a")
                    
                    # Find the first link that contains something company-like
                    company_keywords = ["company", "corporation", "brand", "business", "enterprise", "organization"]
                    for link in links:
                        if any(keyword in link.text.lower() for keyword in company_keywords):
                            logger.info(f"Found more specific company link: {link.text}")
                            
                            # Try this more specific link
                            if retry < max_retries - 1:
                                page_title = link.get("title")
                                if page_title:
                                    return self.scrape_wikipedia(page_title)
                    
                    return {
                        "success": False,
                        "error": "Disambiguation page found",
                        "data": {},
                        "text": f"Multiple Wikipedia pages were found for '{brand_name}'. Please specify a more exact name.",
                        "url": wiki_url
                    }
                
                # Step 3: Parse the page content
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Extract the title
                title = soup.select_one("#firstHeading").get_text().strip() if soup.select_one("#firstHeading") else page_title
                
                # Extract information
                infobox = self._extract_infobox(soup)
                first_paragraph = self._extract_first_paragraph(soup)
                sections = self._extract_sections(soup)
                
                # Prepare the structured data
                data = {
                    "title": title,
                    "url": wiki_url,
                    "summary": first_paragraph,
                    "infobox": infobox,
                    "sections": sections
                }
                
                # Create a combined text representation
                combined_text = f"Wikipedia Information for: {title}\n\n"
                combined_text += f"URL: {wiki_url}\n\n"
                combined_text += f"Summary: {first_paragraph}\n\n"
                
                # Add infobox information
                if infobox:
                    combined_text += "Company Information:\n"
                    for key, value in infobox.items():
                        combined_text += f"- {key}: {value}\n"
                    combined_text += "\n"
                
                # Add selected important sections
                important_sections = ["History", "Overview", "Products", "Services", "Business"]
                for section_name, section_content in sections.items():
                    if any(important in section_name for important in important_sections):
                        combined_text += f"{section_name}:\n{section_content}\n\n"
                
                logger.info(f"Successfully scraped Wikipedia for: {brand_name}")
                
                return {
                    "success": True,
                    "data": data,
                    "text": combined_text,
                    "url": wiki_url,
                    "error": None
                }
                
            except Exception as e:
                logger.error(f"Error scraping Wikipedia for {brand_name}: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "data": {},
                    "text": "",
                    "url": ""
                } 