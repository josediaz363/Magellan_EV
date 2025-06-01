"""
Template helpers for Magellan EV Tracker v3.0
Provides consistent URL generation and other helper functions for templates
"""
from flask import url_for, current_app


def generate_url(endpoint, **kwargs):
    """
    Template helper for consistent URL generation
    
    Args:
        endpoint (str): Flask endpoint name
        **kwargs: Parameters to include in the URL
        
    Returns:
        str: Properly formatted URL
    """
    # Try to get the endpoint rule
    try:
        endpoint_args = list(current_app.url_map.iter_rules(endpoint))
        if endpoint_args:
            # Extract URL parameters vs query parameters
            url_params = {}
            query_params = {}
            
            for k, v in kwargs.items():
                if k in endpoint_args[0].arguments:
                    url_params[k] = v
                else:
                    query_params[k] = v
                    
            # Generate base URL with URL parameters
            url = url_for(endpoint, **url_params)
            
            # Add query parameters if any
            if query_params:
                url += '?' + '&'.join([f"{k}={v}" for k, v in query_params.items()])
                
            return url
    except Exception as e:
        current_app.logger.error(f"Error generating URL for {endpoint}: {str(e)}")
    
    # Fallback to standard url_for
    return url_for(endpoint, **kwargs)


def register_template_helpers(app):
    """
    Register all template helpers with the Flask app
    
    Args:
        app: Flask application instance
    """
    @app.template_global()
    def url_for_entity(entity_type, action, **kwargs):
        """
        Generate URL for entity actions
        
        Args:
            entity_type (str): Type of entity (project, sub_job, cost_code, etc.)
            action (str): Action to perform (add, edit, view, delete)
            **kwargs: Additional parameters
            
        Returns:
            str: Properly formatted URL
        """
        endpoint = f'main.{action}_{entity_type}'
        return generate_url(endpoint, **kwargs)
    
    @app.template_global()
    def work_item_url(action, **kwargs):
        """
        Generate URL for work item actions
        
        Args:
            action (str): Action to perform (add, edit, view, delete)
            **kwargs: Additional parameters
            
        Returns:
            str: Properly formatted URL
        """
        endpoint = f'main.{action}_work_item'
        
        # Ensure sub_job_id is always a query parameter
        if 'sub_job_id' in kwargs:
            base_url = url_for(endpoint)
            query_params = '&'.join([f"{k}={v}" for k, v in kwargs.items()])
            return f"{base_url}?{query_params}"
        
        return generate_url(endpoint, **kwargs)
