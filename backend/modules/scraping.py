import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
import logging

class BrandScraper:
    """Class to handle scraping of brand information from websites"""
    
    def __init__(self):
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Common headers to mimic a browser request
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
    
    def scrape_brand_data(self, url, category=None, country=None):
        """
        Scrape brand data from a given URL
        
        Args:
            url (str): The website URL to scrape
            category (str, optional): Brand category (e.g., fashion, tech)
            country (str, optional): Brand's primary country
            
        Returns:
            dict: Extracted brand data or error information
        """
        try:
            # Validate URL
            if not self._is_valid_url(url):
                return {
                    "success": False,
                    "error": "Invalid URL",
                    "message": "Please provide a valid URL starting with http:// or https://"
                }
            
            # Get the domain name to use as a backup brand name
            domain = self._extract_domain(url)
            
            # Fetch the website content
            self.logger.info(f"Fetching content from: {url}")
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract brand information
            brand_data = {
                "success": True,
                "brand_name": self._extract_brand_name(soup, domain),
                "tagline": self._extract_tagline(soup),
                "description": self._extract_description(soup),
                "products": self._extract_products(soup),
                "category": category or self._infer_category(soup),
                "country": country,
                "source_url": url
            }
            
            return brand_data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request error: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to fetch URL: {str(e)}",
                "message": "Could not connect to the provided website. Please check the URL and try again."
            }
        except Exception as e:
            self.logger.error(f"Scraping error: {str(e)}")
            return {
                "success": False,
                "error": f"Scraping error: {str(e)}",
                "message": "An error occurred while processing the website content."
            }
    
    def _is_valid_url(self, url):
        """Check if a URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
        except:
            return False
    
    def _extract_domain(self, url):
        """Extract domain name from URL"""
        try:
            parsed_uri = urlparse(url)
            domain = parsed_uri.netloc
            # Remove www. if present
            if domain.startswith('www.'):
                domain = domain[4:]
            # Return just the first part of the domain (before any additional dots)
            return domain.split('.')[0].capitalize()
        except:
            return ""
    
    def _extract_brand_name(self, soup, fallback_domain):
        """Extract the brand name from the website"""
        # Try to get from title tag
        if soup.title:
            title = soup.title.text.strip()
            # Remove common title endings like "| Home" or "- Official Site"
            title = re.sub(r'[\|\-–—] .*$', '', title).strip()
            if title:
                return title
        
        # Try to get from meta tags
        meta_name = soup.find('meta', {'property': 'og:site_name'})
        if meta_name and meta_name.get('content'):
            return meta_name.get('content').strip()
        
        # Try to get from header or logo alt text
        logo = soup.find('img', {'alt': re.compile(r'logo', re.I)})
        if logo and logo.get('alt'):
            alt_text = logo.get('alt').strip()
            if 'logo' in alt_text.lower():
                return alt_text.replace('logo', '').replace('Logo', '').strip()
        
        # Use the domain name as fallback
        return fallback_domain
    
    def _extract_tagline(self, soup):
        """Extract tagline or slogan from the website"""
        # Check header elements for short text that might be a tagline
        for tag in ['h1', 'h2', 'h3']:
            elements = soup.find_all(tag)
            for element in elements:
                text = element.text.strip()
                # Taglines are typically short
                if 3 < len(text.split()) < 12 and not re.search(r'navigation|menu|contact|about', text, re.I):
                    return text
        
        # Check meta description as fallback
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            desc = meta_desc.get('content').strip()
            # Try to extract a short phrase from the beginning
            sentences = re.split(r'[.!?]', desc)
            if sentences and len(sentences[0].split()) < 15:
                return sentences[0].strip()
        
        return ""
    
    def _extract_description(self, soup):
        """Extract company description from the website"""
        # First try meta description
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc.get('content').strip()
        
        # Try to find an about section
        about_section = soup.find('section', {'id': re.compile(r'about', re.I)}) or \
                        soup.find('div', {'id': re.compile(r'about', re.I)}) or \
                        soup.find('section', {'class': re.compile(r'about', re.I)}) or \
                        soup.find('div', {'class': re.compile(r'about', re.I)})
        
        if about_section:
            paragraphs = about_section.find_all('p')
            if paragraphs:
                # Use the longest paragraph as it's likely to be the main description
                longest = max(paragraphs, key=lambda p: len(p.text.strip()))
                return longest.text.strip()
        
        # Try to find any paragraph on the homepage
        paragraphs = soup.find_all('p')
        if paragraphs:
            # Filter out very short paragraphs and navigation/footer text
            valid_paragraphs = [p.text.strip() for p in paragraphs 
                                if len(p.text.strip()) > 50 
                                and not re.search(r'cookie|privacy|terms|copyright', p.text, re.I)]
            if valid_paragraphs:
                return max(valid_paragraphs, key=len)
        
        return ""
    
    def _extract_products(self, soup):
        """Extract product names from the website"""
        products = []
        
        # Look for product listings
        product_elements = soup.find_all(['div', 'article', 'li'], {'class': re.compile(r'product|item', re.I)})
        
        for element in product_elements[:10]:  # Limit to top 10 products
            product_name = element.find(['h2', 'h3', 'h4', 'a'])
            if product_name:
                name = product_name.text.strip()
                if name and len(name) < 100:  # Reasonable product name length
                    products.append(name)
        
        # If no products found, try to find them in the navigation
        if not products:
            nav = soup.find(['nav', 'ul'], {'class': re.compile(r'nav|menu', re.I)})
            if nav:
                links = nav.find_all('a')
                for link in links:
                    text = link.text.strip()
                    # Skip common navigation items
                    if text and not re.search(r'home|about|contact|cart|login|sign in', text, re.I):
                        products.append(text)
        
        return products[:10]  # Return up to 10 products
    
    def _infer_category(self, soup):
        """Try to infer the brand category from the website content"""
        text = soup.get_text().lower()
        
        # Define category keywords
        categories = {
            'fashion': ['clothing', 'apparel', 'wear', 'fashion', 'dress', 'shoe', 'accessory', 'style'],
            'beauty': ['beauty', 'cosmetic', 'makeup', 'skincare', 'fragrance', 'perfume'],
            'tech': ['technology', 'tech', 'electronics', 'digital', 'device', 'gadget', 'software'],
            'food': ['food', 'beverage', 'drink', 'snack', 'meal', 'recipe', 'cuisine'],
            'health': ['health', 'wellness', 'fitness', 'supplement', 'vitamin', 'nutrition'],
            'home': ['home', 'furniture', 'decor', 'kitchen', 'bedding', 'interior'],
        }
        
        # Count occurrences of keywords for each category
        scores = {}
        for category, keywords in categories.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                scores[category] = score
        
        # Return the category with the highest score, or None if no matches
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        
        return None 