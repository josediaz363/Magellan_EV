"""
CostCode service for Magellan EV Tracker v2.0
This service handles operations related to cost codes.
"""
from models import CostCode, Project, RuleOfCredit, DISCIPLINE_CHOICES
from services.base_service import BaseService
from sqlalchemy.orm import joinedload
import traceback

class CostCodeService(BaseService):
    """Service for cost code-related operations"""
    
    def get_costcode_by_id(self, costcode_id):
        """Get a cost code by its ID"""
        try:
            return self.get_by_id(CostCode, costcode_id)
        except Exception as e:
            print(f"Error getting cost code by ID: {str(e)}")
            traceback.print_exc()
            return None
    
    def get_all_costcodes(self):
        """Get all cost codes"""
        try:
            return self.get_all(CostCode)
        except Exception as e:
            print(f"Error getting all cost codes: {str(e)}")
            traceback.print_exc()
            return []
    
    def get_costcodes_by_project(self, project_id):
        """Get all cost codes for a specific project"""
        try:
            return self.filter_by(CostCode, project_id=project_id)
        except Exception as e:
            print(f"Error getting cost codes by project: {str(e)}")
            traceback.print_exc()
            return []
    
    def get_costcodes_with_projects(self):
        """Get all cost codes with their related projects and rules of credit"""
        try:
            # Use joinedload to efficiently load related objects
            costcodes = self.db.session.query(CostCode).options(
                joinedload(CostCode.project),
                joinedload(CostCode.rule_of_credit)
            ).all()
            
            result = []
            for costcode in costcodes:
                costcode_data = {
                    'costcode': costcode,
                    'project': costcode.project,
                    'rule_of_credit': costcode.rule_of_credit
                }
                result.append(costcode_data)
            
            return result
        except Exception as e:
            print(f"Error getting cost codes with projects: {str(e)}")
            traceback.print_exc()
            return []
    
    def create_costcode(self, cost_code_id_str, description, discipline, project_id, rule_of_credit_id=None):
        """Create a new cost code"""
        try:
            # Validate project_id
            project = self.db.session.query(Project).get(project_id)
            if not project:
                print(f"Project with ID {project_id} not found")
                return None
            
            # Validate rule_of_credit_id if provided
            if rule_of_credit_id:
                rule = self.db.session.query(RuleOfCredit).get(rule_of_credit_id)
                if not rule:
                    print(f"Rule of Credit with ID {rule_of_credit_id} not found")
                    return None
            
            # Create new cost code
            new_costcode = CostCode(
                cost_code_id_str=cost_code_id_str,
                description=description,
                discipline=discipline,
                project_id=project_id,
                rule_of_credit_id=rule_of_credit_id
            )
            
            self.add(new_costcode)
            self.commit()
            
            # Refresh the session to ensure relationships are loaded
            self.db.session.refresh(new_costcode)
            
            return new_costcode
        except Exception as e:
            print(f"Error creating cost code: {str(e)}")
            traceback.print_exc()
            self.rollback()
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
                costcode.discipline = discipline
            if rule_of_credit_id is not None or rule_of_credit_id == '':
                costcode.rule_of_credit_id = rule_of_credit_id
            
            self.commit()
            
            # Refresh the session to ensure relationships are loaded
            self.db.session.refresh(costcode)
            
            return costcode
        except Exception as e:
            print(f"Error updating cost code: {str(e)}")
            traceback.print_exc()
            self.rollback()
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
            traceback.print_exc()
            self.rollback()
            return False
    
    def get_discipline_choices(self):
        """Get all discipline choices"""
        return DISCIPLINE_CHOICES
