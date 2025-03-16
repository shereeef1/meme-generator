from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import os
from dotenv import load_dotenv
from config import Config
import requests
import logging
import re
from datetime import datetime

# Import our modules
from modules.meme_generation import MemeGenerator
from modules.scraping import BrandScraper
from modules.openai_integration import PromptGenerator
from modules.file_processor import FileProcessor
from modules.document_manager import DocumentManager
# These will be used in subsequent steps
from modules.news_integration import NewsIntegration
# from modules.export import MemeExport
# from firebase_config import db, storage_bucket

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Enable CORS with additional configuration
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://localhost:3001", "http://localhost:3004"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept", "Origin"],
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
            
        # Extract prompt and optional brand data
        prompt = data.get('prompt', '')
        brand_data = data.get('brandData', None)
        
        # Call the actual meme generator
        result = meme_generator.generate_meme(prompt)
        
        if not result["success"]:
            return jsonify(result), 400
            
        return jsonify(result)
            
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
    try:
        # Get limit parameter from query string, default to 20
        limit = request.args.get('limit', 20, type=int)
        
        # Fetch news using NewsIntegration
        news_integration = NewsIntegration()
        news_articles = news_integration.get_top_news(limit=limit)
        
        return jsonify({
            "success": True,
            "news": news_articles
        })
    except Exception as e:
        logging.error(f"Error fetching news: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error fetching news: {str(e)}"
        }), 500

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
        app.logger.info("Starting prompt generation request")
        data = request.get_json()
        
        if not data:
            app.logger.warning("No data provided in request")
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
            
        if 'raw_text' not in data:
            app.logger.warning("No raw_text field in request data")
            return jsonify({
                'success': False,
                'message': 'No raw text provided'
            }), 400

        app.logger.info(f"Received raw text (first 100 chars): {data['raw_text'][:100]}...")
        
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            app.logger.error("DEEPSEEK_API_KEY not found in environment")
            # Return sample prompts instead of failing
            brand_name = data.get('brand_name', 'the brand')
            return jsonify({
                'success': True,
                'prompts': [
                    {
                        'caption': f'When everyone uses ordinary tech, but you choose {brand_name}.',
                        'suggestion': f'Show someone standing out in a crowd because they\'re using {brand_name} products.'
                    },
                    {
                        'caption': f'{brand_name} isn\'t just a product, it\'s a lifestyle choice that sets you apart.',
                        'suggestion': f'Display a split screen comparing ordinary life vs. the extraordinary {brand_name} lifestyle.'
                    },
                    {
                        'caption': f'That moment when you realize {brand_name} changed everything.',
                        'suggestion': f'Person having an "aha" moment while using a {brand_name} product with a lightbulb appearing above their head.'
                    }
                ],
                'message': 'Generated sample data due to error: DEEPSEEK_API_KEY not configured'
            })
        
        api_url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        app.logger.info("Sending request to DeepSeek API")
        app.logger.info(f"Raw text length: {len(data['raw_text'])} characters")
        
        # Get requested prompt count
        prompt_count = int(data.get('prompt_count', 10))
        app.logger.info(f"User requested {prompt_count} prompts")
        
        # Calculate appropriate max_tokens based on prompt count
        max_tokens = min(1500 + (prompt_count * 300), 4000)
        app.logger.info(f"Setting max_tokens to {max_tokens}")
        
        # Generate prompts in one call
        try:
            response = requests.post(
                api_url,
                headers=headers,
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": f"""You are a creative meme generator for a brand marketing team. Create exactly {prompt_count} unique and engaging meme ideas specifically about the brand described in the user's message.

IMPORTANT: The meme ideas must be specifically about the brand in the user's message, not any other brand. Be specific and mention brand name, products, or features in each prompt.

Your meme ideas should be varied and cover different aspects:
- Product features and benefits
- Brand positioning compared to competitors
- Customer experiences and testimonials
- Brand history, milestones, or achievements
- Industry trends related to the brand
- Product usage scenarios

For each idea, provide both a Caption (the text that would appear on the meme) and a Suggestion (a description of the visual scene).

Format each prompt exactly like this, with each prompt on a separate number:
1. Caption: 'The caption text here'
   Suggestion: The visual description here

2. Caption: 'Another caption text'
   Suggestion: Another visual description

Make sure to create exactly {prompt_count} different captions and suggestions as numbered items."""
                    },
                        {"role": "user", "content": data['raw_text']}
                    ],
                    "temperature": 0.8,
                    "max_tokens": max_tokens
                },
                timeout=90  # Increase timeout for longer generations
            )
            
            # Add detailed response logging
            app.logger.info(f"DeepSeek API response status: {response.status_code}")
            app.logger.info(f"DeepSeek API response headers: {dict(response.headers)}")
            
            if response.status_code != 200:
                app.logger.error(f"DeepSeek API error: {response.status_code}, Response body: {response.text}")
                return jsonify({
                    'success': False,
                    'error': f"DeepSeek API returned status code {response.status_code}",
                    'message': f"API error: {response.text}"
                }), 500
            
            response_json = response.json()
            app.logger.info(f"DeepSeek API response JSON keys: {list(response_json.keys())}")
            
            if 'choices' not in response_json or len(response_json['choices']) == 0:
                app.logger.error(f"DeepSeek API response missing 'choices': {response_json}")
                return jsonify({
                    'success': False,
                    'error': "Invalid API response format - missing 'choices'",
                    'message': "The API response didn't contain the expected data format"
                }), 500
                
            if 'message' not in response_json['choices'][0]:
                app.logger.error(f"DeepSeek API response missing 'message' in first choice: {response_json['choices'][0]}")
                return jsonify({
                    'success': False,
                    'error': "Invalid API response format - missing 'message' in first choice",
                    'message': "The API response didn't contain the expected data format"
                }), 500
                
            if 'content' not in response_json['choices'][0]['message']:
                app.logger.error(f"DeepSeek API response missing 'content' in message: {response_json['choices'][0]['message']}")
                return jsonify({
                    'success': False,
                    'error': "Invalid API response format - missing 'content' in message",
                    'message': "The API response didn't contain the expected data format"
                }), 500
                
            generated_text = response_json['choices'][0]['message']['content']
            app.logger.info(f"Successfully extracted generated text, length: {len(generated_text)}")
            app.logger.info(f"Generated text (first 300 chars): {generated_text[:300]}...")
            
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Error making request to DeepSeek API: {str(e)}")
            app.logger.error(f"Request details: URL={api_url}, Headers={headers}")
            return jsonify({
                'success': False,
                'error': f"Failed to connect to DeepSeek API: {str(e)}",
                'message': "There was a network error when connecting to the DeepSeek API. Please check your network connection and try again."
            }), 500

        prompts = []
        
        # Helper function to extract markdown patterns
        def extract_caption_suggestion(text):
            extracted_prompts = []
            
            # First check if it's a numbered list format (1. Caption: ...)
            if re.search(r'^\d+\.?\s+(Caption|caption|CAPTION|\*\*Caption\*\*):', text, re.MULTILINE):
                pattern = r'(?:\d+\.?\s+)?(Caption|caption|CAPTION|\*\*Caption\*\*):([^\n]+)\s+(?:Suggestion|suggestion|SUGGESTION|\*\*Suggestion\*\*):([^\n]+)'
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                
                for match in matches:
                    caption = match[1].strip().strip("'\"*")
                    suggestion = match[2].strip().strip("'\"*")
                    
                    if caption and suggestion:
                        extracted_prompts.append({
                            'caption': caption,
                            'suggestion': suggestion
                        })
            
            # If no matches with the numbered format, try alternative parsing
            if not extracted_prompts:
                lines = text.split('\n')
                current_caption = None
                current_suggestion = None
                
                # Detect markdown formatted headings pattern
                for i, line in enumerate(lines):
                    line = line.strip()
                    
                    # Skip separator lines (--- or similar)
                    if not line or line.startswith('---') or line.startswith('==='):
                        continue
                    
                    # Check for Caption markers with various formats
                    if re.search(r'(Caption|caption|CAPTION|\*\*Caption\*\*):', line, re.IGNORECASE):
                        # Save previous pair if complete
                        if current_caption and current_suggestion:
                            extracted_prompts.append({
                                'caption': current_caption,
                                'suggestion': current_suggestion
                            })
                        
                        # Extract new caption
                        caption_match = re.search(r'(?:Caption|caption|CAPTION|\*\*Caption\*\*):(.+)', line, re.IGNORECASE)
                        if caption_match:
                            current_caption = caption_match.group(1).strip().strip("'\"*")
                            current_suggestion = None
                    
                    # Check for Suggestion markers with various formats
                    elif re.search(r'(Suggestion|suggestion|SUGGESTION|\*\*Suggestion\*\*):', line, re.IGNORECASE):
                        suggestion_match = re.search(r'(?:Suggestion|suggestion|SUGGESTION|\*\*Suggestion\*\*):(.+)', line, re.IGNORECASE)
                        if suggestion_match:
                            current_suggestion = suggestion_match.group(1).strip().strip("'\"*")
                            
                            # If we have both caption and suggestion, add them immediately 
                            if current_caption and current_suggestion:
                                extracted_prompts.append({
                                    'caption': current_caption,
                                    'suggestion': current_suggestion
                                })
                                # Don't reset them yet, in case we want to add another pair later
                
                # Add the final pair if it exists
                if current_caption and current_suggestion:
                    extracted_prompts.append({
                        'caption': current_caption,
                        'suggestion': current_suggestion
                    })
            
            # Log the extracted prompts for debugging
            app.logger.info(f"Extracted {len(extracted_prompts)} prompts from DeepSeek response")
            for i, prompt in enumerate(extracted_prompts):
                app.logger.info(f"Prompt {i+1}: Caption: {prompt['caption'][:30]}... Suggestion: {prompt['suggestion'][:30]}...")
                
            return extracted_prompts

        # Try the more sophisticated parser first
        prompts = extract_caption_suggestion(generated_text)

        # If that fails, use the simpler line-by-line approach as backup
        if not prompts:
            app.logger.warning("Advanced parser failed, trying simple parser")
            current_caption = None
            current_suggestion = None
            
            for line in generated_text.split('\n'):
                line = line.strip()
                # Handle markdown formatted captions with asterisks
                if line.startswith('Caption:') or line.startswith('**Caption**:'):
                    # If we have a complete pair, add it to prompts
                    if current_caption and current_suggestion:
                        prompts.append({
                            'caption': current_caption,
                            'suggestion': current_suggestion
                        })
                    # Start a new pair
                    current_caption = line.replace('**Caption**:', 'Caption:').replace('Caption:', '').strip().strip("'\"*")
                # Handle markdown formatted suggestions with asterisks
                elif line.startswith('Suggestion:') or line.startswith('**Suggestion**:'):
                    current_suggestion = line.replace('**Suggestion**:', 'Suggestion:').replace('Suggestion:', '').strip().strip("'\"*")
            
            # Add the last pair if it exists
            if current_caption and current_suggestion:
                prompts.append({
                    'caption': current_caption,
                    'suggestion': current_suggestion
                })

        # Ensure we have the right number of prompts
        prompt_count = int(data.get('prompt_count', 10))
        if len(prompts) < prompt_count:
            app.logger.warning(f"Received fewer prompts than requested: {len(prompts)} vs {prompt_count}")
            
            # Generate a variety of templates for more diverse generic prompts
            brand_name = data.get('brand_name', 'the brand')
            template_captions = [
                f"When everyone else uses ordinary products, but you choose {brand_name}",
                f"{brand_name}'s innovation puts competitors to shame",
                f"That moment when you realize {brand_name} changed everything",
                f"Nobody: ... {brand_name} users: This is revolutionary!",
                f"{brand_name}: Making the impossible possible since [founding year]",
                f"What my friends think {brand_name} does vs. what it actually does",
                f"Me before and after discovering {brand_name}",
                f"When someone says they don't need {brand_name} in their life",
                f"{brand_name}: Because ordinary products are for ordinary people",
                f"Evolution of technology: → → → {brand_name}"
            ]
            
            template_suggestions = [
                f"A person standing out in a crowd because they're using {brand_name} products.",
                f"Show a comparison of outdated competition vs sleek {brand_name} products.",
                f"Person having an 'aha' moment while using a {brand_name} product.",
                f"A group of excited {brand_name} users contrasted with bored users of other products.",
                f"Timeline showing {brand_name}'s innovative history and achievements.",
                f"Split-screen showing a misconception on one side vs the actual {brand_name} impact on the other.",
                f"Before/after transformation when someone starts using {brand_name}.",
                f"Someone looking shocked/confused when hearing someone doesn't use {brand_name}.",
                f"Show ordinary people using ordinary products, then an extraordinary person using {brand_name}.",
                f"Evolution timeline ending with {brand_name} at the pinnacle."
            ]
            
            # Fill in remaining prompts with varied templates
            for i in range(len(prompts), prompt_count):
                template_index = i % len(template_captions)
                prompts.append({
                    'caption': template_captions[template_index],
                    'suggestion': template_suggestions[template_index]
                })

        if len(prompts) > prompt_count:
            app.logger.info(f"Limiting prompts to requested count: {prompt_count}")
            prompts = prompts[:prompt_count]

        app.logger.info(f"Successfully generated {len(prompts)} prompts")
        
        return jsonify({
            'success': True,
            'prompts': prompts,
            'message': 'Prompts generated successfully'
        })

    except Exception as e:
        app.logger.error(f"Error generating prompts: {str(e)}")
        # Return sample prompts instead of failing with 500 error
        brand_name = data.get('brand_name', 'the brand')
        return jsonify({
            'success': True,
            'prompts': [
                {
                    'caption': f'When everyone uses ordinary tech, but you choose {brand_name}.',
                    'suggestion': f'Show someone standing out in a crowd because they\'re using {brand_name} products.'
                },
                {
                    'caption': f'{brand_name} isn\'t just a product, it\'s a lifestyle choice that sets you apart.',
                    'suggestion': f'Display a split screen comparing ordinary life vs. the extraordinary {brand_name} lifestyle.'
                },
                {
                    'caption': f'That moment when you realize {brand_name} changed everything.',
                    'suggestion': f'Person having an "aha" moment while using a {brand_name} product with a lightbulb appearing above their head.'
                }
            ],
            'message': f'Generated sample data due to error: {str(e)}'
        })

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

@app.route('/api/generate-news-prompt', methods=['POST'])
def generate_news_prompt():
    """Generate a meme prompt based on a news article"""
    try:
        data = request.get_json()
        logging.info("Received news prompt request")
        
        if not data:
            logging.warning("No data provided in news prompt request")
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        if 'news' not in data:
            logging.warning("No news data provided in news prompt request")
            return jsonify({
                'success': False,
                'message': 'No news data provided'
            }), 400
            
        if 'brandData' not in data:
            logging.warning("No brand data provided in news prompt request")
            return jsonify({
                'success': False,
                'message': 'No brand data provided'
            }), 400
            
        news = data['news']
        brand_data = data['brandData']
        
        # Extract title and description from news
        news_title = news.get('title', '')
        news_description = news.get('description', '')
        
        logging.info(f"Generating prompt for news: {news_title[:30]}...")
        
        # Combine news with brand information
        news_content = f"News Article: {news_title}\n\nDescription: {news_description}\n\n"
        brand_content = f"Brand Info: {brand_data.get('raw_text', '')}"
        
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            logging.error("DeepSeek API key not found")
            return jsonify({
                'success': False,
                'message': 'API key not configured'
            }), 500
            
        api_url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Generate a prompt based on the news article
        try:
            logging.info("Making API request to DeepSeek")
            response = requests.post(
                api_url,
                headers=headers,
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": """You are a professional meme prompt generator specializing in creating prompts based on news articles. Create a factual, informative meme idea that connects the news article with the brand information provided.

Format your response exactly like this example:

Caption: 'This new study shows 90% protein concentration benefits muscle recovery by 30% faster than lower concentrations, making NutriWhey the most effective option for athletes.'
Suggestion: Show professional athletes recovering after a workout with charts displaying recovery rates.

Important requirements:
1. Keep the caption under 300 characters
2. Focus on factual information connecting the news and the brand
3. Avoid hashtags completely
4. Keep the tone professional and informative
5. Make sure the content is appropriate for business use"""},
                        {"role": "user", "content": news_content + "\n\n" + brand_content}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 500
                }
            )
            response.raise_for_status()
            logging.info("Received response from DeepSeek API")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error making request to DeepSeek API: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Error in API request: {str(e)}'
            }), 500
        
        # Extract the generated prompt
        try:
            generated_text = response.json()['choices'][0]['message']['content']
            logging.info(f"Generated text: {generated_text[:50]}...")
        except (KeyError, IndexError) as e:
            logging.error(f"Error parsing API response: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Error parsing API response'
            }), 500
        
        # Parse the response
        caption = ""
        suggestion = ""
        
        if 'Caption:' in generated_text and 'Suggestion:' in generated_text:
            parts = generated_text.split('Suggestion:')
            caption_part = parts[0].strip()
            suggestion = parts[1].strip()
            
            caption = caption_part.replace('Caption:', '').strip()
            
            # Ensure caption is under 300 characters
            if len(caption) > 300:
                caption = caption[:297] + '...'
                
            # Remove any hashtags that might have been included
            caption = caption.replace('#', '')
            
            logging.info(f"Successfully parsed prompt: Caption ({len(caption)} chars)")
        else:
            logging.warning("API response did not contain expected Caption/Suggestion format")
            return jsonify({
                'success': False,
                'message': 'Invalid response format from API'
            }), 500
        
        prompt = {
            'caption': caption,
            'suggestion': suggestion
        }
        
        logging.info(f"Generated news prompt with caption of {len(caption)} characters")
        
        return jsonify({
            'success': True,
            'prompt': prompt
        })
        
    except Exception as e:
        app.logger.error(f"Error generating news prompt: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to generate news prompt: {str(e)}'
        }), 500

@app.route('/api/llm-deepsearch-brand', methods=['POST'])
def llm_deepsearch_brand():
    try:
        app.logger.info("Received LLM DeepSearch brand request")
        data = request.get_json()
        
        if not data:
            app.logger.warning("No data provided in LLM DeepSearch request")
            return jsonify({
                "success": False,
                "error": "No data provided",
                "message": "Please provide brand details for research"
            }), 400
            
        brand_name = data.get('brand_name')
        
        if not brand_name:
            app.logger.warning("No brand name provided in LLM DeepSearch request")
            return jsonify({
                "success": False,
                "error": "No brand name provided",
                "message": "Please provide a brand name for research"
            }), 400
            
        category = data.get('category')
        country = data.get('country')
        
        app.logger.info(f"Starting LLM DeepSearch for brand: {brand_name}")
        
        # Use DeepSeek API to perform deep research on the brand
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            app.logger.error("DEEPSEEK_API_KEY not found in environment")
            return jsonify({
                "success": False,
                "error": "API key not configured",
                "message": "DeepSeek API key is not configured. Please check your .env file."
            }), 500
            
        api_url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Create a detailed prompt for comprehensive brand research
        system_prompt = """You are a professional market research analyst specializing in brand analysis. 
        Conduct a detailed analysis of the brand provided by the user.
        
        Your analysis should include:
        1. Company overview (founding, history, mission)
        2. Product/service portfolio
        3. Target audience and market positioning
        4. Competitive landscape
        5. Brand strengths and weaknesses
        6. Recent news or developments
        7. Marketing strategies
        8. Industry trends affecting the brand
        
        Present your findings in a well-structured, detailed report that would be valuable for a marketing team.
        Focus on factual information and professional analysis."""
        
        user_prompt = f"Perform a comprehensive market research analysis on {brand_name}"
        if category:
            user_prompt += f", which operates in the {category} sector"
        if country:
            user_prompt += f", with a focus on their presence in {country}"
        
        app.logger.info("Sending request to DeepSeek API for LLM DeepSearch")
        response = requests.post(
            api_url,
            headers=headers,
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 2500
            },
            timeout=60
        )
        
        if response.status_code == 200:
            research_text = response.json()['choices'][0]['message']['content']
            app.logger.info(f"Successfully received DeepSeek API response, length: {len(research_text)}")
            
            result = {
                "success": True,
                "text": research_text,
                "raw_text": research_text,
                "source_url": "LLM DeepSearch",
                "source_type": "llm_deepsearch",
                "brand_name": brand_name,
                "timestamp": datetime.now().isoformat()
            }
            return jsonify(result)
        else:
            app.logger.error(f"DeepSeek API returned error: {response.status_code}, {response.text}")
            return jsonify({
                "success": False,
                "error": f"API error: {response.status_code}",
                "message": f"Error from DeepSeek API: {response.text}"
            }), 500
            
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Exception during DeepSeek API request: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"API request failed: {str(e)}",
            "message": "Failed to connect to DeepSeek API. Please check your internet connection and API key."
        }), 500
            
    except Exception as e:
        app.logger.error(f"Server error in llm_deepsearch_brand: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}",
            "message": "An error occurred during LLM DeepSearch"
        }), 500

@app.route('/api/llm-deepsearch-brand', methods=['OPTIONS'])
def options_llm_deepsearch_brand():
    response = jsonify({})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response, 200

@app.route('/api/documents', methods=['OPTIONS'])
def options_documents():
    response = jsonify({})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response, 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 