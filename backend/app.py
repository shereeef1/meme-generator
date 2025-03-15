from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from dotenv import load_dotenv
from config import Config

# Import our modules
from modules.meme_generation import MemeGenerator
from modules.scraping import BrandScraper
# These will be used in subsequent steps
# from modules.news_integration import NewsIntegration
# from modules.export import MemeExport
# from firebase_config import db, storage_bucket

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration
app.config.from_object(Config)

# Initialize the modules
meme_generator = MemeGenerator()
brand_scraper = BrandScraper()

# Simple health check route
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "Meme generation API is running"})

# Route for generating memes
@app.route('/api/generate-meme', methods=['POST'])
def generate_meme():
    try:
        # Get the text from the request
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No data provided",
                "message": "Please provide text for the meme"
            }), 400
            
        text = data.get('text', '')
        style = data.get('style')
        template = data.get('template')
        
        # Generate the meme
        result = meme_generator.generate_meme(text, style, template)
        
        # Return the result
        if result["success"]:
            return jsonify(result)
        else:
            # If there was an error, return with appropriate status code
            return jsonify(result), 400
            
    except Exception as e:
        # Handle any unexpected errors
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}",
            "message": "An unexpected error occurred on the server."
        }), 500

# Route for scraping brand data
@app.route('/api/scrape-brand', methods=['POST'])
def scrape_brand():
    try:
        # Get the URL from the request
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({
                "success": False,
                "error": "No URL provided",
                "message": "Please provide a URL to scrape"
            }), 400
            
        url = data.get('url')
        category = data.get('category')
        country = data.get('country')
        
        # Scrape the brand data
        result = brand_scraper.scrape_brand_data(url, category, country)
        
        # Return the result
        if result["success"]:
            return jsonify(result)
        else:
            # If there was an error, return with appropriate status code
            return jsonify(result), 400
            
    except Exception as e:
        # Handle any unexpected errors
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}",
            "message": "An unexpected error occurred on the server."
        }), 500

# Route for fetching news (we'll implement this in Step 5)
@app.route('/api/news', methods=['GET'])
def get_news():
    # Placeholder for now
    return jsonify({"status": "success", "message": "News endpoint (to be implemented)"})

# Route for exporting memes (we'll implement this in Step 7)
@app.route('/api/export-meme', methods=['POST'])
def export_meme():
    # Placeholder for now
    return jsonify({"status": "success", "message": "Meme export endpoint (to be implemented)"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 