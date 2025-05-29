"""
RuleOfCredit service for Magellan EV Tracker v2.0
This service handles operations related to rules of credit.
"""

from models import RuleOfCredit, RuleOfCreditStep
from services.base_service import BaseService
import json

class RuleOfCreditService(BaseService):
    """Service for rule of credit-related operations"""
    
    def get_all_rulesofcredit(self):
        """Get all rules of credit"""
        try:
            return RuleOfCredit.query.all()
        except Exception as e:
            print(f"Error getting rules of credit: {str(e)}")
            return []
            
    def get_ruleofcredit_by_id(self, rule_id):
        """Get rule of credit by ID"""
        try:
            return RuleOfCredit.query.get(rule_id)
        except Exception as e:
            print(f"Error getting rule of credit: {str(e)}")
            return None
            
    def create_ruleofcredit(self, name, description):
        """Create a new rule of credit"""
        try:
            rule = RuleOfCredit(
                name=name,
                description=description
            )
            self.add(rule)
            self.commit()
            return rule
        except Exception as e:
            print(f"Error creating rule of credit: {str(e)}")
            return None
            
    def update_ruleofcredit(self, rule_id, name, description, steps=None):
        """Update an existing rule of credit"""
        try:
            rule = self.get_ruleofcredit_by_id(rule_id)
            if not rule:
                return None
                
            rule.name = name
            rule.description = description
            
            # Update steps if provided
            if steps is not None:
                # Delete existing steps
                RuleOfCreditStep.query.filter_by(rule_of_credit_id=rule_id).delete()
                self.commit()
                
                # Add new steps
                for i, step in enumerate(steps):
                    step_obj = RuleOfCreditStep(
                        rule_of_credit_id=rule_id,
                        name=step['name'],
                        weight=step['weight'],
                        order=i
                    )
                    self.add(step_obj)
            
            self.commit()
            return rule
        except Exception as e:
            print(f"Error updating rule of credit: {str(e)}")
            return None
            
    def delete_ruleofcredit(self, rule_id):
        """Delete a rule of credit"""
        try:
            rule = self.get_ruleofcredit_by_id(rule_id)
            if not rule:
                return False
                
            # Delete steps
            RuleOfCreditStep.query.filter_by(rule_of_credit_id=rule_id).delete()
            
            self.delete(rule)
            self.commit()
            return True
        except Exception as e:
            print(f"Error deleting rule of credit: {str(e)}")
            return False
            
    def get_steps(self, rule_id):
        """Get steps for a rule of credit"""
        try:
            steps = RuleOfCreditStep.query.filter_by(rule_of_credit_id=rule_id).order_by(RuleOfCreditStep.order).all()
            return [{'name': step.name, 'weight': step.weight} for step in steps]
        except Exception as e:
            print(f"Error getting steps: {str(e)}")
            return []
