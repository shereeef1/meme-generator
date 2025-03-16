import firebase_admin
from firebase_admin import credentials, firestore, storage
import os
from config import Config

def initialize_firebase():
    """Initialize Firebase Admin SDK with credentials"""
    
    try:
        # Check if already initialized
        if not firebase_admin._apps:
            if Config.FIREBASE_CREDENTIALS:
                # Initialize Firebase Admin with credentials
                cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS)
                firebase_admin.initialize_app(cred, {
                    'storageBucket': Config.FIREBASE_STORAGE_BUCKET
                })
                print("Firebase initialized with credentials")
            else:
                # Initialize Firebase without credentials for limited functionality
                firebase_admin.initialize_app()
                print("Firebase initialized without credentials (limited functionality)")
        
        # Get Firestore client
        try:
            db = firestore.client()
            bucket = storage.bucket()
            print("Firebase services (Firestore and Storage) initialized successfully")
        except Exception as e:
            print(f"Could not initialize Firebase services: {e}")
            db = None
            bucket = None
        
        return db, bucket
        
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        print("Continuing without Firebase functionality")
        return None, None

# Initialize Firebase when this module is imported
try:
    db, storage_bucket = initialize_firebase()
except Exception as e:
    print(f"Firebase initialization failed: {e}")
    db, storage_bucket = None, None 