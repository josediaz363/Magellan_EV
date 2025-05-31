"""
URL Service module for Magellan EV Tracker v3.0
Provides consistent URL generation across the application
"""
from flask import url_for, current_app


class UrlService:
    """
    Service for generating consistent URLs throughout the application.
    Ensures proper handling of URL parameters vs. query parameters.
    """
    
    @staticmethod
    def work_item_url(action, **params):
        """
        Generate consistent URLs for work item actions
        
        Args:
            action (str): Action to perform (add, edit, view, delete)
            **params: Parameters to include in the URL
            
        Returns:
            str: Properly formatted URL
        """
        base_url = url_for(f'main.{action}_work_item')
        query_params = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_params}" if query_params else base_url
    
    @staticmethod
    def project_url(action, project_id=None, **params):
        """
        Generate consistent URLs for project actions
        
        Args:
            action (str): Action to perform (add, edit, view, delete)
            project_id (int, optional): Project ID
            **params: Additional parameters to include in the URL
            
        Returns:
            str: Properly formatted URL
        """
        if action == 'view' and project_id:
            # View uses URL parameter
            base_url = url_for(f'main.{action}_project', project_id=project_id)
        else:
            # Other actions use query parameters
            base_url = url_for(f'main.{action}_project')
            if project_id:
                params['project_id'] = project_id
                
        query_params = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_params}" if query_params else base_url
    
    @staticmethod
    def sub_job_url(action, sub_job_id=None, project_id=None, **params):
        """
        Generate consistent URLs for sub job actions
        
        Args:
            action (str): Action to perform (add, edit, view, delete)
            sub_job_id (int, optional): Sub Job ID
            project_id (int, optional): Project ID
            **params: Additional parameters to include in the URL
            
        Returns:
            str: Properly formatted URL
        """
        if action == 'view' and sub_job_id:
            # View uses URL parameter
            base_url = url_for(f'main.{action}_sub_job', sub_job_id=sub_job_id)
        else:
            # Other actions use query parameters
            base_url = url_for(f'main.{action}_sub_job')
            if sub_job_id:
                params['sub_job_id'] = sub_job_id
            if project_id:
                params['project_id'] = project_id
                
        query_params = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_params}" if query_params else base_url
    
    @staticmethod
    def cost_code_url(action, cost_code_id=None, project_id=None, **params):
        """
        Generate consistent URLs for cost code actions
        
        Args:
            action (str): Action to perform (add, edit, view, delete)
            cost_code_id (int, optional): Cost Code ID
            project_id (int, optional): Project ID
            **params: Additional parameters to include in the URL
            
        Returns:
            str: Properly formatted URL
        """
        if action == 'view' and cost_code_id:
            # View uses URL parameter
            base_url = url_for(f'main.{action}_cost_code', cost_code_id=cost_code_id)
        else:
            # Other actions use query parameters
            base_url = url_for(f'main.{action}_cost_code')
            if cost_code_id:
                params['cost_code_id'] = cost_code_id
            if project_id:
                params['project_id'] = project_id
                
        query_params = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_params}" if query_params else base_url
    
    @staticmethod
    def rule_of_credit_url(action, rule_id=None, **params):
        """
        Generate consistent URLs for rule of credit actions
        
        Args:
            action (str): Action to perform (add, edit, view, delete)
            rule_id (int, optional): Rule of Credit ID
            **params: Additional parameters to include in the URL
            
        Returns:
            str: Properly formatted URL
        """
        if action == 'view' and rule_id:
            # View uses URL parameter
            base_url = url_for(f'main.{action}_rule_of_credit', rule_id=rule_id)
        else:
            # Other actions use query parameters
            base_url = url_for(f'main.{action}_rule_of_credit')
            if rule_id:
                params['rule_id'] = rule_id
                
        query_params = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_params}" if query_params else base_url
