import requests
import json

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