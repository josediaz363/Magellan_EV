"""
RuleOfCredit service for Magellan EV Tracker v3.0
Provides data access and business logic for rules of credit
"""
from models import RuleOfCredit, db


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
        return RuleOfCredit.query.all()
    
    @staticmethod
    def get_rule_of_credit_details(rule_id):
        """
        Get rule of credit details
        
        Args:
            rule_id (int): Rule of Credit ID
            
        Returns:
            RuleOfCredit: Rule of Credit object
        """
        if not rule_id:
            return None
            
        return RuleOfCredit.query.get(rule_id)
    
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
        rule = RuleOfCredit(
            name=name,
            description=description,
            formula=formula
        )
        db.session.add(rule)
        db.session.commit()
        return rule
    
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
        rule = RuleOfCredit.query.get(rule_id)
        if rule:
            rule.name = name
            rule.description = description
            rule.formula = formula
            db.session.commit()
        return rule
    
    @staticmethod
    def delete_rule_of_credit(rule_id):
        """
        Delete a rule of credit
        
        Args:
            rule_id (int): Rule of Credit ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        rule = RuleOfCredit.query.get(rule_id)
        if rule:
            db.session.delete(rule)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def apply_rule_of_credit(rule_id, quantity, man_hours):
        """
        Apply a rule of credit to calculate earned values
        
        Args:
            rule_id (int): Rule of Credit ID
            quantity (float): Quantity value
            man_hours (float): Man hours value
            
        Returns:
            dict: Dictionary with calculated earned values
        """
        rule = RuleOfCredit.query.get(rule_id)
        if not rule:
            return {
                'earned_quantity': 0.0,
                'earned_man_hours': 0.0
            }
            
        # Basic implementation - in a real system, this would evaluate the formula
        # For now, we'll use a simple percentage calculation
        try:
            # Parse the formula (simplified for this implementation)
            percentage = 100.0  # Default to 100%
            if rule.formula and '%' in rule.formula:
                percentage_str = rule.formula.split('%')[0].strip()
                percentage = float(percentage_str)
                
            earned_quantity = (quantity * percentage) / 100.0
            earned_man_hours = (man_hours * percentage) / 100.0
            
            return {
                'earned_quantity': round(earned_quantity, 2),
                'earned_man_hours': round(earned_man_hours, 2)
            }
        except Exception as e:
            print(f"Error applying rule of credit: {str(e)}")
            return {
                'earned_quantity': 0.0,
                'earned_man_hours': 0.0
            }
