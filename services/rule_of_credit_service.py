"""
Updated RuleOfCredit service for Magellan EV Tracker v3.0
- Fixes parameter naming to align with database model
- Ensures consistent use of steps_json across all components
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
    def get_rule_of_credit_by_id(rule_id):
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
    def create_rule_of_credit(name, description, steps_json):
        """
        Create a new rule of credit
        
        Args:
            name (str): Rule name
            description (str): Rule description
            steps_json (str): JSON string containing steps and weights
            
        Returns:
            RuleOfCredit: Newly created rule of credit
        """
        rule = RuleOfCredit(
            name=name,
            description=description,
            steps_json=steps_json
        )
        db.session.add(rule)
        db.session.commit()
        return rule
    
    @staticmethod
    def update_rule_of_credit(rule_id, name, description, steps_json):
        """
        Update an existing rule of credit
        
        Args:
            rule_id (int): Rule of Credit ID
            name (str): New rule name
            description (str): New rule description
            steps_json (str): JSON string containing steps and weights
            
        Returns:
            RuleOfCredit: Updated rule of credit
        """
        rule = RuleOfCredit.query.get(rule_id)
        if rule:
            rule.name = name
            rule.description = description
            rule.steps_json = steps_json
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
            
        # Implementation using steps_json instead of formula
        try:
            steps = rule.get_steps()
            if not steps:
                return {
                    'earned_quantity': 0.0,
                    'earned_man_hours': 0.0
                }
                
            # For simplicity, we'll use the total of all step weights as the percentage
            total_percentage = sum(float(step.get('weight', 0)) for step in steps)
            
            earned_quantity = (quantity * total_percentage) / 100.0
            earned_man_hours = (man_hours * total_percentage) / 100.0
            
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
