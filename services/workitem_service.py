"""
WorkItem service for Magellan EV Tracker v2.0
This service handles operations related to work items.
"""

from models import WorkItem, RuleOfCredit, CostCode
from services.base_service import BaseService
import json

class WorkItemService(BaseService):
    """Service for work item-related operations"""
    
    def get_all_workitems(self):
        """Get all work items"""
        try:
            return WorkItem.query.all()
        except Exception as e:
            print(f"Error getting work items: {str(e)}")
            return []
            
    def get_recent_workitems(self, limit=10):
        """Get recent work items"""
        try:
            return WorkItem.query.order_by(WorkItem.id.desc()).limit(limit).all()
        except Exception as e:
            print(f"Error getting recent work items: {str(e)}")
            return []
            
    def get_workitem_by_id(self, workitem_id):
        """Get work item by ID"""
        try:
            return WorkItem.query.get(workitem_id)
        except Exception as e:
            print(f"Error getting work item: {str(e)}")
            return None
            
    def get_workitems_by_project(self, project_id):
        """Get work items for a project"""
        try:
            return WorkItem.query.filter_by(project_id=project_id).all()
        except Exception as e:
            print(f"Error getting work items for project: {str(e)}")
            return []
            
    def get_workitems_by_subjob(self, subjob_id):
        """Get work items for a sub job"""
        try:
            return WorkItem.query.filter_by(sub_job_id=subjob_id).all()
        except Exception as e:
            print(f"Error getting work items for sub job: {str(e)}")
            return []
            
    def create_workitem(self, work_item_id_str, description, project_id, sub_job_id, cost_code_id,
                       budgeted_quantity, unit_of_measure, budgeted_man_hours):
        """Create a new work item"""
        try:
            workitem = WorkItem(
                work_item_id_str=work_item_id_str,
                description=description,
                project_id=project_id,
                sub_job_id=sub_job_id,
                cost_code_id=cost_code_id,
                budgeted_quantity=budgeted_quantity,
                unit_of_measure=unit_of_measure,
                budgeted_man_hours=budgeted_man_hours,
                earned_quantity=0,
                earned_man_hours=0,
                percent_complete_hours=0,
                steps_progress="{}"
            )
            self.add(workitem)
            self.commit()
            return workitem
        except Exception as e:
            print(f"Error creating work item: {str(e)}")
            return None
            
    def update_workitem(self, workitem_id, description, budgeted_quantity, unit_of_measure, budgeted_man_hours):
        """Update an existing work item"""
        try:
            workitem = self.get_workitem_by_id(workitem_id)
            if not workitem:
                return None
                
            workitem.description = description
            workitem.budgeted_quantity = budgeted_quantity
            workitem.unit_of_measure = unit_of_measure
            workitem.budgeted_man_hours = budgeted_man_hours
            
            self.commit()
            return workitem
        except Exception as e:
            print(f"Error updating work item: {str(e)}")
            return None
            
    def delete_workitem(self, workitem_id):
        """Delete a work item"""
        try:
            workitem = self.get_workitem_by_id(workitem_id)
            if not workitem:
                return False
                
            self.delete(workitem)
            self.commit()
            return True
        except Exception as e:
            print(f"Error deleting work item: {str(e)}")
            return False
            
    def update_progress_step(self, workitem_id, step_name, completion_percentage):
        """Update progress for a specific step"""
        try:
            workitem = self.get_workitem_by_id(workitem_id)
            if not workitem:
                return False
                
            # Get current progress
            steps_progress = {}
            if workitem.steps_progress:
                steps_progress = json.loads(workitem.steps_progress)
                
            # Update step progress
            steps_progress[step_name] = float(completion_percentage)
            
            # Save updated progress
            workitem.steps_progress = json.dumps(steps_progress)
            
            self.commit()
            return True
        except Exception as e:
            print(f"Error updating progress step: {str(e)}")
            return False
            
    def calculate_earned_values(self, workitem):
        """Calculate earned values based on steps progress"""
        try:
            if not workitem:
                return False
                
            # Get cost code and rule of credit
            cost_code = CostCode.query.get(workitem.cost_code_id)
            if not cost_code or not cost_code.rule_of_credit_id:
                return False
                
            rule = RuleOfCredit.query.get(cost_code.rule_of_credit_id)
            if not rule:
                return False
                
            # Get steps and progress
            steps = rule.get_steps()
            steps_progress = {}
            if workitem.steps_progress:
                steps_progress = json.loads(workitem.steps_progress)
                
            # Calculate weighted progress
            total_progress = 0
            for step in steps:
                step_name = step['name']
                step_weight = step['weight']
                step_progress = steps_progress.get(step_name, 0)
                
                weighted_progress = (step_progress / 100) * step_weight
                total_progress += weighted_progress
                
            # Update work item
            workitem.percent_complete_hours = total_progress
            workitem.earned_man_hours = (total_progress / 100) * workitem.budgeted_man_hours if workitem.budgeted_man_hours else 0
            workitem.earned_quantity = (total_progress / 100) * workitem.budgeted_quantity if workitem.budgeted_quantity else 0
            
            self.commit()
            return True
        except Exception as e:
            print(f"Error calculating earned values: {str(e)}")
            return False
