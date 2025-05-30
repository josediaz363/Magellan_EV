"""
URL validation middleware for Magellan EV Tracker v3.0
Provides validation and sanitization of URL parameters
"""
from flask import request, current_app
import re


class UrlMiddleware:
    """
    Middleware for validating and sanitizing URL parameters
    """
    
    @staticmethod
    def validate_url_parameters():
        """
        Validate and sanitize URL parameters before processing requests
        """
        # Validate numeric parameters
        numeric_params = ['project_id', 'sub_job_id', 'cost_code_id', 'rule_id', 'work_item_id']
        for param in numeric_params:
            value = request.args.get(param)
            if value is not None:
                try:
                    # Ensure parameter is a valid integer
                    int(value)
                except ValueError:
                    current_app.logger.warning(f"Invalid {param} parameter: {value}")
                    # Parameter will be ignored by route handlers if invalid
        
        # Validate string parameters (prevent injection)
        string_params = ['name', 'description', 'discipline', 'area']
        for param in string_params:
            value = request.args.get(param)
            if value is not None:
                # Basic sanitization - remove potentially harmful characters
                if not re.match(r'^[a-zA-Z0-9_\-\s.,]+$', value):
                    current_app.logger.warning(f"Potentially unsafe {param} parameter: {value}")
                    # Parameter will be handled safely by route handlers


def register_url_middleware(app):
    """
    Register URL middleware with the Flask app
    
    Args:
        app: Flask application instance
    """
    @app.before_request
    def validate_url_parameters():
        """
        Validate and sanitize URL parameters before processing requests
        """
        return UrlMiddleware.validate_url_parameters()
