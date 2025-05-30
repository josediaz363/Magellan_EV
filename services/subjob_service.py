"""
SubJob service for Magellan EV Tracker v2.0
This service handles operations related to sub jobs.
"""
from models import SubJob, WorkItem
from services.base_service import BaseService
import traceback  # Add import for traceback

class SubJobService(BaseService):
    """Service for sub job-related operations"""
    
    def get_subjob_by_id(self, subjob_id):
        """Get a sub job by its ID"""
        return self.get_by_id(SubJob, subjob_id)
    
    def get_subjobs_by_project(self, project_id):
        """Get all sub jobs for a specific project"""
        return self.filter_by(SubJob, project_id=project_id)
    
    def create_subjob(self, name, description, sub_job_id_str, project_id, area=None):
        """Create a new sub job"""
        try:
            new_subjob = SubJob(
                name=name,
                description=description,
                sub_job_id_str=sub_job_id_str,
                project_id=project_id,
                area=area
            )
            success = self.add(new_subjob)
            if not success:
                print(f"Failed to add sub job to session")
                return None
                
            success = self.commit()
            if not success:
                print(f"Failed to commit sub job to database")
                return None
                
            # Verify the sub job was actually saved by retrieving it
            saved_subjob = self.get_subjob_by_id(new_subjob.id)
            if not saved_subjob:
                print(f"Sub job appears to be created but cannot be retrieved with ID {new_subjob.id}")
                
            return new_subjob
        except Exception as e:
            print(f"Error creating sub job: {str(e)}")
            traceback.print_exc()
            return None
    
    def update_subjob(self, subjob_id, name=None, description=None, area=None):
        """Update an existing sub job"""
        try:
            subjob = self.get_subjob_by_id(subjob_id)
            if not subjob:
                return None
            
            if name is not None:
                subjob.name = name
            if description is not None:
                subjob.description = description
            if area is not None:
                subjob.area = area
            
            self.commit()
            return subjob
        except Exception as e:
            print(f"Error updating sub job: {str(e)}")
            return None
    
    def delete_subjob(self, subjob_id):
        """Delete a sub job"""
        try:
            subjob = self.get_subjob_by_id(subjob_id)
            if not subjob:
                return False
            
            self.delete(subjob)
            self.commit()
            return True
        except Exception as e:
            print(f"Error deleting sub job: {str(e)}")
            return False
    
    def get_subjob_metrics(self, subjob_id):
        """Get metrics for a specific sub job"""
        try:
            subjob = self.get_subjob_by_id(subjob_id)
            if not subjob:
                return None
            
            # Get all work items for this sub job
            work_items = WorkItem.query.filter_by(sub_job_id=subjob_id).all()
            
            # Calculate totals
            total_budgeted_hours = sum(item.budgeted_man_hours or 0 for item in work_items)
            total_earned_hours = sum(item.earned_man_hours or 0 for item in work_items)
            total_budgeted_quantity = sum(item.budgeted_quantity or 0 for item in work_items)
            total_earned_quantity = sum(item.earned_quantity or 0 for item in work_items)
            
            # Calculate overall progress percentage
            overall_progress = 0
            if total_budgeted_hours > 0:
                overall_progress = (total_earned_hours / total_budgeted_hours) * 100
            
            # Create a dictionary with sub job and its calculated values
            subjob_data = {
                'subjob': subjob,
                'total_budgeted_hours': total_budgeted_hours,
                'total_earned_hours': total_earned_hours,
                'total_budgeted_quantity': total_budgeted_quantity,
                'total_earned_quantity': total_earned_quantity,
                'overall_progress': overall_progress,
                'work_items': work_items
            }
            
            return subjob_data
        except Exception as e:
            print(f"Error getting sub job metrics: {str(e)}")
            return None
