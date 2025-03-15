import firebase_admin
from firebase_admin import credentials, firestore, storage
import os
from config import Config

def initialize_firebase():
    """Initialize Firebase Admin SDK with credentials"""
    
    try:
        # Check if already initialized
        if not firebase_admin._apps:
            # Initialize Firebase Admin with service account
            cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS)
            firebase_admin.initialize_app(cred, {
                'storageBucket': Config.FIREBASE_STORAGE_BUCKET
            })
        
        # Get Firestore client
        db = firestore.client()
        bucket = storage.bucket()
        
        print("Firebase initialized successfully")
        return db, bucket
        
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        raise e

# Initialize Firebase when this module is imported
db, storage_bucket = initialize_firebase() 