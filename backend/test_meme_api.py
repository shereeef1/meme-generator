"""
Test the meme generation functionality with the real API.
This script is separate from the test suite and is meant to be run manually.
"""

import os
import sys
from dotenv import load_dotenv

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our module
from backend.modules.meme_generation import MemeGenerator

# Load environment variables
load_dotenv()

def test_meme_generation():
    """Test generating a meme with the real Supreme Meme AI API"""
    
    print("Testing meme generation with the real Supreme Meme AI API...")
    
    # Create a MemeGenerator instance
    meme_generator = MemeGenerator()
    
    # Generate a meme
    test_text = "When you finally get your meme generator working"
    print(f"Generating meme with text: '{test_text}'")
    
    result = meme_generator.generate_meme(test_text)
    
    # Print the result
    if result["success"]:
        print("Meme generated successfully!")
        print(f"Image URL: {result.get('image_url', 'N/A')}")
        print(f"Meme ID: {result.get('meme_id', 'N/A')}")
    else:
        print("Meme generation failed!")
        print(f"Error: {result.get('error', 'Unknown error')}")
        print(f"Message: {result.get('message', 'No message')}")
        
    # Return success status
    return result["success"]

if __name__ == "__main__":
    success = test_meme_generation()
    sys.exit(0 if success else 1) 