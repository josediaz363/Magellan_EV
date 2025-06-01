"""
CostCode service for Magellan EV Tracker v3.0
Provides data access and business logic for cost codes
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
        cost_codes = CostCode.query.all()
        logger.info(f"Retrieved {len(cost_codes)} cost codes from database")
        for code in cost_codes:
            logger.info(f"Cost code: ID={code.id}, Code={code.cost_code_id_str}, Project ID={code.project_id}")
        return cost_codes
    
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
        logger.info(f"Retrieving cost codes for project_id: {project_id}")
        
        # Use a direct SQL query to ensure we're getting the right data
        # This bypasses any potential ORM relationship issues
        cost_codes = db.session.query(CostCode).filter(CostCode.project_id == project_id).all()
        
        logger.info(f"Found {len(cost_codes)} cost codes for project_id {project_id}")
        for code in cost_codes:
            logger.info(f"Project cost code: ID={code.id}, Code={code.cost_code_id_str}, Project ID={code.project_id}")
        
        return cost_codes
    
    @staticmethod
    def create_cost_code(project_id, code, description, discipline, rule_of_credit_id=None):
        """
        Create a new cost code
        
        Args:
            project_id (int): Project ID
            code (str): Cost code
            description (str): Cost code description
            discipline (str): Discipline for the cost code
            rule_of_credit_id (int, optional): Rule of Credit ID
            
        Returns:
            CostCode: Newly created cost code
        """
        logger.info(f"Creating cost code: project_id={project_id}, code={code}, discipline={discipline}")
        
        # Ensure project_id is an integer
        try:
            project_id = int(project_id)
        except (TypeError, ValueError):
            logger.error(f"Invalid project_id: {project_id}")
            raise ValueError(f"Invalid project_id: {project_id}")
        
        cost_code = CostCode(
            project_id=project_id,
            cost_code_id_str=code,  # Map code to cost_code_id_str in the model
            description=description,
            discipline=discipline,
            rule_of_credit_id=rule_of_credit_id
        )
        
        # Log the cost code object before adding to session
        logger.info(f"Cost code object created: project_id={cost_code.project_id}, code={cost_code.cost_code_id_str}")
        
        db.session.add(cost_code)
        db.session.commit()
        
        # Log the cost code object after commit to confirm ID assignment
        logger.info(f"Cost code committed to database: ID={cost_code.id}, Project ID={cost_code.project_id}")
        
        # Verify the cost code was actually saved by retrieving it
        saved_code = CostCode.query.get(cost_code.id)
        if saved_code:
            logger.info(f"Successfully retrieved saved cost code: ID={saved_code.id}, Project ID={saved_code.project_id}")
        else:
            logger.error(f"Failed to retrieve saved cost code with ID={cost_code.id}")
        
        return cost_code
    
    @staticmethod
    def update_cost_code(cost_code_id, code, description, discipline, rule_of_credit_id=None):
        """
        Update an existing cost code
        
        Args:
            cost_code_id (int): Cost Code ID
            code (str): New cost code
            description (str): New cost code description
            discipline (str): New discipline for the cost code
            rule_of_credit_id (int, optional): New Rule of Credit ID
            
        Returns:
            CostCode: Updated cost code
        """
        cost_code = CostCode.query.get(cost_code_id)
        if cost_code:
            cost_code.cost_code_id_str = code  # Map code to cost_code_id_str in the model
            cost_code.description = description
            cost_code.discipline = discipline
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
