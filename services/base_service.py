"""
Base service class for Magellan EV Tracker v2.0
This class provides common functionality for all service classes.
"""
from models import db

class BaseService:
    """Base service class with common functionality for all services"""
    
    def __init__(self):
        """Initialize the service"""
        self.db = db
    
    def commit(self):
        """Commit changes to the database"""
        try:
            self.db.session.commit()
            return True
        except Exception as e:
            self.db.session.rollback()
            print(f"Error committing changes: {str(e)}")
            return False
    
    def add(self, obj):
        """Add an object to the database"""
        try:
            self.db.session.add(obj)
            return True
        except Exception as e:
            print(f"Error adding object: {str(e)}")
            return False
    
    def delete(self, obj):
        """Delete an object from the database"""
        try:
            self.db.session.delete(obj)
            return True
        except Exception as e:
            print(f"Error deleting object: {str(e)}")
            return False
    
    def get_by_id(self, model_class, id):
        """Get an object by its ID"""
        try:
            return model_class.query.get(id)
        except Exception as e:
            print(f"Error getting object by ID: {str(e)}")
            return None
    
    def get_all(self, model_class):
        """Get all objects of a given model class"""
        try:
            return model_class.query.all()
        except Exception as e:
            print(f"Error getting all objects: {str(e)}")
            return []
    
    def filter_by(self, model_class, **kwargs):
        """Filter objects by given criteria"""
        try:
            return model_class.query.filter_by(**kwargs).all()
        except Exception as e:
            print(f"Error filtering objects: {str(e)}")
            return []
