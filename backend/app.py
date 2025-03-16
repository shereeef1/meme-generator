from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import os
from dotenv import load_dotenv
from config import Config
import requests
import logging
import time
import traceback
import uuid
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

# Import the enhanced research module
from modules.enhanced_research import EnhancedResearch
from modules.research_sources.llm_deepsearch import LLMDeepSearch

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Enable CORS with additional configuration
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://localhost:3001"],
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
news_integration = NewsIntegration()

# Initialize the enhanced research coordinator
enhanced_research = EnhancedResearch(brand_scraper, news_integration, doc_manager)

# Initialize the LLM DeepSearch module
llm_deepsearch = LLMDeepSearch()

# Simple health check route
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "Meme generation API is running"})

# Route for generating memes
@app.route('/api/generate-meme', methods=['POST'])
def generate_meme():
    try:
        app.logger.info("Received meme generation request")
        data = request.get_json()
        
        if not data or 'prompt' not in data:
            app.logger.warning("No prompt provided in meme generation request")
            return jsonify({
                "success": False,
                "error": "No prompt provided",
                "message": "Please provide a prompt for the meme"
            }), 400
        
        prompt = data['prompt']
        brand_name = data.get('brand_name', '')
        category = data.get('category', '')
        
        app.logger.info(f"Generating meme with prompt: {prompt[:50]}...")
        app.logger.info(f"Brand context: {brand_name}, Category: {category}")
        
        # Use the MemeGenerator class to generate memes
        try:
            # Create brand data context if available
            brand_data = None
            if brand_name or category:
                brand_data = {
                    "brand_name": brand_name,
                    "category": category
                }
            
            # Call the actual API through our MemeGenerator class
            result = meme_generator.generate_meme(prompt)
            
            if not result["success"]:
                app.logger.error(f"Meme generation failed: {result.get('error')}")
                return jsonify({
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                    "message": result.get("message", "Failed to generate meme")
                }), 500
            
            app.logger.info(f"Successfully generated {result.get('meme_count', 0)} memes")
            
            # Return the meme URLs
            return jsonify({
                "success": True,
                "meme_urls": result.get("meme_urls", []),
                "message": "Memes generated successfully"
            })
            
        except Exception as e:
            app.logger.error(f"Error in MemeGenerator: {str(e)}")
            # If the API fails, return a fallback response
            app.logger.warning("Falling back to placeholder meme URLs")
            return jsonify({
                "success": True,
                "meme_urls": [
                    "https://picsum.photos/seed/meme1/600/400",
                    "https://picsum.photos/seed/meme2/600/400",
                    "https://picsum.photos/seed/meme3/600/400",
                    "https://picsum.photos/seed/meme4/600/400"
                ],
                "message": "Memes generated using fallback (API unavailable)"
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
        app.logger.info("Received brand scraping request")
        data = request.get_json()
        
        if not data or 'url' not in data:
            app.logger.warning("No URL provided in scrape request")
            return jsonify({
                "success": False,
                "error": "No URL provided",
                "message": "Please provide a URL to scrape"
            }), 400
            
        url = data.get('url')
        category = data.get('category')
        country = data.get('country')
        
        app.logger.info(f"Scraping brand data from URL: {url}")
        # Set a timeout for the scraping operation
        start_time = time.time()
        
        # Scrape the brand data
        result = brand_scraper.scrape_brand_data(url, category, country)
        
        # Log the time taken
        elapsed_time = time.time() - start_time
        app.logger.info(f"Scraping completed in {elapsed_time:.2f} seconds. Success: {result['success']}")
        
        if result["success"]:
            # Add document to history
            doc_entry = doc_manager.add_document(
                result["document_path"],
                result["source_url"],
                category,
                country
            )
            result["document_id"] = doc_entry["id"]
            
            # Check if the raw_text is empty and log it
            if not result.get("raw_text") or not result["raw_text"].strip():
                app.logger.warning(f"Scraping completed but raw_text is empty for URL: {url}")
                # Add a minimal fallback text
                result["raw_text"] = f"Data scraped from {url}. Brand: {result.get('brand_name', 'Unknown')}"
                
            return jsonify(result)
        else:
            app.logger.error(f"Failed to scrape brand data: {result.get('error', 'Unknown error')}")
            return jsonify(result), 400
            
    except Exception as e:
        app.logger.error(f"Server error in scrape_brand: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}",
            "message": "An unexpected error occurred on the server. Please try uploading a file instead."
        }), 500

# Route for fetching news (we'll implement this in Step 5)
@app.route('/api/news', methods=['GET'])
def get_news():
    try:
        # Get limit parameter from query string, default to 20
        limit = request.args.get('limit', 20, type=int)
        
        # Get days parameter, default to 14 (2 weeks)
        days = request.args.get('days', 14, type=int)
        
        # Get country parameter, default to 'in' (India)
        country = request.args.get('country', 'in')
        
        # Get category parameter, default to None (all categories)
        category = request.args.get('category', None)
        
        # Use the globally initialized news_integration
        news_articles = news_integration.get_top_news(limit=limit, days=days, country=country, category=category)
        
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

        raw_text = data.get('raw_text', '')
        app.logger.info(f"Received raw text of length: {len(raw_text)} chars")
        app.logger.info(f"First 200 chars of raw text: {raw_text[:200]}...")
        
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            app.logger.error("DEEPSEEK_API_KEY not found in environment")
            # Return sample prompts instead of failing
            return jsonify({
                'success': True,
                'prompts': [
                    {
                        'caption': 'Tech innovations in India are growing at 40% annually, making our software solutions the perfect match for this booming market!',
                        'suggestion': 'Show a graph with exponential growth with Indian tech companies, with your brand logo at the top of the curve.'
                    },
                    {
                        'caption': 'While India\'s tech sector is reaching new heights, our brand\'s reliability keeps companies grounded in success.',
                        'suggestion': 'Show a rocket with "India Tech" written on it, launching upward with your brand logo as the foundation.'
                    },
                    {
                        'caption': 'The 25% increase in AI adoption in India means your business needs our smart solutions more than ever.',
                        'suggestion': 'Show a business person looking overwhelmed by AI options, then looking relieved when seeing your brand.'
                    }
                ],
                'message': 'Generated from sample data (API key not configured)'
            })
        
        api_url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        app.logger.info("Sending request to DeepSeek API")

        # Truncate text if it's extremely long to avoid API issues
        max_text_length = 15000  # DeepSeek likely has token limits
        if len(raw_text) > max_text_length:
            app.logger.warning(f"Raw text length ({len(raw_text)}) exceeds max length, truncating to {max_text_length} chars")
            raw_text = raw_text[:max_text_length] + "... [content truncated due to length]"

        # Create a system prompt that clearly explains the task
        system_prompt = "You are a creative meme generator. Create 3 unique and engaging meme ideas based on the following content. For each idea, provide both a Caption (the actual text that would appear on the meme) and a Suggestion (a description of the visual scene). Format each prompt exactly like this example:\n\nCaption: 'At 90% protein concentration, this is the purest form of whey you can get. This unflavored protein is so versatile, you can use it any whey you like!'\nSuggestion: Show a confused person surrounded by a smoothie, pancakes, and a shake, captioned with 'When your protein powder does it all.'"
        
        # Generate 3 prompts in one call with increased timeout
        try:
            app.logger.info("Making DeepSeek API request")
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": raw_text}
                ],
                "temperature": 0.8,
                "max_tokens": 1000
            }
            app.logger.debug(f"Request payload: {payload}")
            
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=60  # Increase timeout to 60 seconds
            )
            
            if response.status_code != 200:
                app.logger.error(f"DeepSeek API returned non-200 status: {response.status_code}")
                app.logger.error(f"Response content: {response.text}")
                raise Exception(f"API returned status code {response.status_code}: {response.text}")
                
            response_data = response.json()
            app.logger.info(f"Received response from DeepSeek API: {response_data}")
            
            # Extract the generated content
            if 'choices' in response_data and len(response_data['choices']) > 0:
                generated_content = response_data['choices'][0]['message']['content']
                app.logger.info(f"Generated content: {generated_content}")
                
                # Parse the generated content to extract prompts
                prompts = []
                current_caption = None
                current_suggestion = None
                
                for line in generated_content.split('\n'):
                    line = line.strip()
                    if line.startswith('Caption:'):
                        # If we have a complete pair, add it to prompts
                        if current_caption and current_suggestion:
                            prompts.append({
                                'caption': current_caption,
                                'suggestion': current_suggestion
                            })
                        # Start a new pair
                        current_caption = line[8:].strip().strip("'\"")
                    elif line.startswith('Suggestion:'):
                        current_suggestion = line[11:].strip()
                
                # Add the last pair if it exists
                if current_caption and current_suggestion:
                    prompts.append({
                        'caption': current_caption,
                        'suggestion': current_suggestion
                    })
                
                if not prompts:
                    app.logger.warning(f"Failed to parse prompts from generated content: {generated_content}")
                    # Fall back to sample prompts
                    return jsonify({
                        'success': True,
                        'prompts': [
                            {
                                'caption': 'When your food product claims "no added sugar" but still tastes suspiciously sweet.',
                                'suggestion': 'Show a skeptical person squinting at a food label with a magnifying glass.'
                            },
                            {
                                'caption': 'The whole truth about food labels: Reading them burns more calories than the actual food contains.',
                                'suggestion': 'Show someone in workout clothes exhausted from reading a tiny food label.'
                            },
                            {
                                'caption': 'Food companies be like: "Let\'s make the nutrition label font so small only ants can read it."',
                                'suggestion': 'Show ants having a meeting around a microscopic nutrition label.'
                            }
                        ],
                        'message': 'Generated from sample data (could not parse API response)'
                    })
                
                return jsonify({
                    'success': True,
                    'prompts': prompts,
                    'message': 'Prompts generated successfully'
                })
            else:
                app.logger.error(f"Unexpected response format from DeepSeek API: {response_data}")
                raise Exception("Unexpected response format from API")
                
        except requests.exceptions.Timeout:
            app.logger.error(f"Timeout error connecting to DeepSeek API (60s)")
            return jsonify({
                'success': False,
                'message': 'API request timed out. Please try again with a smaller document.'
            }), 504
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Error making request to DeepSeek API: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'API request failed: {str(e)}'
            }), 502
        except Exception as e:
            app.logger.error(f"Error processing DeepSeek API response: {str(e)}")
            # Return sample prompts instead of failing
            return jsonify({
                'success': True,
                'prompts': [
                    {
                        'caption': 'Tech innovations in India are growing at 40% annually, making our software solutions the perfect match for this booming market!',
                        'suggestion': 'Show a graph with exponential growth with Indian tech companies, with your brand logo at the top of the curve.'
                    },
                    {
                        'caption': 'While India\'s tech sector is reaching new heights, our brand\'s reliability keeps companies grounded in success.',
                        'suggestion': 'Show a rocket with "India Tech" written on it, launching upward with your brand logo as the foundation.'
                    },
                    {
                        'caption': 'The 25% increase in AI adoption in India means your business needs our smart solutions more than ever.',
                        'suggestion': 'Show a business person looking overwhelmed by AI options, then looking relieved when seeing your brand.'
                    }
                ],
                'message': 'Generated from sample data (API processing error)'
            })

    except Exception as e:
        app.logger.error(f"Error generating prompts: {str(e)}")
        # Return sample prompts instead of failing
        return jsonify({
            'success': True,
            'prompts': [
                {
                    'caption': 'Tech innovations in India are growing at 40% annually, making our software solutions the perfect match for this booming market!',
                    'suggestion': 'Show a graph with exponential growth with Indian tech companies, with your brand logo at the top of the curve.'
                },
                {
                    'caption': 'While India\'s tech sector is reaching new heights, our brand\'s reliability keeps companies grounded in success.',
                    'suggestion': 'Show a rocket with "India Tech" written on it, launching upward with your brand logo as the foundation.'
                },
                {
                    'caption': 'The 25% increase in AI adoption in India means your business needs our smart solutions more than ever.',
                    'suggestion': 'Show a business person looking overwhelmed by AI options, then looking relieved when seeing your brand.'
                }
            ],
            'message': 'Generated from sample data (unexpected error)'
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

# Route for enhanced brand research
@app.route('/api/enhanced-brand-research', methods=['POST'])
def enhanced_brand_research():
    try:
        app.logger.info("Received enhanced brand research request")
        data = request.get_json()
        
        if not data:
            app.logger.warning("No data provided in enhanced research request")
            return jsonify({
                "success": False,
                "error": "No data provided",
                "message": "Please provide brand details for research"
            }), 400
            
        brand_name = data.get('brand_name')
        
        if not brand_name:
            app.logger.warning("No brand name provided in enhanced research request")
            return jsonify({
                "success": False,
                "error": "No brand name provided",
                "message": "Please provide a brand name for research"
            }), 400
            
        category = data.get('category')
        country = data.get('country')
        include_competitors = data.get('include_competitors', True)
        include_trends = data.get('include_trends', True)
        
        app.logger.info(f"Starting enhanced research for brand: {brand_name}")
        # Set a timeout for the research operation
        start_time = time.time()
        
        # Perform the enhanced research
        result = enhanced_research.research_brand(
            brand_name=brand_name,
            category=category,
            country=country,
            include_competitors=include_competitors,
            include_trends=include_trends
        )
        
        # Log the time taken
        elapsed_time = time.time() - start_time
        app.logger.info(f"Enhanced research completed in {elapsed_time:.2f} seconds. Success: {result['success']}")
        
        # Check if the raw_text is empty and log it
        if not result.get("raw_text") or not result["raw_text"].strip():
            app.logger.warning(f"Enhanced research completed but raw_text is empty for brand: {brand_name}")
            # Add a minimal fallback text
            result["raw_text"] = f"Enhanced research for {brand_name}. Limited information available."
        
        # Always return a 200 status with the result, even if some parts failed
        # The frontend can handle partial failures using result["success"] and result["partial_failures"]
        if result["success"]:
            app.logger.info(f"Enhanced research successful for {brand_name}")
            
            # Check if there were partial failures
            if result.get("partial_failures") and len(result["partial_failures"]) > 0:
                app.logger.warning(f"Enhanced research had partial failures: {result['partial_failures']}")
        else:
            # If complete failure (all sources failed), log it but still send a 200 status
            app.logger.error(f"Enhanced research failed completely: {result.get('error', 'Unknown error')}")
        
        return jsonify(result)
            
    except Exception as e:
        app.logger.error(f"Server error in enhanced_brand_research: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}",
            "message": "An error occurred during enhanced brand research"
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
        start_time = time.time()
        
        # Perform the LLM DeepSearch
        result = llm_deepsearch.deep_search_brand(
            brand_name=brand_name,
            category=category,
            country=country
        )
        
        # Log the time taken
        elapsed_time = time.time() - start_time
        app.logger.info(f"LLM DeepSearch completed in {elapsed_time:.2f} seconds. Success: {result['success']}")
        
        # Check if the text is empty and log it
        if not result.get("text") or not result["text"].strip():
            app.logger.warning(f"LLM DeepSearch completed but text is empty for brand: {brand_name}")
            # Add a minimal fallback text
            result["text"] = f"LLM DeepSearch for {brand_name} returned no information. Please try with a different brand name."
        
        # Create a document from the research
        if result["success"] and result.get("text"):
            try:
                # Generate a unique document ID
                doc_id = str(uuid.uuid4().hex)[:8]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{brand_name.lower().replace(' ', '_')}_llm_{timestamp}_{doc_id}.docx"
                
                # Save text as document
                doc_path = doc_manager.save_document_text(
                    result["text"],
                    filename,
                    category,
                    country
                )
                
                result["document_path"] = doc_path
                # Format the data for frontend display
                result["raw_text"] = result["text"]
                result["source_url"] = f"LLM DeepSearch: {brand_name}"
                result["source_type"] = "llm_deepsearch"
                result["brand_name"] = brand_name
                result["timestamp"] = datetime.now().isoformat()
                
            except Exception as e:
                app.logger.error(f"Error saving LLM DeepSearch document: {str(e)}")
                # Even if document saving fails, continue with the operation
                result["warning"] = f"Document could not be saved: {str(e)}"
        
        return jsonify(result)
            
    except Exception as e:
        app.logger.error(f"Server error in llm_deepsearch_brand: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}",
            "message": "An error occurred during LLM DeepSearch"
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 