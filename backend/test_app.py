import pytest
from app import app
import json
import unittest.mock as mock

@pytest.fixture
def client():
    """Create a test client for the app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    """Test the health check endpoint"""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert 'message' in data

@mock.patch('modules.meme_generation.MemeGenerator.generate_meme')
def test_generate_meme_endpoint_success(mock_generate_meme, client):
    """Test the meme generation endpoint with successful response"""
    # Mock the generate_meme method to return a successful response with the new format
    mock_generate_meme.return_value = {
        "success": True,
        "message": "Memes generated successfully",
        "meme_urls": [
            "https://example.com/meme1.jpg",
            "https://example.com/meme2.jpg"
        ],
        "primary_meme_url": "https://example.com/meme1.jpg",
        "meme_count": 2
    }
    
    # Send a request to generate a meme
    response = client.post('/api/generate-meme', 
                          json={"text": "This is a test meme"},
                          content_type='application/json')
    
    # Check that the response is successful
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'meme_urls' in data
    assert len(data['meme_urls']) == 2
    assert 'primary_meme_url' in data
    
    # Verify the mock was called with the right parameters
    mock_generate_meme.assert_called_once_with("This is a test meme", None, None)

@mock.patch('modules.meme_generation.MemeGenerator.generate_meme')
def test_generate_meme_endpoint_failure(mock_generate_meme, client):
    """Test the meme generation endpoint with error response"""
    # Mock the generate_meme method to return an error response
    mock_generate_meme.return_value = {
        "success": False,
        "error": "API request failed",
        "message": "Could not connect to the Supermeme.ai API. Please try again later."
    }
    
    # Send a request to generate a meme
    response = client.post('/api/generate-meme', 
                          json={"text": "This is a test meme"},
                          content_type='application/json')
    
    # Check that the response has the right error status
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert 'error' in data

def test_generate_meme_no_data(client):
    """Test the meme generation endpoint with no data"""
    # Send a request with no JSON data
    response = client.post('/api/generate-meme', 
                          content_type='application/json')
    
    # Check that we get a bad request response
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert 'error' in data

def test_scrape_brand_endpoint(client):
    """Test the brand scraping endpoint placeholder"""
    response = client.post('/api/scrape-brand')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'message' in data

def test_news_endpoint(client):
    """Test the news endpoint placeholder"""
    response = client.get('/api/news')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'message' in data

def test_export_meme_endpoint(client):
    """Test the meme export endpoint placeholder"""
    response = client.post('/api/export-meme')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'message' in data 