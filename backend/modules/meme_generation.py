import requests
import os
import json
import base64
import logging
import random
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemeGenerator:
    """Class to handle interactions with the Supermeme.ai API"""
    
    def __init__(self):
        self.api_key = Config.SUPREME_MEME_API_KEY
        # Correct API endpoint from the documentation
        self.api_url = "https://app.supermeme.ai/api/v2/meme/image"
        
        # Check if API key is available
        if not self.api_key:
            logger.warning("Supermeme.ai API key is not configured. Using mock responses.")
            self.mock_mode = True
        else:
            self.mock_mode = False
    
    def generate_meme(self, text, style=None, template=None):
        """
        Generate a meme using the Supermeme.ai API
        
        Args:
            text (str): Text to include in the meme (max 300 chars)
            style (str, optional): Style of meme to generate (may not be used)
            template (str, optional): Specific meme template to use (may not be used)
            
        Returns:
            dict: Response containing URLs to generated memes or error information
        """
        # Ensure text is within 300 character limit
        if not text:
            return {
                "success": False,
                "error": "No text provided",
                "message": "Please provide text for the meme"
            }
            
        if len(text) > 300:
            return {
                "success": False,
                "error": "Text exceeds 300 character limit",
                "message": "Please reduce text to 300 characters or less"
            }
        
        # Use mock responses when in mock mode (no API key)
        if self.mock_mode:
            return self._generate_mock_response(text)
            
        try:
            # Prepare the request payload (only text is required)
            payload = {
                "text": text
            }
            
            # Prepare headers with API key
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # Log attempt to call API
            logger.info(f"Attempting to call Supermeme.ai API with text: {text[:30]}...")
            
            # Make the API request
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30  # Timeout after 30 seconds
            )
            
            # Check if request was successful
            response.raise_for_status()
            
            # Parse the response
            response_data = response.json()
            
            # Check for successful response format (it should contain a "memes" array)
            if 'memes' in response_data and isinstance(response_data['memes'], list) and len(response_data['memes']) > 0:
                return {
                    "success": True,
                    "message": "Memes generated successfully",
                    "meme_urls": response_data['memes'],
                    "primary_meme_url": response_data['memes'][0] if response_data['memes'] else None,
                    "meme_count": len(response_data['memes'])
                }
            else:
                return {
                    "success": False,
                    "error": "Unexpected API response format",
                    "message": "The API returned a success but in an unexpected format",
                    "api_response": response_data
                }
                
        except requests.exceptions.RequestException as e:
            # Handle request exceptions (network errors, timeouts, etc.)
            logger.error(f"API request failed: {str(e)}")
            return {
                "success": False,
                "error": f"API request failed: {str(e)}",
                "message": "Could not connect to the Supermeme.ai API. Please try again later."
            }
            
        except ValueError as e:
            # Handle JSON parsing errors
            return {
                "success": False,
                "error": f"Error parsing API response: {str(e)}",
                "message": "Received an invalid response from the Supermeme.ai API."
            }
            
        except Exception as e:
            # Catch any other unexpected errors
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "message": "An unexpected error occurred while generating the meme."
            }

    def _generate_mock_response(self, text):
        """Generate a mock response when the API key is not available"""
        # List of sample meme images (placeholder URLs)
        sample_meme_urls = [
            "https://placeholder-image.com/meme1.jpg",
            "https://via.placeholder.com/800x600.png?text=Sample+Meme",
            "https://placehold.co/600x400/png",
            "https://picsum.photos/800/600"
        ]
        
        # Randomize how many meme URLs to return (1-3)
        num_memes = random.randint(1, 3)
        selected_memes = random.sample(sample_meme_urls, min(num_memes, len(sample_meme_urls)))
        
        logger.info(f"Returning mock meme response with {len(selected_memes)} sample images")
        
        return {
            "success": True,
            "message": "Mock memes generated (API key not configured)",
            "meme_urls": selected_memes,
            "primary_meme_url": selected_memes[0] if selected_memes else None,
            "meme_count": len(selected_memes),
            "is_mock": True
        }

    def generate_memes(self, text, brand_data=None):
        """
        Generate multiple memes using the Supermeme.ai API
        
        Args:
            text (str): Text to include in the meme
            brand_data (dict, optional): Additional brand context
            
        Returns:
            list: List of meme URLs
        """
        try:
            # Generate a single meme first
            result = self.generate_meme(text)
            
            if not result["success"]:
                raise Exception(result["message"])
                
            return result["meme_urls"]
            
        except Exception as e:
            raise Exception(f"Failed to generate memes: {str(e)}") 