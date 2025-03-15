import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration settings for the application"""
    
    # API Keys (stored as environment variables for security)
    SUPREME_MEME_API_KEY = os.environ.get('SUPREME_MEME_API_KEY')
    NEWS_API_KEY = os.environ.get('NEWS_API_KEY')
    
    # Firebase config
    FIREBASE_CREDENTIALS = os.environ.get('FIREBASE_CREDENTIALS_PATH')
    FIREBASE_STORAGE_BUCKET = os.environ.get('FIREBASE_STORAGE_BUCKET') 