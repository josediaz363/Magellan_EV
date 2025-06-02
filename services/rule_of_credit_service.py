"""
Fixed RuleOfCreditService with count_rules_of_credit method for Magellan EV Tracker v3.0
- Added missing count_rules_of_credit method required by dashboard
- Enhanced error handling and logging
"""
from models import RuleOfCredit, db
import logging

# Configure logging
logger = logging.getLogger(__name__)

class RuleOfCreditService:
    """
    Service for rule of credit-related operations
    """
    
    @staticmethod
    def get_all_rules_of_credit():
        """
        Get all rules of credit
        
        Returns:
            list: List of all rules of credit
        """
        try:
            rules = RuleOfCredit.query.all()
            logger.info(f"Retrieved {len(rules)} rules of credit")
            return rules
        except Exception as e:
            logger.error(f"Error retrieving all rules of credit: {str(e)}")
            return []
    
    @staticmethod
    def get_rule_of_credit_by_id(rule_id):
        """
        Get rule of credit by ID
        
        Args:
            rule_id (int): Rule of Credit ID
            
        Returns:
            RuleOfCredit: Rule of Credit object
        """
        try:
            rule = RuleOfCredit.query.get(rule_id)
            if rule:
                logger.info(f"Retrieved rule of credit: {rule.id}, {rule.name}")
            return rule
        except Exception as e:
            logger.error(f"Error retrieving rule of credit {rule_id}: {str(e)}")
            return None
    
    @staticmethod
    def count_rules_of_credit():
        """
        Count total number of rules of credit
        
        Returns:
            int: Count of rules of credit
        """
        try:
            count = RuleOfCredit.query.count()
            logger.info(f"Counted {count} rules of credit")
            return count
        except Exception as e:
            logger.error(f"Error counting rules of credit: {str(e)}")
            return 0
    
    @staticmethod
    def create_rule_of_credit(name, description, formula):
        """
        Create a new rule of credit
        
        Args:
            name (str): Rule name
            description (str): Rule description
            formula (str): Rule formula
            
        Returns:
            RuleOfCredit: Newly created rule of credit
        """
        try:
            rule = RuleOfCredit(
                name=name,
                description=description,
                formula=formula
            )
            db.session.add(rule)
            db.session.commit()
            logger.info(f"Rule of credit created successfully: {rule.id}, {rule.name}")
            return rule
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating rule of credit: {str(e)}")
            raise
    
    @staticmethod
    def update_rule_of_credit(rule_id, name, description, formula):
        """
        Update an existing rule of credit
        
        Args:
            rule_id (int): Rule of Credit ID
            name (str): New rule name
            description (str): New rule description
            formula (str): New rule formula
            
        Returns:
            RuleOfCredit: Updated rule of credit
        """
        try:
            rule = RuleOfCredit.query.get(rule_id)
            if rule:
                rule.name = name
                rule.description = description
                rule.formula = formula
                db.session.commit()
                logger.info(f"Rule of credit updated successfully: {rule.id}, {rule.name}")
            return rule
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating rule of credit {rule_id}: {str(e)}")
            raise
    
    @staticmethod
    def delete_rule_of_credit(rule_id):
        """
        Delete a rule of credit
        
        Args:
            rule_id (int): Rule of Credit ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            rule = RuleOfCredit.query.get(rule_id)
            if rule:
                db.session.delete(rule)
                db.session.commit()
                logger.info(f"Rule of credit deleted successfully: {rule_id}")
                return True
            return False
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting rule of credit {rule_id}: {str(e)}")
            return False
