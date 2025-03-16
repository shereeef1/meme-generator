import logging
import os
import time
import traceback
import uuid
from datetime import datetime

# Set up logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'enhanced_research.log')

# Configure file logging
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# Get the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)

class EnhancedResearch:
    """
    Class to coordinate enhanced brand research from multiple sources:
    - Wikipedia data
    - DuckDuckGo search results
    - Direct website scraping
    - Competitor information
    - Industry trends
    """
    
    def __init__(self, brand_scraper=None, news_integration=None, document_manager=None):
        """
        Initialize the EnhancedResearch coordinator
        
        Args:
            brand_scraper: Existing BrandScraper instance
            news_integration: Existing NewsIntegration instance
            document_manager: Existing DocumentManager instance
        """
        self.logger = logger
        self.brand_scraper = brand_scraper
        self.news_integration = news_integration
        self.document_manager = document_manager
        
        # Import source-specific scrapers
        from .research_sources.wikipedia_scraper import WikipediaScraper
        from .research_sources.search_integration import DuckDuckGoSearch
        from .research_sources.competitor_analyzer import CompetitorAnalyzer
        from .research_sources.trend_detector import TrendDetector
        from .research_sources.website_scraper import WebsiteScraper
        
        # Initialize source-specific scrapers
        self.wikipedia_scraper = WikipediaScraper()
        self.search_integration = DuckDuckGoSearch()
        self.competitor_analyzer = CompetitorAnalyzer()
        self.trend_detector = TrendDetector()
        self.website_scraper = WebsiteScraper()
    
    def research_brand(self, brand_name, category=None, country=None, include_competitors=True, include_trends=True):
        """
        Perform comprehensive brand research using multiple sources
        
        Args:
            brand_name (str): Name of the brand to research
            category (str, optional): Brand category
            country (str, optional): Brand's primary market
            include_competitors (bool): Whether to include competitor analysis
            include_trends (bool): Whether to include industry trend analysis
            
        Returns:
            dict: Comprehensive brand research results
        """
        start_time = time.time()
        self.logger.info(f"Starting enhanced research for brand: {brand_name}")
        
        # Initialize results dictionary
        results = {
            "success": True,
            "brand_name": brand_name,
            "category": category,
            "country": country,
            "source_type": "enhanced_research",
            "source_url": f"Enhanced Research: {brand_name}",
            "timestamp": datetime.now().isoformat(),
            "basic_info": {},
            "competitors": [],
            "industry_trends": [],
            "sources": [],
            "raw_text": "",
            "partial_failures": []
        }
        
        # Track if we have any successful data sources
        any_source_successful = False
        
        try:
            # 1. Get Wikipedia data
            self.logger.info(f"Fetching Wikipedia data for {brand_name}")
            try:
                wikipedia_data = self.wikipedia_scraper.scrape_wikipedia(brand_name)
                
                if wikipedia_data["success"]:
                    results["basic_info"]["wikipedia"] = wikipedia_data["data"]
                    results["sources"].append({"type": "wikipedia", "url": wikipedia_data["url"]})
                    results["raw_text"] += f"\n\n=== WIKIPEDIA INFORMATION ===\n{wikipedia_data['text']}"
                    any_source_successful = True
                else:
                    results["partial_failures"].append({
                        "source": "wikipedia",
                        "error": wikipedia_data.get("error", "Unknown error")
                    })
                    self.logger.warning(f"Wikipedia scraping failed for {brand_name}: {wikipedia_data.get('error', 'Unknown error')}")
            except Exception as e:
                self.logger.error(f"Exception during Wikipedia scraping for {brand_name}: {str(e)}")
                results["partial_failures"].append({
                    "source": "wikipedia",
                    "error": str(e)
                })
            
            # 2. Get DuckDuckGo search results for the official website URL
            # We'll do this first to use the website URL for direct scraping if possible
            official_website_url = None
            self.logger.info(f"Performing initial DuckDuckGo search for {brand_name} official website")
            try:
                # Only search for the official website without creating a full section yet
                official_website_query = f"{brand_name} official website"
                website_results = self.search_integration.search_brand(official_website_query, max_results=3)
                
                # Look for the most likely official website in the results
                if website_results.get("results"):
                    for result in website_results["results"]:
                        url = result.get("url", "").lower()
                        title = result.get("title", "").lower()
                        
                        # Check if this is likely the official site
                        brand_terms = brand_name.lower().split()
                        if any(term in url for term in brand_terms) and not any(term in url for term in ["wikipedia", "linkedin", "facebook", "twitter"]):
                            official_website_url = result["url"]
                            self.logger.info(f"Found likely official website: {official_website_url}")
                            break
            except Exception as e:
                self.logger.error(f"Exception during initial website search for {brand_name}: {str(e)}")
                # Continue with the process - we'll still try other approaches
            
            # 3. Try direct website scraping if we found a URL
            if official_website_url:
                self.logger.info(f"Attempting direct website scraping for {brand_name} at {official_website_url}")
                try:
                    website_data = self.website_scraper.scrape_brand_website(official_website_url, brand_name)
                    
                    if website_data["success"]:
                        results["basic_info"]["website"] = website_data["data"]
                        results["sources"].append({"type": "website", "url": website_data["url"]})
                        results["raw_text"] += f"\n\n=== WEBSITE INFORMATION ===\n{website_data['text']}"
                        any_source_successful = True
                    else:
                        results["partial_failures"].append({
                            "source": "website",
                            "error": website_data.get("error", "Unknown error")
                        })
                        self.logger.warning(f"Website scraping failed for {brand_name}: {website_data.get('error', 'Unknown error')}")
                except Exception as e:
                    self.logger.error(f"Exception during website scraping for {brand_name}: {str(e)}")
                    results["partial_failures"].append({
                        "source": "website",
                        "error": str(e)
                    })
            
            # 4. Get DuckDuckGo search results (as a fallback or additional information)
            self.logger.info(f"Performing comprehensive DuckDuckGo search for {brand_name}")
            try:
                search_results = self.search_integration.search_brand(brand_name)
                
                if search_results.get("success", False) and search_results.get("results"):
                    results["basic_info"]["search_results"] = search_results["results"]
                    results["sources"].extend(search_results.get("sources", []))
                    results["raw_text"] += f"\n\n=== SEARCH RESULTS ===\n{search_results.get('text', '')}"
                    any_source_successful = True
                else:
                    # Check if this failed due to rate limiting
                    if any("rate limiting" in f.get("error", "") for f in search_results.get("partial_failures", [])):
                        self.logger.warning(f"DuckDuckGo search rate limited for {brand_name}")
                        
                        # If we have at least some results, include what we could get
                        if search_results.get("results") and len(search_results["results"]) > 0:
                            results["basic_info"]["search_results"] = search_results["results"]
                            results["sources"].extend(search_results.get("sources", []))
                            results["raw_text"] += f"\n\n=== SEARCH RESULTS (Partial) ===\n{search_results.get('text', '')}"
                            any_source_successful = True
                    
                    results["partial_failures"].append({
                        "source": "search",
                        "error": search_results.get("error", "Unknown error")
                    })
                    self.logger.warning(f"Search scraping failed for {brand_name}: {search_results.get('error', 'Unknown error')}")
            except Exception as e:
                self.logger.error(f"Exception during search scraping for {brand_name}: {str(e)}")
                results["partial_failures"].append({
                    "source": "search",
                    "error": str(e)
                })
            
            # 5. Get competitor information (if requested)
            if include_competitors:
                self.logger.info(f"Analyzing competitors for {brand_name}")
                try:
                    competitor_results = self.competitor_analyzer.identify_competitors(brand_name, category)
                    
                    if competitor_results.get("success", False) and competitor_results.get("competitors"):
                        results["competitors"] = competitor_results["competitors"]
                        results["sources"].extend(competitor_results.get("sources", []))
                        results["raw_text"] += f"\n\n=== COMPETITOR ANALYSIS ===\n{competitor_results.get('text', '')}"
                        any_source_successful = True
                    else:
                        # For DuckDuckGo rate limiting, provide a fallback message
                        if "DuckDuckGo returned 202 status" in str(competitor_results.get("error", "")):
                            results["raw_text"] += f"\n\n=== COMPETITOR ANALYSIS ===\nCompetitor Analysis for {brand_name}:\n\nNo clear competitors found for {brand_name}\n"
                        
                        results["partial_failures"].append({
                            "source": "competitors",
                            "error": competitor_results.get("error", "Unknown error")
                        })
                        self.logger.warning(f"Competitor analysis failed for {brand_name}: {competitor_results.get('error', 'Unknown error')}")
                except Exception as e:
                    self.logger.error(f"Exception during competitor analysis for {brand_name}: {str(e)}")
                    results["partial_failures"].append({
                        "source": "competitors",
                        "error": str(e)
                    })
            
            # 6. Get industry trends (if requested)
            if include_trends:
                self.logger.info(f"Detecting industry trends for {category or brand_name}")
                try:
                    trend_results = self.trend_detector.detect_trends(brand_name, category)
                    
                    if trend_results.get("success", False) and trend_results.get("trends"):
                        results["industry_trends"] = trend_results["trends"]
                        results["sources"].extend(trend_results.get("sources", []))
                        results["raw_text"] += f"\n\n=== INDUSTRY TRENDS ===\n{trend_results.get('text', '')}"
                        any_source_successful = True
                    else:
                        # For DuckDuckGo rate limiting, provide a fallback message
                        if "DuckDuckGo returned 202 status" in str(trend_results.get("error", "")):
                            results["raw_text"] += f"\n\n=== INDUSTRY TRENDS ===\nTrend Analysis for {brand_name}:\n\nNo clear trends found for {brand_name}\n"
                        
                        results["partial_failures"].append({
                            "source": "trends",
                            "error": trend_results.get("error", "Unknown error")
                        })
                        self.logger.warning(f"Trend detection failed for {brand_name}: {trend_results.get('error', 'Unknown error')}")
                except Exception as e:
                    self.logger.error(f"Exception during trend detection for {brand_name}: {str(e)}")
                    results["partial_failures"].append({
                        "source": "trends",
                        "error": str(e)
                    })
            
            # 7. As a fallback, try to search directly for information if everything else failed
            if not any_source_successful and official_website_url:
                # Try direct scraping of gokwik.co website as a fallback
                self.logger.info(f"Using fallback direct website scraping for {official_website_url}")
                try:
                    generic_url = f"www.{brand_name.lower().replace(' ', '')}.com"
                    website_data = self.website_scraper.scrape_brand_website(generic_url, brand_name)
                    
                    if website_data["success"]:
                        results["basic_info"]["website"] = website_data["data"]
                        results["sources"].append({"type": "website", "url": website_data["url"]})
                        results["raw_text"] += f"\n\n=== WEBSITE INFORMATION ===\n{website_data['text']}"
                        any_source_successful = True
                except Exception as e:
                    self.logger.error(f"Exception during fallback website scraping for {brand_name}: {str(e)}")
                    # This is a fallback so we don't need to add to partial_failures
            
            # If we've got at least one successful source, consider the operation successful
            if any_source_successful:
                results["success"] = True
                
                # If we have partial failures, add a warning message
                if results["partial_failures"]:
                    failed_sources = [f["source"] for f in results["partial_failures"]]
                    results["warning"] = f"Some data sources failed: {', '.join(failed_sources)}. Results may be incomplete."
                    self.logger.warning(f"Partial failures in enhanced research for {brand_name}: {failed_sources}")
                
                # Generate a unique document ID for storage
                doc_id = str(uuid.uuid4().hex)[:8]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{brand_name.lower().replace(' ', '_')}_{timestamp}_{doc_id}.docx"
                
                # Save the document using existing document_manager
                if self.document_manager:
                    doc_path = self.document_manager.save_document_text(
                        results["raw_text"],
                        filename,
                        category,
                        country
                    )
                    results["document_path"] = doc_path
            else:
                # If all sources failed, mark the overall operation as failed
                results["success"] = False
                results["error"] = "All data sources failed"
                results["message"] = "Unable to research this brand. Please try a different brand name or try again later."
                self.logger.error(f"All research sources failed for {brand_name}")
            
            elapsed_time = time.time() - start_time
            self.logger.info(f"Enhanced research completed in {elapsed_time:.2f} seconds for {brand_name}")
            
        except Exception as e:
            self.logger.error(f"Error during enhanced research for {brand_name}: {str(e)}")
            traceback.print_exc()
            results["success"] = False
            results["error"] = str(e)
            results["message"] = "An error occurred during enhanced brand research"
        
        return results 