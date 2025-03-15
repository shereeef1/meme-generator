import requests
import json
import logging
import os
from config import Config

# Set up a file handler for detailed logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'news_api.log')

# Configure file logging
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# Get the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)

class NewsIntegration:
    """Class to fetch and filter trending news for brands"""
    
    def __init__(self):
        self.api_key = Config.NEWS_API_KEY
        self.top_headlines_url = "https://newsapi.org/v2/top-headlines"
        self.everything_url = "https://newsapi.org/v2/everything"
        self.logger = logger
        
        # Log API key existence for debugging
        if self.api_key:
            self.logger.info(f"NewsAPI key is configured: {self.api_key[:4]}...{self.api_key[-4:] if len(self.api_key) > 8 else 'too_short'}")
        else:
            self.logger.error("NewsAPI key is not configured!")
            
        # Log the config values for debugging
        self.logger.debug(f"NEWS_API_KEY from Config: {self.api_key}")
    
    def get_top_news(self, country="in", limit=20):
        """
        Fetch top news from NewsAPI from multiple sources
        
        Args:
            country (str): Country code for news (default: "in" for India)
            limit (int): Maximum number of news articles to return
            
        Returns:
            list: List of news articles formatted for the frontend
        """
        articles = []
        
        try:
            # Check if API key is configured
            if not self.api_key:
                self.logger.error("Cannot fetch news: NewsAPI key is not configured")
                return self._get_sample_news()
            
            # First try from top headlines by country
            country_articles = self._fetch_top_headlines_by_country(country, limit)
            articles.extend(country_articles)
            
            # If we don't have enough articles, try sources from that country
            if len(articles) < limit:
                source_articles = self._fetch_news_from_sources(country, limit - len(articles))
                articles.extend(source_articles)
            
            # If we still don't have enough articles, try a keyword search
            if len(articles) < limit:
                keyword_articles = self._fetch_news_by_keywords(country, limit - len(articles))
                articles.extend(keyword_articles)
            
            # If we still don't have articles, try global news
            if not articles:
                self.logger.info(f"No articles found for country {country}, trying global news...")
                global_articles = self._fetch_top_headlines_by_country("us", limit)
                articles.extend(global_articles)
            
            # Still nothing? Return sample data
            if not articles:
                self.logger.warning("No articles found from any source, returning sample data")
                return self._get_sample_news()
            
            self.logger.info(f"Total articles collected: {len(articles)}")
            
            # Format and return articles
            formatted_articles = []
            for idx, article in enumerate(articles[:limit]):
                formatted_articles.append({
                    "id": idx + 1,
                    "title": article.get("title", "No Title"),
                    "description": article.get("description", "No Description"),
                    "content": article.get("content", "No Content"),
                    "url": article.get("url", ""),
                    "source": article.get("source", {}).get("name", "Unknown Source"),
                    "publishedAt": article.get("publishedAt", ""),
                    "imageUrl": article.get("urlToImage", "")
                })
            
            return formatted_articles
            
        except Exception as e:
            self.logger.error(f"Unexpected error in get_top_news: {str(e)}")
            return self._get_sample_news()
    
    def _fetch_top_headlines_by_country(self, country, limit):
        """Fetch top headlines for a specific country"""
        try:
            params = {
                "country": country,
                "apiKey": self.api_key,
                "pageSize": min(limit, 100)  # API limit is 100
            }
            
            self.logger.info(f"Fetching top headlines for country: {country}, limit: {limit}")
            
            response = requests.get(self.top_headlines_url, params=params, timeout=10)
            self.logger.info(f"Top headlines response status: {response.status_code}")
            
            if response.status_code != 200:
                self.logger.error(f"Error fetching top headlines: {response.status_code} - {response.text}")
                return []
            
            data = response.json()
            articles = data.get("articles", [])
            self.logger.info(f"Received {len(articles)} top headline articles for {country}")
            
            return articles
        except Exception as e:
            self.logger.error(f"Error in _fetch_top_headlines_by_country: {str(e)}")
            return []
    
    def _fetch_news_from_sources(self, country, limit):
        """Fetch news from sources in a specific country"""
        try:
            # First get sources from the country
            sources_url = "https://newsapi.org/v2/sources"
            sources_params = {
                "country": country,
                "apiKey": self.api_key
            }
            
            self.logger.info(f"Fetching sources for country: {country}")
            
            sources_response = requests.get(sources_url, params=sources_params, timeout=10)
            if sources_response.status_code != 200:
                self.logger.error(f"Error fetching sources: {sources_response.status_code} - {sources_response.text}")
                return []
            
            sources_data = sources_response.json()
            sources = sources_data.get("sources", [])
            
            if not sources:
                self.logger.warning(f"No sources found for country {country}")
                return []
            
            # Get a comma-separated list of source IDs
            # Prioritize specific Indian news sources
            priority_sources = ["google-news-in", "the-hindu", "ndtv", "the-times-of-india"]
            available_sources = [source.get("id") for source in sources]
            
            # Filter to get available priority sources
            filtered_sources = [s for s in priority_sources if s in available_sources]
            
            # Add other sources if we don't have enough priority sources
            if len(filtered_sources) < 5:
                remaining_sources = [s for s in available_sources if s not in filtered_sources]
                filtered_sources.extend(remaining_sources[:5-len(filtered_sources)])
            
            source_ids = ",".join(filtered_sources[:5])  # Limit to 5 sources
            
            # Now fetch articles from these sources
            params = {
                "sources": source_ids,
                "apiKey": self.api_key,
                "pageSize": min(limit, 100)
            }
            
            self.logger.info(f"Fetching news from sources: {source_ids}")
            
            response = requests.get(self.top_headlines_url, params=params, timeout=10)
            if response.status_code != 200:
                self.logger.error(f"Error fetching news from sources: {response.status_code} - {response.text}")
                return []
            
            data = response.json()
            raw_articles = data.get("articles", [])
            self.logger.info(f"Received {len(raw_articles)} articles from country sources")
            
            # Process Google News articles to make them more meaningful
            processed_articles = []
            generic_google_news_count = 0
            
            for article in raw_articles:
                # Skip duplicate "Google News" titles or limit them to 2
                if article.get("title") == "Google News":
                    if generic_google_news_count >= 2:
                        continue
                    # Try to extract a better title from the URL or description
                    description = article.get("description", "")
                    if description and description != "Comprehensive up-to-date news coverage, aggregated from sources all over the world by Google News.":
                        # Use the first sentence of the description as the title
                        first_sentence = description.split('.')[0] + "."
                        article["title"] = first_sentence if len(first_sentence) > 10 else "India News Update"
                    else:
                        article["title"] = f"India News Update {generic_google_news_count + 1}"
                    
                    # Add India context to generic description
                    if article.get("description") == "Comprehensive up-to-date news coverage, aggregated from sources all over the world by Google News.":
                        article["description"] = "Latest news updates from across India, covering politics, business, technology and current affairs."
                    
                    # Add a more meaningful content snippet
                    if article.get("content") == "Comprehensive up-to-date news coverage, aggregated from sources all over the world by Google News.":
                        article["content"] = "Stay updated with the latest news from India. Click through to read the full article from Google News."
                    
                    generic_google_news_count += 1
                
                processed_articles.append(article)
            
            return processed_articles
            
        except Exception as e:
            self.logger.error(f"Error in _fetch_news_from_sources: {str(e)}")
            return []
    
    def _fetch_news_by_keywords(self, country, limit):
        """Fetch news by keywords related to the country"""
        try:
            # Define keywords based on country
            country_keywords = {
                "in": "India OR Delhi OR Mumbai OR Bangalore",
                "us": "USA OR America OR Washington OR New York",
                # Add more countries as needed
            }
            
            query = country_keywords.get(country.lower(), country)
            
            params = {
                "q": query,
                "apiKey": self.api_key,
                "pageSize": min(limit, 100),
                "language": "en"
            }
            
            self.logger.info(f"Fetching news by keywords: {query}")
            
            response = requests.get(self.everything_url, params=params, timeout=10)
            if response.status_code != 200:
                self.logger.error(f"Error fetching news by keywords: {response.status_code} - {response.text}")
                return []
            
            data = response.json()
            articles = data.get("articles", [])
            self.logger.info(f"Received {len(articles)} articles from keyword search")
            
            return articles
        except Exception as e:
            self.logger.error(f"Error in _fetch_news_by_keywords: {str(e)}")
            return []
    
    def _get_sample_news(self):
        """Return sample news data when API fails"""
        return [
            {
                "id": 1,
                "title": "Sample News Article 1",
                "description": "This is a sample news article description.",
                "content": "This is sample content for news article 1.",
                "url": "https://example.com/news/1",
                "source": "Sample News",
                "publishedAt": "2023-05-01T12:00:00Z",
                "imageUrl": "https://via.placeholder.com/450x200"
            },
            {
                "id": 2,
                "title": "Sample News Article 2",
                "description": "This is another sample news article description.",
                "content": "This is sample content for news article 2.",
                "url": "https://example.com/news/2",
                "source": "Sample News",
                "publishedAt": "2023-05-01T10:30:00Z",
                "imageUrl": "https://via.placeholder.com/450x200"
            },
            {
                "id": 3,
                "title": "Sample Technology News",
                "description": "This is a sample technology news article.",
                "content": "This is sample content about technology advancements.",
                "url": "https://example.com/news/3",
                "source": "Tech News",
                "publishedAt": "2023-05-02T09:15:00Z", 
                "imageUrl": "https://via.placeholder.com/450x200"
            },
            {
                "id": 4,
                "title": "Sample Business Update",
                "description": "This is a sample business news article.",
                "content": "This is sample content about business trends.",
                "url": "https://example.com/news/4",
                "source": "Business Daily",
                "publishedAt": "2023-05-03T14:30:00Z",
                "imageUrl": "https://via.placeholder.com/450x200"
            },
            {
                "id": 5,
                "title": "Sample Health News",
                "description": "This is a sample health news article.",
                "content": "This is sample content about health discoveries.",
                "url": "https://example.com/news/5",
                "source": "Health Times",
                "publishedAt": "2023-05-04T11:45:00Z",
                "imageUrl": "https://via.placeholder.com/450x200"
            }
        ]
    
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