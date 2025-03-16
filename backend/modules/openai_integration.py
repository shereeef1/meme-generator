import os
import logging
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PromptGenerator:
    def __init__(self, require_key=False):
        """Initialize the PromptGenerator with DeepSeek client."""
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            logger.warning("DeepSeek API key not found in environment variables")
            if require_key:
                raise ValueError("DeepSeek API key not found")
            else:
                self.available = False
                logger.info("PromptGenerator will operate in limited mode without DeepSeek API")
                return
        
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Only test the API key if it's available
        self.available = True
        if self.api_key and os.environ.get('FLASK_ENV') != 'production':
            # Test the API key with a minimal request
            try:
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": "You are a helpful assistant."},
                            {"role": "user", "content": "Hello! Are you working?"}
                        ],
                        "max_tokens": 5
                    }
                )
                response.raise_for_status()
                logger.info("DeepSeek API key validated successfully")
            except Exception as e:
                logger.warning(f"DeepSeek API test request failed: {e}")
                # Don't raise an exception, just log the warning
                
    def generate_meme_prompts(self, brand_data):
        """
        Generate meme prompts based on the brand data.
        
        Args:
            brand_data (dict): Dictionary containing brand information
            
        Returns:
            list: List of generated meme prompts
        """
        if not self.available:
            # Return fallback prompts if API is not available
            return {
                'success': True,
                'prompts': [
                    {
                        'caption': f'When everyone uses ordinary products, but you choose {brand_data.get("brand_name", "our brand")}.',
                        'suggestion': f'Show someone standing out in a crowd because they\'re using {brand_data.get("brand_name", "our brand")} products.'
                    },
                    {
                        'caption': f'{brand_data.get("brand_name", "Our brand")} isn\'t just a product, it\'s a lifestyle choice that sets you apart.',
                        'suggestion': f'Display a split screen comparing ordinary life vs. the extraordinary {brand_data.get("brand_name", "our brand")} lifestyle.'
                    },
                    {
                        'caption': f'That moment when you realize {brand_data.get("brand_name", "our brand")} changed everything.',
                        'suggestion': f'Person having an "aha" moment while using a {brand_data.get("brand_name", "our brand")} product with a lightbulb appearing above their head.'
                    }
                ],
                'message': 'Generated sample prompts (DeepSeek API not available)'
            }
            
        try:
            # Extract raw text directly
            raw_text = brand_data.get('raw_text', '')
            if not raw_text:
                raise ValueError("No raw text provided in brand data")
            
            logger.info("Generating prompts with DeepSeek API...")
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": """You are a professional meme prompt generator. The brand name and category is mentioned, try to include the brand name in the prompt generated. Create 30 unique and engaging meme ideas based on the provided content. For each idea, provide both a Caption (the actual text that would appear on the meme) and a Suggestion (a description of the visual scene). Format each prompt exactly like this example:

Caption: 'This protein powder delivers 90% protein concentration, making it one of the purest forms of whey available.'
Suggestion: Show a laboratory scientist carefully measuring protein powder with precision equipment.

Important requirements:
1. Keep all captions under 300 characters
2. Focus on factual information about the product or service
3. Avoid hashtags completely
4. Keep the tone professional and informative
5. Each prompt should be unique and relevant to the content provided."""},
                        {"role": "user", "content": raw_text}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            )
            response.raise_for_status()
            
            # Extract and format the prompts
            content = response.json()['choices'][0]['message']['content']
            
            # Split by double newlines to separate each prompt pair
            prompts = []
            prompt_pairs = content.split('\n\n')
            for pair in prompt_pairs:
                if 'Caption:' in pair and 'Suggestion:' in pair:
                    parts = pair.split('\nSuggestion:')
                    if len(parts) == 2:
                        caption = parts[0].replace('Caption:', '').strip()
                        suggestion = parts[1].strip()
                        
                        # Ensure caption is under 300 characters
                        if len(caption) > 300:
                            caption = caption[:297] + '...'
                            
                        # Remove any hashtags that might have been included
                        caption = caption.replace('#', '')
                        
                        prompts.append({
                            'caption': caption,
                            'suggestion': suggestion
                        })
            
            # Ensure we have exactly 30 prompts
            prompts = prompts[:30]
            
            if not prompts:
                raise Exception("No valid prompts were generated")
            
            logger.info(f"Generated {len(prompts)} meme prompts successfully")
            logger.info(f"Caption character count range: {min([len(p['caption']) for p in prompts])} - {max([len(p['caption']) for p in prompts])}")
            return prompts
            
        except Exception as e:
            logger.error(f"Error generating meme prompts: {str(e)}")
            raise Exception(f"Failed to generate prompts: {str(e)}") 