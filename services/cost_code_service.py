"""
CostCode service for Magellan EV Tracker v3.0
Provides data access and business logic for cost codes
"""
from models import CostCode, RuleOfCredit, db


class CostCodeService:
    """
    Service for cost code-related operations
    """
    
    @staticmethod
    def get_all_cost_codes():
        """
        Get all cost codes
        
        Returns:
            list: List of all cost codes
        """
        return CostCode.query.all()
    
    @staticmethod
    def get_cost_code_details(cost_code_id):
        """
        Get cost code details with all necessary related data
        
        Args:
            cost_code_id (int): Cost Code ID
            
        Returns:
            CostCode: Cost Code object with related data
        """
        if not cost_code_id:
            return None
            
        return CostCode.query.get(cost_code_id)
    
    @staticmethod
    def get_project_cost_codes(project_id):
        """
        Get all cost codes for a project
        
        Args:
            project_id (int): Project ID
            
        Returns:
            list: List of cost codes for the project
        """
        return CostCode.query.filter_by(project_id=project_id).all()
    
    @staticmethod
    def create_cost_code(project_id, code, description, rule_of_credit_id=None):
        """
        Create a new cost code
        
        Args:
            project_id (int): Project ID
            code (str): Cost code
            description (str): Cost code description
            rule_of_credit_id (int, optional): Rule of Credit ID
            
        Returns:
            CostCode: Newly created cost code
        """
        cost_code = CostCode(
            project_id=project_id,
            code=code,
            description=description,
            rule_of_credit_id=rule_of_credit_id
        )
        db.session.add(cost_code)
        db.session.commit()
        return cost_code
    
    @staticmethod
    def update_cost_code(cost_code_id, code, description, rule_of_credit_id=None):
        """
        Update an existing cost code
        
        Args:
            cost_code_id (int): Cost Code ID
            code (str): New cost code
            description (str): New cost code description
            rule_of_credit_id (int, optional): New Rule of Credit ID
            
        Returns:
            CostCode: Updated cost code
        """
        cost_code = CostCode.query.get(cost_code_id)
        if cost_code:
            cost_code.code = code
            cost_code.description = description
            cost_code.rule_of_credit_id = rule_of_credit_id
            db.session.commit()
        return cost_code
    
    @staticmethod
    def delete_cost_code(cost_code_id):
        """
        Delete a cost code
        
        Args:
            cost_code_id (int): Cost Code ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        cost_code = CostCode.query.get(cost_code_id)
        if cost_code:
            db.session.delete(cost_code)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def get_available_rules_of_credit():
        """
        Get all available rules of credit
        
        Returns:
            list: List of all rules of credit
        """
        return RuleOfCredit.query.all()
