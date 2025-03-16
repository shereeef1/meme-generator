import os
import logging
import requests
import re
import time
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LLMDeepSearch:
    """
    Class for using DeepSeek's reasoning capabilities to gather and analyze brand information
    """

    def __init__(self):
        """Initialize the LLM DeepSearch module"""
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            logging.error("DeepSeek API key not found in environment variables")
            raise ValueError("DeepSeek API key not found in environment variables")
        
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
    
    def deep_search_brand(self, brand_name, category=None, country=None):
        """
        Perform deep search on a brand using DeepSeek's reasoning capabilities
        
        Args:
            brand_name (str): Name of the brand to research
            category (str, optional): Brand category
            country (str, optional): Brand's primary market
            
        Returns:
            dict: Brand research results from DeepSeek
        """
        self.logger.info(f"Starting LLM DeepSearch for brand: {brand_name}")
        start_time = time.time()
        
        try:
            # Formulate a detailed prompt for comprehensive brand research
            prompt = self._create_research_prompt(brand_name, category, country)
            
            # Call DeepSeek API with comprehensive research prompt
            response = self._call_deepseek_api(prompt)
            
            if not response or not response.get("choices") or not response["choices"][0].get("message"):
                raise Exception("Invalid response from DeepSeek API")
            
            # Process the response content
            content = response["choices"][0]["message"]["content"]
            
            # Structure the research results
            structured_data = self._structure_brand_research(content, brand_name)
            
            # Calculate elapsed time
            elapsed_time = time.time() - start_time
            self.logger.info(f"LLM DeepSearch completed in {elapsed_time:.2f} seconds for {brand_name}")
            
            return {
                "success": True,
                "brand_name": brand_name,
                "data": structured_data,
                "text": content,
                "url": "LLM DeepSearch Analysis"
            }
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            self.logger.error(f"Error during LLM DeepSearch for {brand_name}: {str(e)}")
            
            return {
                "success": False,
                "brand_name": brand_name,
                "error": str(e),
                "text": f"Failed to complete LLM DeepSearch for {brand_name}. Error: {str(e)}",
                "url": "LLM DeepSearch Analysis (Failed)"
            }
    
    def _create_research_prompt(self, brand_name, category=None, country=None):
        """
        Create a comprehensive research prompt for DeepSeek
        
        Args:
            brand_name (str): Name of the brand to research
            category (str, optional): Brand category
            country (str, optional): Brand's primary market
            
        Returns:
            str: Detailed prompt for DeepSeek API
        """
        prompt = [
            {"role": "system", "content": """You are a brand research expert with exceptional analytical and reasoning skills. 
Your task is to provide comprehensive information about a brand by thinking step-by-step and gathering as much factual information as possible.

Please structure your analysis to include:

1. **Brand Overview**
   - Brand name, founding date, founder(s)
   - Core business, products/services
   - Target audience, market positioning

2. **Business Model**
   - Revenue streams
   - Pricing strategy
   - Distribution channels

3. **Market Position**
   - Market share/size
   - Main competitors
   - Competitive advantage

4. **Brand Identity**
   - Brand values and mission
   - Visual identity (colors, logo description)
   - Brand voice and messaging

5. **Product or Service Details**
   - Key products/services
   - Unique features and benefits
   - Quality positioning

6. **Marketing & Communication**
   - Marketing channels
   - Key campaigns
   - Social media presence

7. **Customer Experience**
   - Customer service approach
   - Online vs offline experience
   - Customer feedback themes

8. **Recent Developments**
   - Recent news
   - Innovations
   - Leadership changes

9. **Challenges & Opportunities**
   - Current challenges
   - Growth opportunities
   - Market trends affecting the brand

Provide the most accurate and detailed information available to you about this brand. If you're uncertain about specific details, indicate this clearly rather than providing potentially incorrect information."""},
            {"role": "user", "content": f"Please research the brand: {brand_name}" + 
             (f" in the {category} category" if category else "") + 
             (f" with a focus on the {country} market" if country else "") + 
             ". Provide comprehensive information using your knowledge and reasoning capabilities."}
        ]
        
        return prompt
    
    def _call_deepseek_api(self, prompt):
        """
        Call the DeepSeek API with a given prompt
        
        Args:
            prompt (list): List of message objects for the DeepSeek API
            
        Returns:
            dict: API response
        """
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={
                    "model": "deepseek-chat",
                    "messages": prompt,
                    "temperature": 0.2,  # Lower temperature for more factual responses
                    "max_tokens": 3000    # Increase token limit for detailed analysis
                },
                timeout=60  # Increase timeout for complex reasoning
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error calling DeepSeek API: {str(e)}")
            raise Exception(f"Error calling DeepSeek API: {str(e)}")
    
    def _structure_brand_research(self, content, brand_name):
        """
        Structure the brand research content from DeepSeek
        
        Args:
            content (str): Raw text response from DeepSeek
            brand_name (str): Name of the brand
            
        Returns:
            dict: Structured brand research data
        """
        # Create basic structure for brand research
        structured_data = {
            "name": brand_name,
            "overview": {},
            "business_model": {},
            "market_position": {},
            "brand_identity": {},
            "products_services": {},
            "marketing": {},
            "customer_experience": {},
            "recent_developments": {},
            "challenges_opportunities": {}
        }
        
        # Extract sections using regex patterns
        try:
            # Extract Brand Overview section
            overview_match = re.search(r"(?:Brand Overview|1\.\s*\*\*Brand Overview\*\*)(.*?)(?=\d\.\s*\*\*|\Z)", content, re.DOTALL)
            if overview_match:
                structured_data["overview"]["text"] = overview_match.group(1).strip()
            
            # Extract Business Model section
            business_model_match = re.search(r"(?:Business Model|2\.\s*\*\*Business Model\*\*)(.*?)(?=\d\.\s*\*\*|\Z)", content, re.DOTALL)
            if business_model_match:
                structured_data["business_model"]["text"] = business_model_match.group(1).strip()
            
            # Extract Market Position section
            market_position_match = re.search(r"(?:Market Position|3\.\s*\*\*Market Position\*\*)(.*?)(?=\d\.\s*\*\*|\Z)", content, re.DOTALL)
            if market_position_match:
                structured_data["market_position"]["text"] = market_position_match.group(1).strip()
                
                # Try to extract competitors
                competitors_match = re.search(r"(?:Main competitors|Competitors)(.*?)(?=-|\*|\d\.|\Z)", market_position_match.group(1), re.DOTALL)
                if competitors_match:
                    competitors_text = competitors_match.group(1).strip()
                    competitors = [comp.strip() for comp in re.split(r',|\n-', competitors_text) if comp.strip()]
                    structured_data["market_position"]["competitors"] = competitors
            
            # Extract Brand Identity section
            brand_identity_match = re.search(r"(?:Brand Identity|4\.\s*\*\*Brand Identity\*\*)(.*?)(?=\d\.\s*\*\*|\Z)", content, re.DOTALL)
            if brand_identity_match:
                structured_data["brand_identity"]["text"] = brand_identity_match.group(1).strip()
            
            # Extract Product or Service Details section
            products_match = re.search(r"(?:Product or Service Details|5\.\s*\*\*Product or Service Details\*\*)(.*?)(?=\d\.\s*\*\*|\Z)", content, re.DOTALL)
            if products_match:
                structured_data["products_services"]["text"] = products_match.group(1).strip()
            
            # Extract Marketing & Communication section
            marketing_match = re.search(r"(?:Marketing & Communication|6\.\s*\*\*Marketing & Communication\*\*)(.*?)(?=\d\.\s*\*\*|\Z)", content, re.DOTALL)
            if marketing_match:
                structured_data["marketing"]["text"] = marketing_match.group(1).strip()
            
            # Extract Customer Experience section
            customer_exp_match = re.search(r"(?:Customer Experience|7\.\s*\*\*Customer Experience\*\*)(.*?)(?=\d\.\s*\*\*|\Z)", content, re.DOTALL)
            if customer_exp_match:
                structured_data["customer_experience"]["text"] = customer_exp_match.group(1).strip()
            
            # Extract Recent Developments section
            recent_dev_match = re.search(r"(?:Recent Developments|8\.\s*\*\*Recent Developments\*\*)(.*?)(?=\d\.\s*\*\*|\Z)", content, re.DOTALL)
            if recent_dev_match:
                structured_data["recent_developments"]["text"] = recent_dev_match.group(1).strip()
            
            # Extract Challenges & Opportunities section
            challenges_match = re.search(r"(?:Challenges & Opportunities|9\.\s*\*\*Challenges & Opportunities\*\*)(.*?)(?=\d\.\s*\*\*|\Z|$)", content, re.DOTALL)
            if challenges_match:
                structured_data["challenges_opportunities"]["text"] = challenges_match.group(1).strip()
                
        except Exception as e:
            self.logger.warning(f"Error while structuring data: {str(e)}")
            # Even if structuring fails, we still have the raw text
        
        return structured_data 