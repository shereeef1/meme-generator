import os
import json
from datetime import datetime
import docx
import logging
from typing import List, Dict, Optional

class DocumentManager:
    """Class to handle document storage, history, and management"""
    
    def __init__(self):
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Set up directories
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.docs_dir = os.path.join(self.base_dir, 'documents')
        self.history_file = os.path.join(self.docs_dir, 'history.json')
        
        # Create necessary directories
        os.makedirs(self.docs_dir, exist_ok=True)
        
        # Initialize history
        self._init_history()
    
    def _init_history(self):
        """Initialize or load document history"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
            except:
                self.history = []
                self._save_history()
        else:
            self.history = []
            self._save_history()
    
    def _save_history(self):
        """Save document history to file"""
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def add_document(self, doc_path: str, source_url: str, category: str = None, country: str = None) -> Dict:
        """
        Add a document to history
        
        Args:
            doc_path (str): Path to the document
            source_url (str): Original URL for scraped content
            category (str, optional): Brand category
            country (str, optional): Brand's primary country
            
        Returns:
            dict: Document entry
        """
        doc_name = os.path.basename(doc_path)
        entry = {
            "id": len(self.history) + 1,
            "filename": doc_name,
            "path": doc_path,
            "source_url": source_url,
            "category": category,
            "country": country,
            "created_at": datetime.now().isoformat(),
            "file_size": os.path.getsize(doc_path)
        }
        
        self.history.append(entry)
        self._save_history()
        return entry
    
    def get_document_history(self, limit: int = None, offset: int = 0) -> List[Dict]:
        """
        Get document history
        
        Args:
            limit (int, optional): Number of entries to return
            offset (int, optional): Number of entries to skip
            
        Returns:
            list: List of document entries
        """
        if limit:
            return self.history[offset:offset + limit]
        return self.history[offset:]
    
    def get_document(self, doc_id: int) -> Optional[Dict]:
        """
        Get document by ID
        
        Args:
            doc_id (int): Document ID
            
        Returns:
            dict: Document entry or None if not found
        """
        for entry in self.history:
            if entry["id"] == doc_id:
                return entry
        return None
    
    def update_document_content(self, doc_path: str, new_content: str) -> bool:
        """
        Update document content
        
        Args:
            doc_path (str): Path to the document
            new_content (str): New content to write
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create new document
            doc = docx.Document()
            
            # Add content
            paragraphs = new_content.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    doc.add_paragraph(para.strip())
            
            # Save document
            doc.save(doc_path)
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating document: {str(e)}")
            return False
    
    def delete_document(self, doc_id: int) -> bool:
        """
        Delete document by ID
        
        Args:
            doc_id (int): Document ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        for i, entry in enumerate(self.history):
            if entry["id"] == doc_id:
                try:
                    # Delete file
                    if os.path.exists(entry["path"]):
                        os.remove(entry["path"])
                    
                    # Remove from history
                    self.history.pop(i)
                    self._save_history()
                    return True
                except Exception as e:
                    self.logger.error(f"Error deleting document: {str(e)}")
                    return False
        return False 