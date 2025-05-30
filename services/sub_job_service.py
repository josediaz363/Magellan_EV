"""
SubJob service for Magellan EV Tracker v2.0
This service handles operations related to sub jobs.
"""
from models import SubJob, WorkItem
from services.base_service import BaseService
import traceback  # Add import for traceback

class SubJobService(BaseService):
    """Service for sub job-related operations"""
    
    def get_sub_job_by_id(self, sub_job_id):
        """Get a sub job by its ID"""
        return self.get_by_id(SubJob, sub_job_id)
    
    def get_sub_jobs_by_project(self, project_id):
        """Get all sub jobs for a specific project"""
        return self.filter_by(SubJob, project_id=project_id)
    
    def create_sub_job(self, name, description, sub_job_id_str, project_id, area=None):
        """Create a new sub job"""
        try:
            new_sub_job = SubJob(
                name=name,
                description=description,
                sub_job_id_str=sub_job_id_str,
                project_id=project_id,
                area=area
            )
            success = self.add(new_sub_job)
            if not success:
                print(f"Failed to add sub job to session")
                return None
                
            success = self.commit()
            if not success:
                print(f"Failed to commit sub job to database")
                return None
                
            # Verify the sub job was actually saved by retrieving it
            saved_sub_job = self.get_sub_job_by_id(new_sub_job.id)
            if not saved_sub_job:
                print(f"Sub job appears to be created but cannot be retrieved with ID {new_sub_job.id}")
                
            return new_sub_job
        except Exception as e:
            print(f"Error creating sub job: {str(e)}")
            traceback.print_exc()
            return None
    
    def update_sub_job(self, sub_job_id, name=None, description=None, area=None):
        """Update an existing sub job"""
        try:
            sub_job = self.get_sub_job_by_id(sub_job_id)
            if not sub_job:
                return None
            
            if name is not None:
                sub_job.name = name
            if description is not None:
                sub_job.description = description
            if area is not None:
                sub_job.area = area
            
            self.commit()
            return sub_job
        except Exception as e:
            print(f"Error updating sub job: {str(e)}")
            return None
    
    def delete_sub_job(self, sub_job_id):
        """Delete a sub job"""
        try:
            sub_job = self.get_sub_job_by_id(sub_job_id)
            if not sub_job:
                return False
            
            self.delete(sub_job)
            self.commit()
            return True
        except Exception as e:
            print(f"Error deleting sub job: {str(e)}")
            return False
    
    def get_sub_job_metrics(self, sub_job_id):
        """Get metrics for a specific sub job"""
        try:
            sub_job = self.get_sub_job_by_id(sub_job_id)
            if not sub_job:
                return None
            
            # Get all work items for this sub job
            work_items = WorkItem.query.filter_by(sub_job_id=sub_job_id).all()
            
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
            sub_job_data = {
                'sub_job': sub_job,
                'total_budgeted_hours': total_budgeted_hours,
                'total_earned_hours': total_earned_hours,
                'total_budgeted_quantity': total_budgeted_quantity,
                'total_earned_quantity': total_earned_quantity,
                'overall_progress': overall_progress,
                'work_items': work_items
            }
            
            return sub_job_data
        except Exception as e:
            print(f"Error getting sub job metrics: {str(e)}")
            return None
            
    # Alias methods for backward compatibility
    def get_subjob_by_id(self, subjob_id):
        """Alias for get_sub_job_by_id for backward compatibility"""
        return self.get_sub_job_by_id(subjob_id)
    
    def get_subjobs_by_project(self, project_id):
        """Alias for get_sub_jobs_by_project for backward compatibility"""
        return self.get_sub_jobs_by_project(project_id)
    
    def create_subjob(self, name, description, sub_job_id_str, project_id, area=None):
        """Alias for create_sub_job for backward compatibility"""
        return self.create_sub_job(name, description, sub_job_id_str, project_id, area)
    
    def update_subjob(self, subjob_id, name=None, description=None, area=None):
        """Alias for update_sub_job for backward compatibility"""
        return self.update_sub_job(subjob_id, name, description, area)
    
    def delete_subjob(self, subjob_id):
        """Alias for delete_sub_job for backward compatibility"""
        return self.delete_sub_job(subjob_id)
    
    def get_subjob_metrics(self, subjob_id):
        """Alias for get_sub_job_metrics for backward compatibility"""
        return self.get_sub_job_metrics(subjob_id)
