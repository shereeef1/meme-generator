import requests
import json
import logging
import os
from config import Config
from datetime import datetime, timedelta
import traceback
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time
import random
import re
from urllib.parse import urljoin, urlparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/news_api.log'),
        logging.StreamHandler()
    ]
)

class NewsIntegration:
    """Class to fetch and filter trending news for brands"""
    
    def __init__(self):
        self.api_key = Config.NEWS_API_KEY
        self.top_headlines_url = "https://newsapi.org/v2/top-headlines"
        self.everything_url = "https://newsapi.org/v2/everything"
        self.logger = logging.getLogger(__name__)
        
        # Create a cache for news results to reduce API calls
        self.news_cache = {}
        self.cache_expiry = 60 * 60  # Cache news for 1 hour (in seconds)
        
        # Flag to indicate if we're out of API quota
        self.api_quota_exceeded = False
        self.quota_reset_time = None
        
        # Track how many API calls we've made
        self.api_calls_count = 0
        self.max_api_calls = 20  # Conservative limit (actual limit is 100 per day)
        
        # Log API key existence for debugging
        if self.api_key:
            self.logger.info(f"NewsAPI key is configured: {self.api_key[:4]}...{self.api_key[-4:] if len(self.api_key) > 8 else 'too_short'}")
        else:
            self.logger.error("NewsAPI key is not configured!")
            
        # Log the config values for debugging
        self.logger.debug(f"NEWS_API_KEY from Config: {self.api_key}")
    
    def get_top_news(self, limit=20, days=14, country='in', category=None):
        """
        Get trending news articles.
        
        Parameters:
        - limit (int): Number of articles to return
        - days (int): Number of past days to include articles from (default: 14 days)
        - country (str): Country code to fetch news for (default: 'in' for India)
        - category (str, optional): Category to filter news by (default: None for all categories)
            
        Returns:
        - list: List of trending news articles
        """
        # Check if we've exceeded our API quota
        if self.api_quota_exceeded:
            # If we have a reset time and it's passed, reset the flag
            if self.quota_reset_time and datetime.now() > self.quota_reset_time:
                self.api_quota_exceeded = False
                self.api_calls_count = 0
                self.logger.info("API quota reset - resuming normal operations")
            else:
                # If we're still rate limited, use Google News scraper fallback
                self.logger.warning("API quota exceeded - falling back to Google News scraper")
                return self._scrape_google_news(limit=limit, country=country)
        
        # Calculate the date range (from days ago to today)
        from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        to_date = datetime.now().strftime('%Y-%m-%d')
        
        # Create a cache key based on parameters
        cache_key = f"{country}_{category}_{limit}_{days}"
        
        # Check if we have a valid cached result
        if cache_key in self.news_cache:
            cache_entry = self.news_cache[cache_key]
            # If the cache is still valid (not expired)
            if datetime.now().timestamp() - cache_entry['timestamp'] < self.cache_expiry:
                self.logger.info(f"Returning cached news for {cache_key}")
                return cache_entry['articles']
        
        self.logger.info(f"Fetching trending news from {from_date} to {to_date} for country {country}, category: {category}, limit: {limit}")
        
        # Initialize empty articles list
        all_articles = []
        
        # Only make API calls if we haven't exceeded our quota
        if not self.api_quota_exceeded:
            try:
                # First try with top headlines - this is the most efficient API call
                if self.api_calls_count < self.max_api_calls:
                    self.api_calls_count += 1
                    articles = self._get_top_headlines_by_country(country, limit, category)
                    
                    # Apply date filter post-retrieval for top headlines
                    filtered_articles = self._filter_recent_articles(articles, days)
                    all_articles.extend(filtered_articles)
                
                # If not enough articles and we still have API calls available, try with one popular source
                if len(all_articles) < limit and self.api_calls_count < self.max_api_calls:
                    # Use only one most reliable source to avoid multiple API calls
                    source = 'google-news-in' if country == 'in' else 'google-news'
                    self.api_calls_count += 1
                    source_articles = self._get_news_by_source(source, limit, from_date, to_date)
                    if source_articles:
                        all_articles.extend(source_articles)
                
                # If still not enough articles and we have API calls available, try with one keyword
                if len(all_articles) < limit and self.api_calls_count < self.max_api_calls:
                    # Use only one keyword to avoid multiple API calls
                    keyword = 'trending india news' if country == 'in' else 'trending news'
                    self.api_calls_count += 1
                    keyword_articles = self._get_news_by_keyword(keyword, limit, from_date, to_date)
                    if keyword_articles:
                        all_articles.extend(keyword_articles)
                
            except Exception as e:
                self.logger.error(f"Error fetching news: {str(e)}")
                # If there was an error, default to scraping Google News
                if not all_articles:
                    self.logger.info("Falling back to Google News scraper due to API error")
                    return self._scrape_google_news(limit=limit, country=country)
        
        # If we still don't have enough articles, fall back to Google News scraper
        if len(all_articles) < 5:
            self.logger.warning(f"Insufficient articles ({len(all_articles)}) - falling back to Google News scraper")
            scraped_articles = self._scrape_google_news(limit=limit, country=country)
            
            # Add scraped news but avoid duplicates
            existing_titles = [article.get('title', '').lower() for article in all_articles]
            for article in scraped_articles:
                if article.get('title', '').lower() not in existing_titles:
                    all_articles.append(article)
                    if len(all_articles) >= limit:
                        break
        
        # Filter duplicate articles based on title
        unique_articles = []
        seen_titles = set()
        for article in all_articles:
            title = article.get('title', '').lower()
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_articles.append(article)
        
        # Sort articles for relevance and return limited number
        sorted_articles = self._sort_by_popularity(unique_articles)
        result = sorted_articles[:limit]
        
        # Cache the result
        self.news_cache[cache_key] = {
            'timestamp': datetime.now().timestamp(),
            'articles': result
        }
        
        return result
    
    def _get_top_headlines_by_country(self, country='us', page_size=20, category=None):
        """Get top headlines by country and optional category."""
        try:
            params = {
                'country': country,
                'apiKey': self.api_key,
                'pageSize': page_size
            }
            
            # Add category parameter if specified
            if category:
                params['category'] = category
            
            self.logger.info(f"Fetching top headlines for country: {country}, category: {category}")
            response = requests.get(self.top_headlines_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                self.logger.info(f"Received {len(articles)} articles for country: {country}, category: {category}")
                return articles
            elif response.status_code == 429:
                self.logger.error(f"Rate limit exceeded for country {country}, category: {category}. Status: {response.status_code}, Response: {response.text}")
                # Raise the exception to be caught by the main method
                raise Exception(f"Rate limit exceeded: {response.text}")
            else:
                self.logger.error(f"Error fetching top headlines for {country}, category: {category}. Status: {response.status_code}, Response: {response.text}")
                return []
        except Exception as e:
            if "429" in str(e) or "rate limit" in str(e).lower():
                # Re-raise rate limit exceptions
                raise
            self.logger.error(f"Exception fetching top headlines for {country}, category: {category}: {str(e)}")
            return []
    
    def _get_news_by_source(self, source, page_size=20, from_date=None, to_date=None):
        """Get news by source."""
        try:
            params = {
                'sources': source,
                'apiKey': self.api_key,
                'pageSize': page_size,
                'sortBy': 'popularity'
            }
            
            # Add date filtering if provided
            if from_date:
                params['from'] = from_date
            if to_date:
                params['to'] = to_date
            
            self.logger.info(f"Fetching news from source: {source}")
            response = requests.get(self.everything_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"Received {len(data.get('articles', []))} articles from source: {source}")
                return data.get('articles', [])
            elif response.status_code == 429:
                self.logger.error(f"Rate limit exceeded for source {source}. Status: {response.status_code}, Response: {response.text}")
                # Raise the exception to be caught by the main method
                raise Exception(f"Rate limit exceeded: {response.text}")
            else:
                self.logger.error(f"Error fetching news from source {source}. Status: {response.status_code}, Response: {response.text}")
            return []
        except Exception as e:
            if "429" in str(e) or "rate limit" in str(e).lower():
                # Re-raise rate limit exceptions
                raise
            self.logger.error(f"Exception fetching news from source {source}: {str(e)}")
                return []
            
    def _get_news_by_keyword(self, keyword, page_size=20, from_date=None, to_date=None):
        """Get news by keyword."""
        try:
            params = {
                'q': keyword,
                'apiKey': self.api_key,
                'pageSize': page_size,
                'sortBy': 'popularity',
                'language': 'en'
            }
            
            # Add date filtering if provided
            if from_date:
                params['from'] = from_date
            if to_date:
                params['to'] = to_date
            
            self.logger.info(f"Fetching news for keyword: {keyword}")
            response = requests.get(self.everything_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"Received {len(data.get('articles', []))} articles for keyword: {keyword}")
                return data.get('articles', [])
            elif response.status_code == 429:
                self.logger.error(f"Rate limit exceeded for keyword {keyword}. Status: {response.status_code}, Response: {response.text}")
                # Raise the exception to be caught by the main method
                raise Exception(f"Rate limit exceeded: {response.text}")
            else:
                self.logger.error(f"Error fetching news for keyword {keyword}. Status: {response.status_code}, Response: {response.text}")
            return []
        except Exception as e:
            if "429" in str(e) or "rate limit" in str(e).lower():
                # Re-raise rate limit exceptions
                raise
            self.logger.error(f"Exception fetching news for keyword {keyword}: {str(e)}")
                return []
    
    def _filter_recent_articles(self, articles, days=14):
        """Filter articles to include only those published within the specified number of days."""
        filtered_articles = []
        for article in articles:
            if 'publishedAt' in article:
                try:
                    pub_date = datetime.strptime(article['publishedAt'][:10], '%Y-%m-%d')
                    if (datetime.now() - pub_date).days <= days:
                        filtered_articles.append(article)
                except (ValueError, TypeError):
                    # If date parsing fails, include the article anyway
                    filtered_articles.append(article)
            else:
                # Include articles without date
                filtered_articles.append(article)
        return filtered_articles
    
    def _sort_by_popularity(self, articles):
        """Sort articles by popularity indicators"""
        try:
            # Define a scoring function for popularity 
            def popularity_score(article):
                score = 0
                
                # Articles with images are prioritized
                if article.get("urlToImage"):
                    score += 10
                
                # Articles with content are prioritized
                if article.get("content"):
                    score += 5
                
                # Articles with descriptions are prioritized
                if article.get("description"):
                    score += 3
                
                # Recent articles get higher priority (up to 10 points)
                try:
                    published_at = article.get("publishedAt", "")
                    if published_at:
                        pub_date = datetime.strptime(published_at[:19], "%Y-%m-%dT%H:%M:%S")
                        days_old = (datetime.now() - pub_date).days
                        recency_score = max(0, 10 - days_old)  # 0 to 10 points based on recency
                        score += recency_score
                except (ValueError, TypeError):
                    pass
                
                # Premium sources get a boost
                premium_sources = ["bbc", "cnn", "reuters", "the-new-york-times", 
                                  "the-washington-post", "the-hindu", "the-times-of-india"]
                source_name = article.get("source", {}).get("name", "").lower()
                for premium in premium_sources:
                    if premium in source_name:
                        score += 5
                        break
                
                return score
            
            # Sort articles by descending popularity score
            sorted_articles = sorted(articles, key=popularity_score, reverse=True)
            return sorted_articles
        except Exception as e:
            self.logger.error(f"Error in _sort_by_popularity: {str(e)}")
            return articles  # Return original list on error
    
    def _simple_google_news_fallback(self, limit=20, country='in'):
        """Primary fallback using direct HTTP requests to Google News"""
        self.logger.info("Using HTTP-based Google News fallback")
        articles = []
        
        try:
            # Define URLs for different sections
            urls = []
            if country.lower() == 'in':
                urls = [
                    'https://news.google.com/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZxYUdjU0FtVnVHZ0pWVXlnQVAB?hl=en-IN&gl=IN&ceid=IN%3Aen',
                    'https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRGx1YlY4U0JXVnVMVWRDR2dKSlRpZ0FQAQ?hl=en-IN&gl=IN&ceid=IN%3Aen'
                ]
            else:
                urls = [f'https://news.google.com/?hl=en-{country.upper()}&gl={country.upper()}&ceid={country.upper()}%3Aen']
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            for url in urls:
                try:
                    response = requests.get(url, headers=headers, timeout=10)
                    response.raise_for_status()
                    
                    # Parse with BeautifulSoup
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Find all news article elements
                    article_elements = soup.find_all('article', {'class': 'MQsxIb'})
                    
                    for article in article_elements:
                        if len(articles) >= limit:
                            break
                            
                        try:
                            # Extract article information
                            title_element = article.find('h3')
                            link_element = article.find('a', {'class': 'VDXfz'})
                            time_element = article.find('time')
                            source_element = article.find('a', {'class': 'wEwyrc'})
                            
                            if not title_element or not link_element:
                                continue
                            
                            title = title_element.text.strip()
                            relative_url = link_element.get('href', '')
                            url = urljoin('https://news.google.com/', relative_url)
                            
                            # Get source
                            source = source_element.text.strip() if source_element else "Google News"
                            
                            # Get publication time
                            if time_element and time_element.get('datetime'):
                                pub_time = time_element['datetime']
                            else:
                                pub_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                            
                            # Create article object
                            article_obj = {
                                "id": len(articles) + 1,
                                "title": title,
                                "description": f"Click to read full article from {source}",
                                "content": title,
                                "url": url,
                                "source": source,
                                "publishedAt": pub_time,
                                "imageUrl": "https://news.google.com/favicon.ico"
                            }
                            
                            articles.append(article_obj)
                            
                        except Exception as e:
                            self.logger.error(f"Error parsing article: {str(e)}")
                            continue
                    
                except Exception as e:
                    self.logger.error(f"Error fetching URL {url}: {str(e)}")
                    continue
                
                if len(articles) >= limit:
                    break
            
            if not articles:
                # If HTTP requests fail, try web scraping
                return self._scrape_google_news(limit=limit, country=country)
            
            return articles
            
        except Exception as e:
            self.logger.error(f"Error with HTTP fallback: {str(e)}")
            # If HTTP requests fail, try web scraping
            return self._scrape_google_news(limit, country)
    
    def _scrape_google_news(self, limit=20, country='in'):
        """Secondary fallback using web scraping when HTTP requests fail"""
        self.logger.info(f"Scraping Google News for {country}")
        articles = []
        driver = None
        
        try:
            # Configure Chrome options for headless operation
            chrome_options = Options()
            chrome_options.add_argument("--headless=new")  # Use new headless mode
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-infobars")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--blink-settings=imagesEnabled=false")  # Disable images for faster loading
            
            # Set up User-Agent
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            chrome_options.add_argument(f'user-agent={user_agent}')
            
            # Initialize the Chrome driver with a page load timeout
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            driver.set_page_load_timeout(20)  # Set page load timeout to 20 seconds
            
            # Determine URL based on country
            if country.lower() == 'in':
                urls = [
                    'https://news.google.com/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZxYUdjU0FtVnVHZ0pWVXlnQVAB?hl=en-IN&gl=IN&ceid=IN%3Aen'
                ]
            else:
                urls = [f'https://news.google.com/?hl=en-{country.upper()}&gl={country.upper()}&ceid={country.upper()}%3Aen']
            
            for url in urls:
                try:
                    # Load the page with retry mechanism
                    max_retries = 3
                    for retry in range(max_retries):
                        try:
                            driver.get(url)
                            # Wait for content to load (max 10 seconds)
                            time.sleep(min(3 * (retry + 1), 10))
                            break
                        except Exception as e:
                            if retry == max_retries - 1:
                                raise
                            self.logger.warning(f"Retry {retry + 1} failed: {str(e)}")
                            continue
                    
                    # Get the page source
                    page_source = driver.page_source
                    
                    # Parse with BeautifulSoup using html5lib for better parsing
                    soup = BeautifulSoup(page_source, 'html5lib')
                    
                    # Find all news article elements
                    article_elements = soup.find_all(['article', 'div'], {'class': ['MQsxIb', 'IBr9hb']})
                    
                    for article in article_elements:
                        if len(articles) >= limit:
                            break
                            
                        try:
                            # Extract article information with multiple selectors
                            title_element = article.find(['h3', 'h4']) or article.find('a', {'class': 'DY5T1d'})
                            link_element = article.find('a', {'class': ['VDXfz', 'DY5T1d']})
                            time_element = article.find('time') or article.find('div', {'class': 'SVJrMe'})
                            source_element = article.find('a', {'class': ['wEwyrc', 'QmrVtf']})
                            
                            if not title_element or not link_element:
                                continue
                            
                            title = title_element.get_text().strip()
                            relative_url = link_element.get('href', '')
                            url = urljoin('https://news.google.com/', relative_url)
                            
                            # Get source
                            source = source_element.get_text().strip() if source_element else "Google News"
                            
                            # Get publication time
                            if time_element:
                                pub_time = time_element.get('datetime') or time_element.get_text()
                            else:
                                pub_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                            
                            # Create article object
                            article_obj = {
                                "id": len(articles) + 1,
                                "title": title,
                                "description": f"Click to read full article from {source}",
                                "content": title,
                                "url": url,
                                "source": source,
                                "publishedAt": pub_time,
                                "imageUrl": "https://news.google.com/favicon.ico"
                            }
                            
                            articles.append(article_obj)
                            
                        except Exception as e:
                            self.logger.error(f"Error parsing article: {str(e)}")
                            continue
                    
                except Exception as e:
                    self.logger.error(f"Error scraping URL {url}: {str(e)}")
                    continue
                
                if len(articles) >= limit:
                    break
            
            if not articles:
                # If scraping fails, use simple HTTP fallback
                return self._simple_google_news_fallback(limit, country)
            
            return articles
            
        except Exception as e:
            self.logger.error(f"Error with web scraping fallback: {str(e)}")
            # If scraping fails, use simple HTTP fallback
            return self._simple_google_news_fallback(limit, country)
            
        finally:
            # Always close the driver
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def _redirect_to_google_news(self, limit=20, country='in'):
        """Final fallback that redirects to Google News homepage"""
        self.logger.warning("All fallbacks failed - redirecting to Google News homepage")
        
        # Create a single article that redirects to Google News
        google_news_url = f"https://news.google.com/home?hl=en-{country.upper()}&gl={country.upper()}&ceid={country.upper()}:en"
        
        article = {
                "id": 1,
            "title": "Click here to read the latest news on Google News",
            "description": "We're experiencing technical difficulties. Click to visit Google News directly.",
            "content": "Redirecting to Google News...",
            "url": google_news_url,
            "source": "Google News",
            "publishedAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "imageUrl": "https://news.google.com/favicon.ico"
        }
        
        return [article]
    
    def filter_news_for_brand(self, news_articles, brand_keywords):
        """
        Filter news articles based on relevance to brand keywords
        
        Args:
            news_articles (list): List of news articles
            brand_keywords (list): Keywords related to the brand
            
        Returns:
            list: Filtered news articles relevant to the brand
        """
        if not brand_keywords or not news_articles:
            return news_articles
            
        filtered_articles = []
        
        for article in news_articles:
            # Convert everything to lowercase for case-insensitive matching
            title = article.get("title", "").lower()
            description = article.get("description", "").lower()
            content = article.get("content", "").lower()
            
            # Check if any keyword is in the article
            for keyword in brand_keywords:
                keyword = keyword.lower()
                if keyword in title or keyword in description or keyword in content:
                    filtered_articles.append(article)
                    break
        
        return filtered_articles 
