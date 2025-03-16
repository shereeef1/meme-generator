import logging
import re
import time
import random
from .search_integration import DuckDuckGoSearch
from collections import Counter
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TrendDetector:
    """
    Class for detecting current trends in an industry or related to a brand.
    Uses search results to identify trending topics.
    """
    
    def __init__(self):
        self.search = DuckDuckGoSearch()
        
        # Common words to exclude from trend analysis
        self.stop_words = set([
            "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "as", "at", 
            "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can", "did", "do", 
            "does", "doing", "don", "down", "during", "each", "few", "for", "from", "further", "had", "has", "have", 
            "having", "he", "her", "here", "hers", "herself", "him", "himself", "his", "how", "i", "if", "in", "into", 
            "is", "it", "its", "itself", "just", "me", "more", "most", "my", "myself", "no", "nor", "not", "now", "of", 
            "off", "on", "once", "only", "or", "other", "our", "ours", "ourselves", "out", "over", "own", "s", "same", 
            "she", "should", "so", "some", "such", "t", "than", "that", "the", "their", "theirs", "them", "themselves", 
            "then", "there", "these", "they", "this", "those", "through", "to", "too", "under", "until", "up", "very", 
            "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom", "why", "will", "with", 
            "you", "your", "yours", "yourself", "yourselves"
        ])
    
    def _extract_date_clues(self, text):
        """
        Extract date clues from text to determine recency
        
        Args:
            text (str): Text to analyze
            
        Returns:
            datetime or None: Estimated date if found
        """
        today = datetime.now()
        
        # Look for explicit dates
        date_patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',  # 01/01/2023, 1-1-23
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (\d{1,2})(?:st|nd|rd|th)?,? (\d{4})',  # January 1st, 2023
            r'(\d{1,2})(?:st|nd|rd|th)? (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (\d{4})'  # 1st January, 2023
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    # Try to parse the date
                    # This is simplified handling - in real code we'd have more robust date parsing
                    return today
                except:
                    pass
        
        # Look for relative time expressions
        if re.search(r'today|tonight|this morning', text, re.IGNORECASE):
            return today
        elif re.search(r'yesterday', text, re.IGNORECASE):
            return today - timedelta(days=1)
        elif re.search(r'this week', text, re.IGNORECASE):
            return today - timedelta(days=3)
        elif re.search(r'last week', text, re.IGNORECASE):
            return today - timedelta(days=7)
        elif re.search(r'this month', text, re.IGNORECASE):
            return today - timedelta(days=15)
        elif re.search(r'last month', text, re.IGNORECASE):
            return today - timedelta(days=30)
        
        return None
    
    def _extract_phrases(self, text, min_length=2, max_length=4):
        """
        Extract potentially meaningful phrases from text
        
        Args:
            text (str): Text to analyze
            min_length (int): Minimum words in a phrase
            max_length (int): Maximum words in a phrase
            
        Returns:
            Counter: Phrases with their frequencies
        """
        # Clean text
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        
        # Remove stop words
        filtered_words = [word for word in words if word not in self.stop_words and len(word) > 2]
        
        phrases = Counter()
        
        # Extract phrases of different lengths
        for length in range(min_length, min(max_length + 1, len(filtered_words))):
            for i in range(len(filtered_words) - length + 1):
                phrase = " ".join(filtered_words[i:i+length])
                phrases[phrase] += 1
        
        return phrases
    
    def detect_trends(self, brand_name, category=None):
        """
        Detect trends related to a brand or its industry
        
        Args:
            brand_name (str): The name of the brand to research
            category (str, optional): The brand category for more specific results
            
        Returns:
            dict: Trend analysis results
        """
        try:
            logger.info(f"Detecting trends for brand: {brand_name}, category: {category}")
            
            # Create search queries for trending topics
            queries = [
                f"{brand_name} trends",
                f"{brand_name} latest news",
                f"{brand_name} innovation"
            ]
            
            if category:
                queries.append(f"{category} industry trends")
                queries.append(f"{category} latest developments")
                queries.append(f"trends in {category} market")
            
            all_results = []
            sources = []
            all_text = ""
            trend_phrases = Counter()
            
            for query in queries:
                # Add random delay to avoid rate limiting
                time.sleep(random.uniform(1, 2))
                
                results = self.search._search_duckduckgo(query, max_results=5)
                
                for result in results:
                    # Check if we already have this result
                    if not any(r["url"] == result["url"] for r in all_results):
                        # Get the date clues from the snippet
                        date_estimate = self._extract_date_clues(result["snippet"])
                        
                        result["date_estimate"] = date_estimate
                        result["recency_score"] = 1
                        
                        # Boost score for recent content
                        if date_estimate:
                            days_ago = (datetime.now() - date_estimate).days
                            if days_ago < 7:
                                result["recency_score"] = 3
                            elif days_ago < 30:
                                result["recency_score"] = 2
                        
                        all_results.append(result)
                        sources.append({"type": "search", "url": result["url"], "query": query})
                        
                        # Extract phrases from title and snippet
                        content = f"{result['title']} {result['snippet']}"
                        all_text += content + " "
                        
                        # Extract meaningful phrases
                        phrases = self._extract_phrases(content)
                        for phrase, count in phrases.items():
                            trend_phrases[phrase] += count * result["recency_score"]
            
            # Get the top trend phrases
            top_phrases = trend_phrases.most_common(15)
            
            # Filter out brand name and category to focus on actual trends
            trends = []
            brand_words = set(brand_name.lower().split())
            category_words = set(category.lower().split()) if category else set()
            exclusion_set = brand_words.union(category_words)
            
            for phrase, score in top_phrases:
                # Check if the phrase is just the brand name or category
                phrase_words = set(phrase.split())
                if not phrase_words.issubset(exclusion_set) and score > 1:
                    trends.append({"phrase": phrase, "score": score})
            
            # Prepare the text representation
            combined_text = f"Trend Analysis for {brand_name}"
            if category:
                combined_text += f" in {category} industry"
            combined_text += ":\n\n"
            
            if trends:
                combined_text += "Top Trending Topics:\n"
                for i, trend in enumerate(trends[:10], 1):
                    combined_text += f"{i}. {trend['phrase']} (Relevance Score: {trend['score']})\n"
            else:
                combined_text += f"No clear trends found for {brand_name}\n"
            
            # Add some recent news excerpts
            if all_results:
                # Sort by recency
                recent_results = sorted(all_results, key=lambda x: x.get("recency_score", 0), reverse=True)
                
                combined_text += "\nRecent Developments:\n"
                for result in recent_results[:5]:
                    combined_text += f"- {result['title']}: {result['snippet']}\n"
            
            logger.info(f"Found {len(trends)} potential trends for {brand_name}")
            
            return {
                "success": True,
                "trends": trends[:10],
                "sources": sources[:10],
                "text": combined_text,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Error detecting trends for {brand_name}: {e}")
            return {
                "success": False,
                "trends": [],
                "sources": [],
                "text": "",
                "error": str(e)
            } 