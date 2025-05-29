"""
Base service class for Magellan EV Tracker v2.0
This class provides common database operations for all service classes.
"""

from models import db

class BaseService:
    """Base service class with common database operations"""
    
    def __init__(self):
        self.db = db
        
    def commit(self):
        """Commit changes to database"""
        try:
            self.db.session.commit()
            return True
        except Exception as e:
            self.db.session.rollback()
            print(f"Database error: {str(e)}")
            return False
            
    def add(self, obj):
        """Add object to database"""
        try:
            self.db.session.add(obj)
            return True
        except Exception as e:
            print(f"Error adding to database: {str(e)}")
            return False
            
    def delete(self, obj):
        """Delete object from database"""
        try:
            self.db.session.delete(obj)
            return True
        except Exception as e:
            print(f"Error deleting from database: {str(e)}")
            return False
