"""
CostCode service for Magellan EV Tracker v2.0
This service handles operations related to cost codes.
"""
from models import CostCode, Project, RuleOfCredit, DISCIPLINE_CHOICES
from services.base_service import BaseService
from sqlalchemy.orm import joinedload

class CostCodeService(BaseService):
    """Service for cost code-related operations"""
    
    def get_costcode_by_id(self, costcode_id):
        """Get a cost code by its ID"""
        return self.get_by_id(CostCode, costcode_id)
    
    def get_costcodes_by_project(self, project_id):
        """Get all cost codes for a specific project"""
        return self.filter_by(CostCode, project_id=project_id)
    
    def get_costcodes_by_discipline(self, discipline):
        """Get all cost codes for a specific discipline"""
        return self.filter_by(CostCode, discipline=discipline)
    
    def get_all_costcodes(self):
        """Get all cost codes with eager loading of relationships"""
        try:
            # Use joinedload to eagerly load related entities
            return CostCode.query.options(
                joinedload(CostCode.project),
                joinedload(CostCode.rule_of_credit)
            ).all()
        except Exception as e:
            print(f"Error getting all cost codes: {str(e)}")
            return []
    
    def get_discipline_choices(self):
        """Get all valid discipline choices"""
        return DISCIPLINE_CHOICES
    
    def create_costcode(self, cost_code_id_str, description, discipline, project_id, rule_of_credit_id=None):
        """Create a new cost code"""
        try:
            # Validate discipline
            if discipline not in DISCIPLINE_CHOICES:
                print(f"Invalid discipline: {discipline}")
                return None
            
            new_costcode = CostCode(
                cost_code_id_str=cost_code_id_str,
                description=description,
                discipline=discipline,
                project_id=project_id,
                rule_of_credit_id=rule_of_credit_id
            )
            self.add(new_costcode)
            self.commit()
            return new_costcode
        except Exception as e:
            print(f"Error creating cost code: {str(e)}")
            return None
    
    def update_costcode(self, costcode_id, description=None, discipline=None, rule_of_credit_id=None):
        """Update an existing cost code"""
        try:
            costcode = self.get_costcode_by_id(costcode_id)
            if not costcode:
                return None
            
            if description is not None:
                costcode.description = description
            if discipline is not None:
                # Validate discipline
                if discipline not in DISCIPLINE_CHOICES:
                    print(f"Invalid discipline: {discipline}")
                    return None
                costcode.discipline = discipline
            if rule_of_credit_id is not None:
                costcode.rule_of_credit_id = rule_of_credit_id
            
            self.commit()
            return costcode
        except Exception as e:
            print(f"Error updating cost code: {str(e)}")
            return None
    
    def delete_costcode(self, costcode_id):
        """Delete a cost code"""
        try:
            costcode = self.get_costcode_by_id(costcode_id)
            if not costcode:
                return False
            
            self.delete(costcode)
            self.commit()
            return True
        except Exception as e:
            print(f"Error deleting cost code: {str(e)}")
            return False
    
    def assign_rule_of_credit(self, costcode_id, rule_of_credit_id):
        """Assign a rule of credit to a cost code"""
        try:
            costcode = self.get_costcode_by_id(costcode_id)
            if not costcode:
                return False
            
            costcode.rule_of_credit_id = rule_of_credit_id
            self.commit()
            return True
        except Exception as e:
            print(f"Error assigning rule of credit: {str(e)}")
            return False
    
    def get_costcodes_with_projects(self):
        """Get all cost codes with their associated projects"""
        try:
            costcodes = self.get_all_costcodes()
            result = []
            
            for costcode in costcodes:
                # Get the project for this cost code
                project = Project.query.get(costcode.project_id)
                
                costcode_data = {
                    'costcode': costcode,
                    'project': project
                }
                
                result.append(costcode_data)
            
            return result
        except Exception as e:
            print(f"Error getting cost codes with projects: {str(e)}")
            return []
