import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base config."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-dev-key')
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'
    DEBUG = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    # API URLs
    OPENAI_API_URL = 'https://api.openai.com/v1/chat/completions'
    DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions'

class ProductionConfig(Config):
    """Production config."""
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    """Development config."""
    DEBUG = True

class TestingConfig(Config):
    """Testing config."""
    TESTING = True
    
# Map config based on environment
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}

def get_config():
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, DevelopmentConfig)

# API Keys (stored as environment variables for security)
SUPREME_MEME_API_KEY = os.environ.get('SUPREME_MEME_API_KEY')
NEWS_API_KEY = os.environ.get('NEWS_API_KEY')

# Firebase config
FIREBASE_CREDENTIALS = os.environ.get('FIREBASE_CREDENTIALS_PATH')
FIREBASE_STORAGE_BUCKET = os.environ.get('FIREBASE_STORAGE_BUCKET') 