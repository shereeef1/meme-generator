import requests
import json

url = 'http://localhost:5000/api/generate-prompts'
data = {
    'raw_text': 'Test document content for generating prompts. This is a health and wellness brand focused on natural ingredients.',
    'brand_name': 'Test Brand',
    'category': 'Health',
    'country': 'US'
}

print(f'Sending request to {url} with data: {data}')

try:
    response = requests.post(url, json=data, timeout=30)
    print(f'Status code: {response.status_code}')
    print(f'Response: {response.text[:200]}...')
except Exception as e:
    print(f'Error: {e}')
