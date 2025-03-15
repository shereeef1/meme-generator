"""
Test script for the Supermeme.ai API integration.

This is a standalone test to verify that the API key is working and can generate memes.
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv('backend/.env')

def test_supermeme_api():
    """Test connecting to the Supermeme.ai API and generating a meme."""
    
    # Get API key from environment
    api_key = os.environ.get('SUPREME_MEME_API_KEY')
    if not api_key:
        print("Error: SUPREME_MEME_API_KEY not found in environment variables")
        return False
    
    print(f"API Key loaded: {api_key[:5]}...{api_key[-5:]}")  # Show just parts of the key for security
    
    # Correct API endpoint from the documentation
    api_url = "https://app.supermeme.ai/api/v2/meme/image"
    
    # Text for the meme
    meme_text = "When your API integration finally works"
    
    # Prepare the request
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "text": meme_text
    }
    
    print(f"Sending request to {api_url} with text: '{meme_text}'")
    
    try:
        # Make the API request
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        # Print response status
        print(f"Response status code: {response.status_code}")
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the response
            try:
                response_data = response.json()
                print("Response data:", json.dumps(response_data, indent=4))
                
                if 'memes' in response_data and isinstance(response_data['memes'], list) and len(response_data['memes']) > 0:
                    print(f"Success! Generated {len(response_data['memes'])} memes")
                    print(f"First meme URL: {response_data['memes'][0]}")
                    return True
                else:
                    print("Warning: Response doesn't contain 'memes' array")
                    print("Full response:", response_data)
                    return False
                    
            except ValueError as e:
                print(f"Error parsing response JSON: {e}")
                print("Response content:", response.text[:500])  # Show part of the response
                return False
        else:
            print(f"Error: API request failed with status code {response.status_code}")
            print("Response content:", response.text[:500])  # Show part of the response
            return False
            
    except Exception as e:
        print(f"Error making API request: {e}")
        return False

if __name__ == "__main__":
    print("Testing Supermeme.ai API integration...")
    success = test_supermeme_api()
    
    if success:
        print("\n✅ Test passed! The API integration is working.")
    else:
        print("\n❌ Test failed! Check the error messages above.")

url = 'http://localhost:5000/api/generate-meme'
data = {
    'prompt': 'When your protein bar has more flavor than your love life.',
    'brand_name': 'Test Brand',
    'category': 'Health'
}

print(f'Sending request to {url} with data: {data}')

try:
    response = requests.post(url, json=data, timeout=30)
    print(f'Status code: {response.status_code}')
    
    if response.status_code == 200:
        result = response.json()
        print(f'Success: {result.get("success")}')
        print(f'Message: {result.get("message")}')
        print('Meme URLs:')
        for i, url in enumerate(result.get("meme_urls", [])):
            print(f'  {i+1}. {url}')
    else:
        print(f'Error response: {response.text}')
except Exception as e:
    print(f'Error: {e}') 