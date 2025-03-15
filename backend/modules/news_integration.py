import requests
import json
import logging
import os
from config import Config
from datetime import datetime, timedelta
import traceback

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
    
    def get_top_news(self, limit=20, days=14):
        """
        Get trending news articles.
        
        Parameters:
        - limit (int): Number of articles to return
        - days (int): Number of past days to include articles from (default: 14 days)
        
        Returns:
        - list: List of trending news articles
        """
        # Calculate the date range (from days ago to today)
        from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        to_date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"Fetching trending news from {from_date} to {to_date}, limit: {limit}")
        
        all_articles = []
        
        # Try to get top headlines first
        country_codes = ['us', 'gb', 'in']  # US, UK, India
        for country in country_codes:
            articles = self._get_top_headlines_by_country(country, limit)
            if articles:
                # Apply date filter post-retrieval for top headlines
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
                
                all_articles.extend(filtered_articles)
                
        # If not enough articles, try with specific sources
        if len(all_articles) < limit:
            sources = [
                'google-news', 'bbc-news', 'cnn', 'fox-news', 
                'the-verge', 'techcrunch', 'business-insider',
                'google-news-in', 'the-hindu', 'the-times-of-india'
            ]
            for source in sources:
                if len(all_articles) >= limit * 2:  # Get double the limit to allow for filtering
                    break
                source_articles = self._get_news_by_source(source, limit, from_date, to_date)
                if source_articles:
                    all_articles.extend(source_articles)
        
        # If still not enough articles, try with keywords
        if len(all_articles) < limit:
            keywords = ['trending', 'viral', 'popular', 'breaking news', 'latest']
            for keyword in keywords:
                if len(all_articles) >= limit * 2:  # Get double the limit to allow for filtering
                    break
                keyword_articles = self._get_news_by_keyword(keyword, limit, from_date, to_date)
                if keyword_articles:
                    all_articles.extend(keyword_articles)
        
        # Filter duplicate articles based on title
        unique_articles = []
        seen_titles = set()
        for article in all_articles:
            title = article.get('title', '').lower()
            if title and title not in seen_titles:
                seen_titles.add(title)
                
                # Filter by date if publishedAt is available
                if 'publishedAt' in article:
                    try:
                        pub_date = datetime.strptime(article['publishedAt'][:10], '%Y-%m-%d')
                        if (datetime.now() - pub_date).days > days:
                            continue
                    except (ValueError, TypeError):
                        # If date parsing fails, include the article anyway
                        pass
                
                unique_articles.append(article)
        
        # Sort articles by popularity indicators:
        # 1. Has an image
        # 2. Comes from a reputable source 
        # 3. More recent articles
        def sort_key(article):
            has_image = 1 if article.get('urlToImage') else 0
            
            # Check for reputable sources
            source = article.get('source', {}).get('name', '').lower()
            reputable_sources = ['bbc', 'cnn', 'nyt', 'washington post', 'guardian', 
                              'times', 'forbes', 'bloomberg', 'reuters', 'associated press']
            source_score = 0
            for reputable in reputable_sources:
                if reputable in source:
                    source_score = 1
                    break
            
            # Parse date for recency score
            recency_score = 0
            if 'publishedAt' in article:
                try:
                    pub_date = datetime.strptime(article['publishedAt'][:19], '%Y-%m-%dT%H:%M:%S')
                    # More recent = higher score (0-10 range)
                    days_old = (datetime.now() - pub_date).days
                    recency_score = max(0, 10 - days_old)
                except (ValueError, TypeError):
                    pass
            
            # Combined score gives priority to recent, reputable articles with images
            return (has_image, source_score, recency_score)
        
        # Sort articles by popularity indicators (descending order)
        unique_articles.sort(key=sort_key, reverse=True)
        
        # Return only the requested number of articles
        return unique_articles[:limit]
    
    def _get_top_headlines_by_country(self, country='us', page_size=20):
        """Get top headlines by country."""
        try:
            params = {
                'country': country,
                'apiKey': self.api_key,
                'pageSize': page_size
            }
            
            logger.info(f"Fetching top headlines for country: {country}")
            response = requests.get(self.top_headlines_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                logger.info(f"Received {len(articles)} articles for country: {country}")
                return articles
            else:
                logger.error(f"Error fetching top headlines for {country}. Status: {response.status_code}, Response: {response.text}")
                return []
        except Exception as e:
            logger.error(f"Exception fetching top headlines for {country}: {str(e)}")
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
            
            logger.info(f"Fetching news from source: {source}")
            response = requests.get(self.everything_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Received {len(data.get('articles', []))} articles from source: {source}")
                return data.get('articles', [])
            else:
                logger.error(f"Error fetching news from source {source}. Status: {response.status_code}, Response: {response.text}")
                return []
        except Exception as e:
            logger.error(f"Exception fetching news from source {source}: {str(e)}")
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
            
            logger.info(f"Fetching news for keyword: {keyword}")
            response = requests.get(self.everything_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Received {len(data.get('articles', []))} articles for keyword: {keyword}")
                return data.get('articles', [])
            else:
                logger.error(f"Error fetching news for keyword {keyword}. Status: {response.status_code}, Response: {response.text}")
                return []
        except Exception as e:
            logger.error(f"Exception fetching news for keyword {keyword}: {str(e)}")
            return []
    
    def _filter_recent_articles(self, articles, days=14):
        """Filter articles to get only those from the specified number of days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            filtered_articles = []
            
            for article in articles:
                published_at = article.get("publishedAt")
                if not published_at:
                    continue
                
                try:
                    article_date = datetime.strptime(published_at[:19], "%Y-%m-%dT%H:%M:%S")
                    if article_date >= cutoff_date:
                        filtered_articles.append(article)
                except (ValueError, TypeError):
                    # If we can't parse the date, still include the article
                    filtered_articles.append(article)
            
            self.logger.info(f"Filtered to {len(filtered_articles)} articles within the last {days} days")
            return filtered_articles
        except Exception as e:
            self.logger.error(f"Error in _filter_recent_articles: {str(e)}")
            return articles  # Return original list on error
    
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
    
    def _fetch_news_from_sources(self, country, limit, date_from=None):
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
                "pageSize": min(limit, 100),
                "sortBy": "popularity"  # Sort by popularity
            }
            
            # Add date filter if provided
            if date_from:
                params["from"] = date_from
            
            self.logger.info(f"Fetching news from sources: {source_ids}")
            
            response = requests.get(self.everything_url, params=params, timeout=10)
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
    
    def _fetch_news_by_keywords(self, country, limit, date_from=None):
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
                "language": "en",
                "sortBy": "popularity"  # Sort by popularity
            }
            
            # Add date filter if provided
            if date_from:
                params["from"] = date_from
            
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
        """Return sample news data when the API fails"""
        self.logger.warning("Returning sample news data")
        
        # Define some realistic sample news data
        sample_data = [
            {
                "id": 1,
                "title": "Tech Innovation Drives Economic Growth in 2024",
                "description": "Recent advances in AI and clean technology are creating new job opportunities across various sectors.",
                "content": "The rapid pace of technological innovation is reshaping global economies, with artificial intelligence and sustainable energy solutions leading the way. According to recent reports, these sectors are expected to generate millions of new jobs in the coming years.",
                "url": "https://example.com/tech-news-1",
                "source": "Tech Today",
                "publishedAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "imageUrl": "https://via.placeholder.com/300x200?text=Tech+News"
            },
            {
                "id": 2,
                "title": "Global Markets Respond to Policy Changes",
                "description": "Financial markets show resilience as central banks adjust interest rates to manage inflation.",
                "content": "Investors responded positively to recent monetary policy adjustments, with major indices showing growth despite ongoing economic challenges. Analysts suggest this indicates confidence in the long-term economic outlook.",
                "url": "https://example.com/finance-news-1",
                "source": "Financial Times",
                "publishedAt": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "imageUrl": "https://via.placeholder.com/300x200?text=Finance+News"
            },
            {
                "id": 3,
                "title": "Breakthrough in Renewable Energy Storage",
                "description": "Scientists develop new battery technology that could accelerate the adoption of renewable energy.",
                "content": "A team of researchers has announced a significant advancement in energy storage capabilities, potentially solving one of the biggest challenges in renewable energy adoption. The new technology offers longer lifespan and higher efficiency than current solutions.",
                "url": "https://example.com/science-news-1",
                "source": "Science Daily",
                "publishedAt": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "imageUrl": "https://via.placeholder.com/300x200?text=Science+News"
            },
            {
                "id": 4,
                "title": "Consumer Trends Shift Toward Sustainable Products",
                "description": "Market research indicates growing consumer preference for environmentally friendly options.",
                "content": "Recent studies show that consumers are increasingly making purchasing decisions based on sustainability factors. This trend is particularly pronounced among younger demographics, driving companies to adapt their product offerings and supply chains.",
                "url": "https://example.com/business-news-1",
                "source": "Business Insider",
                "publishedAt": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "imageUrl": "https://via.placeholder.com/300x200?text=Business+News"
            },
            {
                "id": 5,
                "title": "Healthcare Innovations Address Global Challenges",
                "description": "New medical technologies provide solutions for aging populations and underserved communities.",
                "content": "Healthcare providers are implementing cutting-edge technologies to extend care to previously underserved regions and address the unique needs of aging populations. These innovations range from telemedicine platforms to advanced diagnostic tools that can be deployed in resource-limited settings.",
                "url": "https://example.com/health-news-1",
                "source": "Health Monthly",
                "publishedAt": (datetime.now() - timedelta(days=4)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "imageUrl": "https://via.placeholder.com/300x200?text=Health+News"
            }
        ]
        
        return sample_data
    
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