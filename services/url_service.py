"""
URL Service for Magellan EV Tracker v3.0
- Provides URL handling and generation functionality
- Ensures consistent URL formatting across the application
"""

class UrlService:
    """
    Service for handling URL operations in the Magellan EV Tracker application.
    """
    
    @staticmethod
    def get_base_url():
        """
        Returns the base URL for the application.
        """
        return ""
    
    @staticmethod
    def format_url(url):
        """
        Formats a URL to ensure consistency.
        """
        if not url:
            return ""
        
        # Remove trailing slashes
        while url.endswith('/'):
            url = url[:-1]
            
        return url
    
    @staticmethod
    def join_url_parts(*parts):
        """
        Joins URL parts together, ensuring proper formatting.
        """
        if not parts:
            return ""
            
        # Filter out empty parts
        filtered_parts = [part for part in parts if part]
        
        if not filtered_parts:
            return ""
            
        # Join parts with a single slash
        result = "/".join(filtered_parts)
        
        # Ensure no double slashes
        while "//" in result:
            result = result.replace("//", "/")
            
        return result
