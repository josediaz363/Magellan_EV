"""
Fixed CostCodeService for Magellan EV Tracker v3.0
- Corrected field name mismatches (code → cost_code_id_str)
- Added missing required parameters (discipline)
- Improved transaction management and error handling
- Ensures proper database persistence on Railway
"""
from models import CostCode, RuleOfCredit, db
import logging

# Configure logging
logger = logging.getLogger(__name__)

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
        try:
            cost_codes = CostCode.query.all()
            logger.info(f"Retrieved {len(cost_codes)} cost codes")
            return cost_codes
        except Exception as e:
            logger.error(f"Error retrieving all cost codes: {str(e)}")
            return []
    
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
        
        try:
            cost_code = CostCode.query.get(cost_code_id)
            if cost_code:
                logger.info(f"Retrieved cost code: {cost_code.id}, {cost_code.cost_code_id_str}")
            return cost_code
        except Exception as e:
            logger.error(f"Error retrieving cost code {cost_code_id}: {str(e)}")
            return None
    
    @staticmethod
    def get_project_cost_codes(project_id):
        """
        Get all cost codes for a project
        
        Args:
            project_id (int): Project ID
            
        Returns:
            list: List of cost codes for the project
        """
        try:
            # Ensure project_id is an integer
            project_id = int(project_id) if project_id else None
            
            if not project_id:
                logger.warning("No project_id provided for get_project_cost_codes")
                return []
            
            cost_codes = CostCode.query.filter_by(project_id=project_id).all()
            logger.info(f"Retrieved {len(cost_codes)} cost codes for project {project_id}")
            
            # Log each cost code for debugging
            for cc in cost_codes:
                logger.info(f"Cost code: {cc.id}, {cc.cost_code_id_str}, project_id={cc.project_id}")
                
            return cost_codes
        except Exception as e:
            logger.error(f"Error retrieving cost codes for project {project_id}: {str(e)}")
            return []
    
    @staticmethod
    def create_cost_code(project_id, code, description, discipline, rule_of_credit_id=None):
        """
        Create a new cost code
        
        Args:
            project_id (int): Project ID
            code (str): Cost code ID string
            description (str): Cost code description
            discipline (str): Discipline category
            rule_of_credit_id (int, optional): Rule of Credit ID
            
        Returns:
            CostCode: Newly created cost code
        """
        try:
            # Ensure project_id is an integer
            project_id = int(project_id) if project_id else None
            
            if not project_id:
                logger.error("Cannot create cost code: No project_id provided")
                raise ValueError("Project ID is required")
                
            # Log creation attempt
            logger.info(f"Creating cost code: {code} for project {project_id}, discipline={discipline}")
            
            # Create cost code with correct field names
            cost_code = CostCode(
                project_id=project_id,
                cost_code_id_str=code,  # Match the model field name
                description=description,
                discipline=discipline,   # Required field
                rule_of_credit_id=rule_of_credit_id
            )
            
            # Add and commit with explicit transaction
            db.session.add(cost_code)
            db.session.commit()
            
            # Verify the cost code was saved
            saved_cost_code = CostCode.query.filter_by(cost_code_id_str=code).first()
            if saved_cost_code:
                logger.info(f"Cost code created successfully: {saved_cost_code.id}, {saved_cost_code.cost_code_id_str}")
            else:
                logger.warning(f"Cost code created but not found in verification query: {code}")
                
            return cost_code
        except Exception as e:
            # Explicit rollback on error
            db.session.rollback()
            logger.error(f"Error creating cost code: {str(e)}")
            raise
    
    @staticmethod
    def update_cost_code(cost_code_id, code, description, discipline, rule_of_credit_id=None):
        """
        Update an existing cost code
        
        Args:
            cost_code_id (int): Cost Code ID
            code (str): New cost code ID string
            description (str): New cost code description
            discipline (str): Discipline category
            rule_of_credit_id (int, optional): New Rule of Credit ID
            
        Returns:
            CostCode: Updated cost code
        """
        try:
            cost_code = CostCode.query.get(cost_code_id)
            if cost_code:
                cost_code.cost_code_id_str = code  # Match the model field name
                cost_code.description = description
                cost_code.discipline = discipline   # Required field
                cost_code.rule_of_credit_id = rule_of_credit_id
                db.session.commit()
                logger.info(f"Cost code updated successfully: {cost_code.id}, {cost_code.cost_code_id_str}")
            return cost_code
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating cost code {cost_code_id}: {str(e)}")
            raise
    
    @staticmethod
    def delete_cost_code(cost_code_id):
        """
        Delete a cost code
        
        Args:
            cost_code_id (int): Cost Code ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            cost_code = CostCode.query.get(cost_code_id)
            if cost_code:
                db.session.delete(cost_code)
                db.session.commit()
                logger.info(f"Cost code deleted successfully: {cost_code_id}")
                return True
            return False
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting cost code {cost_code_id}: {str(e)}")
            return False
    
    @staticmethod
    def get_available_rules_of_credit():
        """
        Get all available rules of credit
        
        Returns:
            list: List of all rules of credit
        """
        try:
            rules = RuleOfCredit.query.all()
            logger.info(f"Retrieved {len(rules)} rules of credit")
            return rules
        except Exception as e:
            logger.error(f"Error retrieving rules of credit: {str(e)}")
            return []
