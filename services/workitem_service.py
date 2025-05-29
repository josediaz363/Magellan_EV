"""
WorkItem service for Magellan EV Tracker v2.0
This service handles operations related to work items.
"""
from models import WorkItem, CostCode, RuleOfCredit, Project, SubJob
from services.base_service import BaseService
import json
import datetime

class WorkItemService(BaseService):
    """Service for work item-related operations"""
    
    def get_workitem_by_id(self, workitem_id):
        """Get a work item by its ID"""
        return self.get_by_id(WorkItem, workitem_id)
    
    def get_workitems_by_project(self, project_id):
        """Get all work items for a specific project"""
        return self.filter_by(WorkItem, project_id=project_id)
    
    def get_workitems_by_subjob(self, subjob_id):
        """Get all work items for a specific sub job"""
        return self.filter_by(WorkItem, sub_job_id=subjob_id)
    
    def get_workitems_by_costcode(self, costcode_id):
        """Get all work items for a specific cost code"""
        return self.filter_by(WorkItem, cost_code_id=costcode_id)
    
    def get_recent_workitems(self, limit=10):
        """Get recent work items"""
        try:
            return WorkItem.query.order_by(WorkItem.id.desc()).limit(limit).all()
        except Exception as e:
            print(f"Error getting recent work items: {str(e)}")
            return []
    
    def get_workitems_with_related_data(self):
        """Get all work items with related project, sub job, and cost code data"""
        try:
            # Join with related tables to get all data in one query
            work_items = WorkItem.query\
                .join(Project, WorkItem.project_id == Project.id)\
                .join(SubJob, WorkItem.sub_job_id == SubJob.id)\
                .outerjoin(CostCode, WorkItem.cost_code_id == CostCode.id)\
                .add_entity(Project)\
                .add_entity(SubJob)\
                .add_entity(CostCode)\
                .all()
            
            # Format the results
            result = []
            for item in work_items:
                work_item = item[0]
                project = item[1]
                sub_job = item[2]
                cost_code = item[3]
                
                result.append({
                    'work_item': work_item,
                    'project': project,
                    'sub_job': sub_job,
                    'cost_code': cost_code
                })
            
            return result
        except Exception as e:
            print(f"Error getting work items with related data: {str(e)}")
            return []
    
    def create_workitem(self, work_item_id_str, description, project_id, sub_job_id, cost_code_id, 
                       budgeted_quantity=None, unit_of_measure=None, budgeted_man_hours=None):
        """Create a new work item"""
        try:
            new_workitem = WorkItem(
                work_item_id_str=work_item_id_str,
                description=description,
                project_id=project_id,
                sub_job_id=sub_job_id,
                cost_code_id=cost_code_id,
                budgeted_quantity=budgeted_quantity,
                unit_of_measure=unit_of_measure,
                budgeted_man_hours=budgeted_man_hours,
                progress_json="[]",
                earned_man_hours=0.0,
                earned_quantity=0.0,
                percent_complete_hours=0.0,
                percent_complete_quantity=0.0
            )
            self.add(new_workitem)
            self.commit()
            return new_workitem
        except Exception as e:
            print(f"Error creating work item: {str(e)}")
            return None
    
    def update_workitem(self, workitem_id, description=None, budgeted_quantity=None, 
                       unit_of_measure=None, budgeted_man_hours=None):
        """Update an existing work item"""
        try:
            workitem = self.get_workitem_by_id(workitem_id)
            if not workitem:
                return None
            
            if description is not None:
                workitem.description = description
            if budgeted_quantity is not None:
                workitem.budgeted_quantity = budgeted_quantity
            if unit_of_measure is not None:
                workitem.unit_of_measure = unit_of_measure
            if budgeted_man_hours is not None:
                workitem.budgeted_man_hours = budgeted_man_hours
            
            self.commit()
            # Recalculate earned values after update
            self.calculate_earned_values(workitem)
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
        """Update progress for a specific step of a work item"""
        try:
            workitem = self.get_workitem_by_id(workitem_id)
            if not workitem:
                return False
            
            # Update the progress step
            workitem.update_progress_step(step_name, completion_percentage)
            
            # Add timestamp to history
            try:
                history = json.loads(getattr(workitem, 'progress_history', '[]') or '[]')
                history.append({
                    "date": datetime.datetime.utcnow().isoformat(),
                    "progress": workitem.percent_complete_hours
                })
                workitem.progress_history = json.dumps(history)
            except Exception as e:
                print(f"Error updating progress history: {str(e)}")
            
            self.commit()
            return True
        except Exception as e:
            print(f"Error updating progress step: {str(e)}")
            return False
    
    def calculate_earned_values(self, workitem):
        """Calculate earned values for a work item based on rule of credit"""
        try:
            # Get the cost code and rule of credit
            cost_code = CostCode.query.get(workitem.cost_code_id)
            if not cost_code or not cost_code.rule_of_credit_id:
                workitem.earned_man_hours = 0
                workitem.percent_complete_hours = 0
                workitem.earned_quantity = 0
                workitem.percent_complete_quantity = 0
                self.commit()
                return False
            
            rule = RuleOfCredit.query.get(cost_code.rule_of_credit_id)
            if not rule:
                workitem.earned_man_hours = 0
                workitem.percent_complete_hours = 0
                workitem.earned_quantity = 0
                workitem.percent_complete_quantity = 0
                self.commit()
                return False
            
            # Call the work item's calculate_earned_values method
            workitem.calculate_earned_values()
            self.commit()
            return True
        except Exception as e:
            print(f"Error calculating earned values: {str(e)}")
            return False
    
    def get_workitem_progress_history(self, workitem_id):
        """Get progress history for a work item"""
        try:
            workitem = self.get_workitem_by_id(workitem_id)
            if not workitem:
                return []
            
            try:
                history = json.loads(getattr(workitem, 'progress_history', '[]') or '[]')
                return history
            except Exception:
                return []
        except Exception as e:
            print(f"Error getting work item progress history: {str(e)}")
            return []
