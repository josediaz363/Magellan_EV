"""
CostCode service for Magellan EV Tracker v2.0
This service handles operations related to cost codes.
"""

from models import CostCode, ProjectCostCode, DISCIPLINE_CHOICES
from services.base_service import BaseService

class CostCodeService(BaseService):
    """Service for cost code-related operations"""
    
    def get_all_costcodes(self):
        """Get all cost codes"""
        try:
            return CostCode.query.all()
        except Exception as e:
            print(f"Error getting cost codes: {str(e)}")
            return []
            
    def get_costcode_by_id(self, costcode_id):
        """Get cost code by ID"""
        try:
            return CostCode.query.get(costcode_id)
        except Exception as e:
            print(f"Error getting cost code: {str(e)}")
            return None
            
    def get_costcodes_by_project(self, project_id):
        """Get cost codes for a project"""
        try:
            # Get project-cost code associations
            associations = ProjectCostCode.query.filter_by(project_id=project_id).all()
            cost_code_ids = [assoc.cost_code_id for assoc in associations]
            
            # Get cost codes
            return CostCode.query.filter(CostCode.id.in_(cost_code_ids)).all()
        except Exception as e:
            print(f"Error getting cost codes for project: {str(e)}")
            return []
            
    def create_costcode(self, cost_code_id_str, description, discipline, project_id, rule_of_credit_id=None):
        """Create a new cost code"""
        try:
            costcode = CostCode(
                cost_code_id_str=cost_code_id_str,
                description=description,
                discipline=discipline,
                rule_of_credit_id=rule_of_credit_id
            )
            self.add(costcode)
            self.commit()
            
            # Associate with project if provided
            if project_id:
                project_costcode = ProjectCostCode(
                    project_id=project_id,
                    cost_code_id=costcode.id
                )
                self.add(project_costcode)
                self.commit()
            
            return costcode
        except Exception as e:
            print(f"Error creating cost code: {str(e)}")
            return None
            
    def update_costcode(self, costcode_id, description, discipline, rule_of_credit_id=None):
        """Update an existing cost code"""
        try:
            costcode = self.get_costcode_by_id(costcode_id)
            if not costcode:
                return None
                
            costcode.description = description
            costcode.discipline = discipline
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
                
            # Delete project associations
            ProjectCostCode.query.filter_by(cost_code_id=costcode_id).delete()
            
            self.delete(costcode)
            self.commit()
            return True
        except Exception as e:
            print(f"Error deleting cost code: {str(e)}")
            return False
            
    def get_costcodes_with_projects(self):
        """Get all cost codes with their associated projects"""
        try:
            costcodes = self.get_all_costcodes()
            result = []
            
            for costcode in costcodes:
                # Get project associations
                associations = ProjectCostCode.query.filter_by(cost_code_id=costcode.id).all()
                projects = [assoc.project for assoc in associations]
                
                result.append({
                    'costcode': costcode,
                    'projects': projects
                })
                
            return result
        except Exception as e:
            print(f"Error getting cost codes with projects: {str(e)}")
            return []
            
    def get_discipline_choices(self):
        """Get discipline choices"""
        return DISCIPLINE_CHOICES
