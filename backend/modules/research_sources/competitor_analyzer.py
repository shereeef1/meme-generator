import logging
import re
import time
import random
from .search_integration import DuckDuckGoSearch

logger = logging.getLogger(__name__)

class CompetitorAnalyzer:
    """
    Class for identifying and analyzing competitors of a brand.
    Uses search results to find and analyze competitors.
    """
    
    def __init__(self):
        self.search = DuckDuckGoSearch()
    
    def identify_competitors(self, brand_name, category=None):
        """
        Identify competitors of a brand based on search results
        
        Args:
            brand_name (str): The name of the brand to research
            category (str, optional): The brand category for more specific results
            
        Returns:
            dict: Competitor analysis results
        """
        try:
            logger.info(f"Identifying competitors for: {brand_name}")
            
            # Create search queries for finding competitors
            queries = [
                f"{brand_name} competitors",
                f"{brand_name} alternatives",
                f"{brand_name} vs",
            ]
            
            if category:
                queries.append(f"top {category} brands like {brand_name}")
                queries.append(f"best {category} companies")
            
            # Get search results
            all_results = []
            sources = []
            competitor_mentions = {}
            
            for query in queries:
                # Add random delay to avoid rate limiting
                time.sleep(random.uniform(1, 2))
                
                results = self.search._search_duckduckgo(query, max_results=5)
                
                for result in results:
                    # Add to our sources if not already present
                    if not any(s["url"] == result["url"] for s in sources):
                        sources.append({"type": "search", "url": result["url"], "query": query})
                        all_results.append(result)
                    
                    # Extract potential competitor names from title and snippet
                    content = f"{result['title']} {result['snippet']}".lower()
                    
                    # Look for "X vs Y" patterns
                    vs_matches = re.findall(rf"{brand_name.lower()}\s+vs\s+([a-z0-9\s]+)", content)
                    vs_matches += re.findall(rf"([a-z0-9\s]+)\s+vs\s+{brand_name.lower()}", content)
                    
                    for match in vs_matches:
                        competitor = match.strip()
                        if competitor and competitor != brand_name.lower():
                            competitor_mentions[competitor] = competitor_mentions.get(competitor, 0) + 3
                    
                    # Look for "alternatives to X" patterns
                    alt_matches = re.findall(r"alternatives\s+to[:\s]+([^,\.]+)", content)
                    for match in alt_matches:
                        competitor = match.strip()
                        if competitor and competitor != brand_name.lower():
                            competitor_mentions[competitor] = competitor_mentions.get(competitor, 0) + 2
                    
                    # Look for "X, Y, and Z are competitors" patterns
                    list_matches = re.findall(r"([a-z0-9\s,]+(?:and|&)[a-z0-9\s]+)", content)
                    for match in list_matches:
                        items = [item.strip() for item in re.split(r',|\sand\s|\s&\s', match)]
                        for item in items:
                            if item and item != brand_name.lower():
                                competitor_mentions[item] = competitor_mentions.get(item, 0) + 1
            
            # Sort competitors by number of mentions
            sorted_competitors = sorted(competitor_mentions.items(), key=lambda x: x[1], reverse=True)
            top_competitors = [{"name": name, "mentions": count} for name, count in sorted_competitors[:10]]
            
            # Create the text representation
            combined_text = f"Competitor Analysis for {brand_name}:\n\n"
            
            if top_competitors:
                combined_text += "Top Competitors:\n"
                for i, comp in enumerate(top_competitors, 1):
                    combined_text += f"{i}. {comp['name']} (Mentions: {comp['mentions']})\n"
            else:
                combined_text += f"No clear competitors found for {brand_name}\n"
            
            # Add some search result excerpts
            if all_results:
                combined_text += "\nCompetitor References:\n"
                for result in all_results[:5]:
                    combined_text += f"- {result['title']}: {result['snippet']}\n"
            
            logger.info(f"Found {len(top_competitors)} potential competitors for {brand_name}")
            
            return {
                "success": True,
                "competitors": top_competitors,
                "sources": sources[:10],
                "text": combined_text,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Error identifying competitors for {brand_name}: {e}")
            return {
                "success": False,
                "competitors": [],
                "sources": [],
                "text": "",
                "error": str(e)
            } 