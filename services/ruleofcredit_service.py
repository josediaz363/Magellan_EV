"""
RuleOfCredit service for Magellan EV Tracker v2.0
This service handles operations related to rules of credit.
"""
from models import RuleOfCredit
from services.base_service import BaseService
import json

class RuleOfCreditService(BaseService):
    """Service for rule of credit-related operations"""
    
    def get_ruleofcredit_by_id(self, ruleofcredit_id):
        """Get a rule of credit by its ID"""
        return self.get_by_id(RuleOfCredit, ruleofcredit_id)
    
    def get_all_rulesofcredit(self):
        """Get all rules of credit"""
        return self.get_all(RuleOfCredit)
    
    def create_ruleofcredit(self, name, description, steps=None):
        """Create a new rule of credit"""
        try:
            new_ruleofcredit = RuleOfCredit(
                name=name,
                description=description,
                steps_json="[]" if steps is None else json.dumps(steps)
            )
            self.add(new_ruleofcredit)
            self.commit()
            return new_ruleofcredit
        except Exception as e:
            print(f"Error creating rule of credit: {str(e)}")
            return None
    
    def update_ruleofcredit(self, ruleofcredit_id, name=None, description=None, steps=None):
        """Update an existing rule of credit"""
        try:
            ruleofcredit = self.get_ruleofcredit_by_id(ruleofcredit_id)
            if not ruleofcredit:
                return None
            
            if name is not None:
                ruleofcredit.name = name
            if description is not None:
                ruleofcredit.description = description
            if steps is not None:
                ruleofcredit.steps_json = json.dumps(steps)
            
            self.commit()
            return ruleofcredit
        except Exception as e:
            print(f"Error updating rule of credit: {str(e)}")
            return None
    
    def delete_ruleofcredit(self, ruleofcredit_id):
        """Delete a rule of credit"""
        try:
            ruleofcredit = self.get_ruleofcredit_by_id(ruleofcredit_id)
            if not ruleofcredit:
                return False
            
            self.delete(ruleofcredit)
            self.commit()
            return True
        except Exception as e:
            print(f"Error deleting rule of credit: {str(e)}")
            return False
    
    def get_steps(self, ruleofcredit_id):
        """Get steps for a rule of credit"""
        try:
            ruleofcredit = self.get_ruleofcredit_by_id(ruleofcredit_id)
            if not ruleofcredit:
                return []
            
            return ruleofcredit.get_steps()
        except Exception as e:
            print(f"Error getting steps: {str(e)}")
            return []
    
    def set_steps(self, ruleofcredit_id, steps):
        """Set steps for a rule of credit"""
        try:
            ruleofcredit = self.get_ruleofcredit_by_id(ruleofcredit_id)
            if not ruleofcredit:
                return False
            
            ruleofcredit.set_steps(steps)
            self.commit()
            return True
        except Exception as e:
            print(f"Error setting steps: {str(e)}")
            return False
    
    def add_step(self, ruleofcredit_id, step_name, weight):
        """Add a step to a rule of credit"""
        try:
            ruleofcredit = self.get_ruleofcredit_by_id(ruleofcredit_id)
            if not ruleofcredit:
                return False
            
            steps = ruleofcredit.get_steps()
            steps.append({
                "name": step_name,
                "weight": float(weight)
            })
            
            ruleofcredit.set_steps(steps)
            self.commit()
            return True
        except Exception as e:
            print(f"Error adding step: {str(e)}")
            return False
    
    def update_step(self, ruleofcredit_id, step_index, step_name=None, weight=None):
        """Update a step in a rule of credit"""
        try:
            ruleofcredit = self.get_ruleofcredit_by_id(ruleofcredit_id)
            if not ruleofcredit:
                return False
            
            steps = ruleofcredit.get_steps()
            if step_index < 0 or step_index >= len(steps):
                return False
            
            if step_name is not None:
                steps[step_index]["name"] = step_name
            if weight is not None:
                steps[step_index]["weight"] = float(weight)
            
            ruleofcredit.set_steps(steps)
            self.commit()
            return True
        except Exception as e:
            print(f"Error updating step: {str(e)}")
            return False
    
    def delete_step(self, ruleofcredit_id, step_index):
        """Delete a step from a rule of credit"""
        try:
            ruleofcredit = self.get_ruleofcredit_by_id(ruleofcredit_id)
            if not ruleofcredit:
                return False
            
            steps = ruleofcredit.get_steps()
            if step_index < 0 or step_index >= len(steps):
                return False
            
            steps.pop(step_index)
            ruleofcredit.set_steps(steps)
            self.commit()
            return True
        except Exception as e:
            print(f"Error deleting step: {str(e)}")
            return False
