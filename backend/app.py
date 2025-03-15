from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import os
from dotenv import load_dotenv
from config import Config
import requests
import logging

# Import our modules
from modules.meme_generation import MemeGenerator
from modules.scraping import BrandScraper
from modules.openai_integration import PromptGenerator
from modules.file_processor import FileProcessor
from modules.document_manager import DocumentManager
# These will be used in subsequent steps
# from modules.news_integration import NewsIntegration
# from modules.export import MemeExport
# from firebase_config import db, storage_bucket

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Enable CORS with additional configuration
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})
app.config.from_object(Config)

# Initialize the modules
meme_generator = MemeGenerator()
brand_scraper = BrandScraper()
prompt_generator = PromptGenerator()
file_processor = FileProcessor()
doc_manager = DocumentManager()

# Simple health check route
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "Meme generation API is running"})

# Route for generating memes
@app.route('/api/generate-meme', methods=['POST'])
def generate_meme():
    try:
        data = request.get_json()
        
        if not data or 'prompt' not in data:
            return jsonify({
                "success": False,
                "error": "No prompt provided",
                "message": "Please provide a prompt for the meme"
            }), 400
            
        # Get the prompt and brand data
        prompt = data['prompt']
        brand_data = data.get('brandData', {})
        
        # Generate memes using the meme generator module
        meme_urls = meme_generator.generate_memes(prompt, brand_data)
        
        if not meme_urls:
            raise Exception("No memes were generated")
            
        return jsonify({
            "success": True,
            "meme_urls": meme_urls,
            "message": "Memes generated successfully"
        })
            
    except Exception as e:
        app.logger.error(f"Error generating meme: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to generate meme"
        }), 500

# Route for scraping brand data
@app.route('/api/scrape-brand', methods=['POST'])
def scrape_brand():
    try:
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
        
        if result["success"]:
            # Add document to history
            doc_entry = doc_manager.add_document(
                result["document_path"],
                result["source_url"],
                category,
                country
            )
            result["document_id"] = doc_entry["id"]
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        app.logger.error(f"Server error in scrape_brand: {str(e)}")
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

# Add this new route
@app.route('/api/documents', methods=['GET'])
def get_documents():
    """Get document history with pagination"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        offset = (page - 1) * per_page
        documents = doc_manager.get_document_history(limit=per_page, offset=offset)
        
        return jsonify({
            "success": True,
            "documents": documents,
            "page": page,
            "per_page": per_page,
            "total": len(doc_manager.get_document_history())
        })
        
    except Exception as e:
        app.logger.error(f"Error fetching documents: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to fetch documents"
        }), 500

@app.route('/api/documents/<int:doc_id>', methods=['GET'])
def get_document(doc_id):
    """Get document by ID"""
    try:
        doc = doc_manager.get_document(doc_id)
        if doc:
            return send_file(
                doc["path"],
                as_attachment=True,
                download_name=doc["filename"]
            )
        else:
            return jsonify({
                "success": False,
                "error": "Document not found",
                "message": "The requested document was not found"
            }), 404
            
    except Exception as e:
        app.logger.error(f"Error fetching document: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to fetch document"
        }), 500

@app.route('/api/documents/<int:doc_id>', methods=['PUT'])
def update_document(doc_id):
    """Update document content"""
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({
                "success": False,
                "error": "No content provided",
                "message": "Please provide content to update"
            }), 400
            
        doc = doc_manager.get_document(doc_id)
        if not doc:
            return jsonify({
                "success": False,
                "error": "Document not found",
                "message": "The requested document was not found"
            }), 404
            
        success = doc_manager.update_document_content(doc["path"], data["content"])
        if success:
            return jsonify({
                "success": True,
                "message": "Document updated successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Update failed",
                "message": "Failed to update document"
            }), 500
            
    except Exception as e:
        app.logger.error(f"Error updating document: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to update document"
        }), 500

@app.route('/api/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    """Delete document"""
    try:
        success = doc_manager.delete_document(doc_id)
        if success:
            return jsonify({
                "success": True,
                "message": "Document deleted successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Delete failed",
                "message": "Failed to delete document"
            }), 500
            
    except Exception as e:
        app.logger.error(f"Error deleting document: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to delete document"
        }), 500

@app.route('/api/generate-prompts', methods=['POST'])
def generate_prompts():
    try:
        data = request.get_json()
        
        if not data or 'raw_text' not in data:
            return jsonify({
                'success': False,
                'message': 'No raw text provided'
            }), 400

        api_key = os.getenv("DEEPSEEK_API_KEY")
        api_url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Generate 30 prompts in one call
        response = requests.post(
            api_url,
            headers=headers,
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "You are a creative meme generator. Create 30 unique and engaging meme ideas based on the following content. For each idea, provide both a Caption (the actual text that would appear on the meme) and a Suggestion (a description of the visual scene). Format each prompt exactly like this example:\n\nCaption: 'At 90% protein concentration, this is the purest form of whey you can get. This unflavored protein is so versatile, you can use it any whey you like!'\nSuggestion: Show a confused person surrounded by a smoothie, pancakes, and a shake, captioned with 'When your protein powder does it all.'"},
                    {"role": "user", "content": data['raw_text']}
                ],
                "temperature": 0.8,
                "max_tokens": 2000
            }
        )
        response.raise_for_status()

        # Extract and clean up the generated prompts
        generated_text = response.json()['choices'][0]['message']['content']
        prompts = []
        
        # Split by double newlines to separate each prompt pair
        prompt_pairs = generated_text.split('\n\n')
        for pair in prompt_pairs:
            if 'Caption:' in pair and 'Suggestion:' in pair:
                parts = pair.split('\nSuggestion:')
                if len(parts) == 2:
                    caption = parts[0].replace('Caption:', '').strip()
                    suggestion = parts[1].strip()
                    prompts.append({
                        'caption': caption,
                        'suggestion': suggestion
                    })
        
        # Ensure we have exactly 30 prompts
        prompts = prompts[:30]
        
        if not prompts:
            raise Exception("Failed to generate any valid prompts")
        
        return jsonify({
            'success': True,
            'prompts': prompts
        })

    except Exception as e:
        app.logger.error(f"Error generating prompts: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to generate prompts: {str(e)}'
        }), 500

@app.route('/api/upload-file', methods=['POST'])
def upload_file():
    """Handle file upload and process its content"""
    try:
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "error": "No file provided",
                "message": "Please select a file to upload"
            }), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                "success": False,
                "error": "No file selected",
                "message": "Please select a file to upload"
            }), 400
            
        # Get optional parameters
        category = request.form.get('category')
        country = request.form.get('country')
        
        # Process the file
        result = file_processor.process_file(
            file.read(),
            file.filename,
            category=category,
            country=country
        )
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logging.error(f"Error processing file upload: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "An error occurred while processing the file"
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 