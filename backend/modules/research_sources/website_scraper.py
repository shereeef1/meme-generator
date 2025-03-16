import requests
from bs4 import BeautifulSoup
import logging
import re
import time
import random
import urllib.parse

logger = logging.getLogger(__name__)

class WebsiteScraper:
    """
    Class for scraping brand websites directly to extract information
    when Wikipedia or other sources don't have sufficient data.
    """
    
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
        ]
    
    def _get_random_user_agent(self):
        """Get a random user agent to avoid detection"""
        return random.choice(self.user_agents)
    
    def _normalize_url(self, url):
        """Normalize URL to ensure it has a scheme"""
        if not url.startswith(('http://', 'https://')):
            return f"https://{url}"
        return url
    
    def _extract_main_text(self, soup):
        """
        Extract the main text content from an HTML page,
        focusing on important sections like about, company, etc.
        """
        # Try to find important sections based on common patterns
        important_sections = []
        
        # Look for "About" section
        about_sections = soup.select("section[id*=about], div[id*=about], section[class*=about], div[class*=about]")
        important_sections.extend(about_sections)
        
        # Look for "Company" section
        company_sections = soup.select("section[id*=company], div[id*=company], section[class*=company], div[class*=company]")
        important_sections.extend(company_sections)
        
        # Look for main content area if we couldn't find specific sections
        if not important_sections:
            main_content = soup.select("main, article, .content, #content, .main-content")
            important_sections.extend(main_content)
        
        # Extract text from important sections
        content = []
        for section in important_sections:
            # Get all paragraphs
            paragraphs = section.select("p")
            for p in paragraphs:
                text = p.get_text().strip()
                if text and len(text) > 20:  # Skip very short paragraphs
                    content.append(text)
        
        # If we couldn't find any content in the important sections,
        # fall back to all paragraphs on the page
        if not content:
            all_paragraphs = soup.select("p")
            for p in all_paragraphs:
                text = p.get_text().strip()
                if text and len(text) > 20:  # Skip very short paragraphs
                    content.append(text)
                    
                    # Limit to ~50 paragraphs to avoid huge amounts of text
                    if len(content) >= 50:
                        break
        
        return "\n\n".join(content)
    
    def _extract_company_info(self, soup, url):
        """Extract structured company information from the page"""
        company_info = {
            "website": url,
            "name": "",
            "tagline": "",
            "founded": "",
            "headquarters": "",
            "industry": "",
            "products_services": []
        }
        
        # Try to extract company name and tagline from the page
        # Often in the header or title
        title = soup.select_one("title")
        if title:
            title_text = title.get_text().strip()
            # Company name is often before the pipe or dash in the title
            if " | " in title_text:
                company_info["name"] = title_text.split(" | ")[0].strip()
            elif " - " in title_text:
                company_info["name"] = title_text.split(" - ")[0].strip()
            else:
                company_info["name"] = title_text
        
        # Try to find a tagline (often a subtitle or description)
        meta_description = soup.select_one("meta[name='description']")
        if meta_description:
            company_info["tagline"] = meta_description.get("content", "").strip()
        
        # Extract product/service information
        product_sections = soup.select("section[id*=product], div[id*=product], section[class*=product], div[class*=product]")
        for section in product_sections:
            headings = section.select("h1, h2, h3, h4")
            for heading in headings:
                product_name = heading.get_text().strip()
                if product_name:
                    company_info["products_services"].append(product_name)
        
        # Limit to prevent excessive results
        company_info["products_services"] = company_info["products_services"][:10]
        
        return company_info
    
    def scrape_brand_website(self, url, brand_name=None):
        """
        Scrape a brand's website for information
        
        Args:
            url (str): URL of the brand website
            brand_name (str, optional): Name of the brand for fallback
            
        Returns:
            dict: Structured information about the brand
        """
        max_retries = 3
        retry_delay = 2  # seconds
        
        # Ensure URL is properly formatted
        url = self._normalize_url(url)
        
        logger.info(f"Scraping brand website: {url}")
        
        for retry in range(max_retries):
            try:
                headers = {
                    "User-Agent": self._get_random_user_agent(),
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Referer": "https://www.google.com/",
                    "DNT": "1"
                }
                
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=30,
                    allow_redirects=True
                )
                
                if response.status_code != 200:
                    logger.error(f"Website scrape failed with status code: {response.status_code}")
                    if retry < max_retries - 1:
                        logger.info(f"Waiting {retry_delay} seconds before retrying...")
                        time.sleep(retry_delay * (retry + 1))
                        continue
                    else:
                        return {
                            "success": False,
                            "error": f"Failed to access website: {response.status_code}",
                            "data": {},
                            "text": f"Could not access the website {url}.",
                            "url": url
                        }
                
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Check for common bot detection or access denied pages
                if any(term in response.text.lower() for term in ["captcha", "robot", "automated access", "access denied"]):
                    logger.warning(f"Bot detection triggered for: {url}")
                    if retry < max_retries - 1:
                        logger.info(f"Waiting {retry_delay} seconds before retrying with a different user agent...")
                        time.sleep(retry_delay * (retry + 1))
                        continue
                    else:
                        return {
                            "success": False,
                            "error": "Bot detection triggered",
                            "data": {},
                            "text": f"Unable to access {url} due to bot protection.",
                            "url": url
                        }
                
                # Extract content from the page
                main_text = self._extract_main_text(soup)
                company_info = self._extract_company_info(soup, url)
                
                # Try to also scrape the About page if we're on the home page
                about_urls = []
                for a in soup.select("a"):
                    href = a.get("href")
                    text = a.get_text().lower().strip()
                    
                    if not href:
                        continue
                        
                    # Look for "about" links
                    if "about" in text or "about-us" in text or "about us" in text:
                        if href.startswith("/"):
                            # Relative URL
                            parsed_url = urllib.parse.urlparse(url)
                            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                            about_urls.append(f"{base_url}{href}")
                        elif href.startswith("http"):
                            # Absolute URL
                            about_urls.append(href)
                        else:
                            # Relative without leading slash
                            parsed_url = urllib.parse.urlparse(url)
                            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                            about_urls.append(f"{base_url}/{href}")
                
                # If we found an about page and we're not already on it,
                # scrape that too and combine the results
                about_text = ""
                if about_urls and not any(term in url.lower() for term in ["/about", "about-us", "about_us"]):
                    about_url = about_urls[0]  # Just use the first one we found
                    try:
                        logger.info(f"Scraping about page: {about_url}")
                        about_response = requests.get(
                            about_url,
                            headers=headers,
                            timeout=30
                        )
                        
                        if about_response.status_code == 200:
                            about_soup = BeautifulSoup(about_response.text, "html.parser")
                            about_text = self._extract_main_text(about_soup)
                    except Exception as e:
                        logger.error(f"Error scraping about page: {e}")
                
                # Combine main page text and about page text
                combined_text = main_text
                if about_text:
                    combined_text += f"\n\n--- ABOUT PAGE ---\n\n{about_text}"
                
                # If we have almost no text, this probably failed
                if len(combined_text) < 100:
                    logger.warning(f"Website scrape yielded very little text: {len(combined_text)} chars")
                    if retry < max_retries - 1:
                        logger.info(f"Waiting {retry_delay} seconds before retrying...")
                        time.sleep(retry_delay * (retry + 1))
                        continue
                    else:
                        return {
                            "success": False,
                            "error": "Insufficient text extracted",
                            "data": {},
                            "text": f"Could not extract meaningful information from {url}.",
                            "url": url
                        }
                
                # Create a formatted text representation
                formatted_text = f"Website Information for: {company_info['name'] or brand_name or 'Unknown'}\n\n"
                formatted_text += f"URL: {url}\n\n"
                
                if company_info['tagline']:
                    formatted_text += f"Tagline: {company_info['tagline']}\n\n"
                
                if company_info['products_services']:
                    formatted_text += "Products/Services:\n"
                    for item in company_info['products_services']:
                        formatted_text += f"- {item}\n"
                    formatted_text += "\n"
                
                formatted_text += "Website Content:\n\n"
                formatted_text += combined_text
                
                logger.info(f"Successfully scraped website: {url}, extracted {len(combined_text)} chars")
                
                return {
                    "success": True,
                    "data": company_info,
                    "text": formatted_text,
                    "url": url,
                    "error": None
                }
                
            except Exception as e:
                logger.error(f"Error scraping website {url}: {e}")
                if retry < max_retries - 1:
                    logger.info(f"Waiting {retry_delay} seconds before retrying...")
                    time.sleep(retry_delay * (retry + 1))
                    continue
                else:
                    return {
                        "success": False,
                        "error": str(e),
                        "data": {},
                        "text": f"Error accessing website: {str(e)}",
                        "url": url
                    } 