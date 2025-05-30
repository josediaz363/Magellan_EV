"""
WorkItem service for Magellan EV Tracker v2.0
This service handles operations related to work items.
"""
from models import WorkItem, SubJob, CostCode
from services.base_service import BaseService
from sqlalchemy.orm import joinedload
import traceback  # Add import for traceback

class WorkItemService(BaseService):
    """Service for work item-related operations"""
    
    def get_workitem_by_id(self, workitem_id):
        """Get a work item by its ID"""
        return self.get_by_id(WorkItem, workitem_id)
    
    def get_workitems_by_project(self, project_id):
        """Get all work items for a specific project"""
        return self.filter_by(WorkItem, project_id=project_id)
    
    def get_workitems_by_subjob(self, sub_job_id):
        """Get all work items for a specific sub job"""
        return self.filter_by(WorkItem, sub_job_id=sub_job_id)
    
    def get_workitems_by_costcode(self, costcode_id):
        """Get all work items for a specific cost code"""
        return self.filter_by(WorkItem, cost_code_id=costcode_id)
    
    def get_all_workitems(self):
        """Get all work items"""
        return self.get_all(WorkItem)
    
    def get_recent_workitems(self, limit=10):
        """Get the most recent work items"""
        try:
            return WorkItem.query.order_by(WorkItem.id.desc()).limit(limit).all()
        except Exception as e:
            print(f"Error getting recent work items: {str(e)}")
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
                budgeted_quantity=float(budgeted_quantity) if budgeted_quantity else None,
                unit_of_measure=unit_of_measure,
                budgeted_man_hours=float(budgeted_man_hours) if budgeted_man_hours else None
            )
            self.add(new_workitem)
            self.commit()
            
            # Calculate earned values based on rule of credit
            new_workitem.calculate_earned_values()
            self.commit()
            
            return new_workitem
        except Exception as e:
            print(f"Error creating work item: {str(e)}")
            traceback.print_exc()
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
                workitem.budgeted_quantity = float(budgeted_quantity)
            if unit_of_measure is not None:
                workitem.unit_of_measure = unit_of_measure
            if budgeted_man_hours is not None:
                workitem.budgeted_man_hours = float(budgeted_man_hours)
            
            # Recalculate earned values
            workitem.calculate_earned_values()
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
    
    def update_progress(self, workitem_id, progress_dict):
        """Update progress for a work item"""
        try:
            workitem = self.get_workitem_by_id(workitem_id)
            if not workitem:
                return False
            
            # Update progress data
            workitem.set_progress_data(progress_dict)
            
            # Recalculate earned values
            workitem.calculate_earned_values()
            
            self.commit()
            return True
        except Exception as e:
            print(f"Error updating progress: {str(e)}")
            return False
    
    def get_workitems_with_related(self):
        """Get all work items with related objects"""
        try:
            # Use joinedload to efficiently load related objects
            workitems = self.db.session.query(WorkItem).options(
                joinedload(WorkItem.project),
                joinedload(WorkItem.sub_job),
                joinedload(WorkItem.cost_code)
            ).all()
            
            result = []
            for workitem in workitems:
                workitem_data = {
                    'workitem': workitem,
                    'project': workitem.project,
                    'sub_job': workitem.sub_job,
                    'cost_code': workitem.cost_code
                }
                result.append(workitem_data)
            
            return result
        except Exception as e:
            print(f"Error getting work items with related: {str(e)}")
            traceback.print_exc()
            return []
