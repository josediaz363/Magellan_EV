"""
SubJob service for Magellan EV Tracker v2.0
This service handles operations related to sub jobs.
"""

from models import SubJob, WorkItem
from services.base_service import BaseService

class SubJobService(BaseService):
    """Service for sub job-related operations"""
    
    def get_all_subjobs(self):
        """Get all sub jobs"""
        try:
            return SubJob.query.all()
        except Exception as e:
            print(f"Error getting sub jobs: {str(e)}")
            return []
            
    def get_subjob_by_id(self, subjob_id):
        """Get sub job by ID"""
        try:
            return SubJob.query.get(subjob_id)
        except Exception as e:
            print(f"Error getting sub job: {str(e)}")
            return None
            
    def get_subjobs_by_project(self, project_id):
        """Get sub jobs for a project"""
        try:
            return SubJob.query.filter_by(project_id=project_id).all()
        except Exception as e:
            print(f"Error getting sub jobs for project: {str(e)}")
            return []
            
    def create_subjob(self, name, description, sub_job_id_str, project_id, area):
        """Create a new sub job"""
        try:
            subjob = SubJob(
                name=name,
                description=description,
                sub_job_id_str=sub_job_id_str,
                project_id=project_id,
                area=area
            )
            self.add(subjob)
            self.commit()
            return subjob
        except Exception as e:
            print(f"Error creating sub job: {str(e)}")
            return None
            
    def update_subjob(self, subjob_id, name, description, area):
        """Update an existing sub job"""
        try:
            subjob = self.get_subjob_by_id(subjob_id)
            if not subjob:
                return None
                
            subjob.name = name
            subjob.description = description
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
        """Get metrics for a sub job"""
        try:
            subjob = self.get_subjob_by_id(subjob_id)
            if not subjob:
                return None
                
            # Get work items
            work_items = WorkItem.query.filter_by(sub_job_id=subjob_id).all()
            
            # Calculate metrics
            total_budgeted_hours = sum(item.budgeted_man_hours or 0 for item in work_items)
            total_earned_hours = sum(item.earned_man_hours or 0 for item in work_items)
            total_budgeted_quantity = sum(item.budgeted_quantity or 0 for item in work_items)
            total_earned_quantity = sum(item.earned_quantity or 0 for item in work_items)
            
            # Calculate progress
            overall_progress = 0
            if total_budgeted_hours > 0:
                overall_progress = (total_earned_hours / total_budgeted_hours) * 100
            
            return {
                'subjob': subjob,
                'work_items': work_items,
                'total_budgeted_hours': total_budgeted_hours,
                'total_earned_hours': total_earned_hours,
                'total_budgeted_quantity': total_budgeted_quantity,
                'total_earned_quantity': total_earned_quantity,
                'overall_progress': overall_progress
            }
        except Exception as e:
            print(f"Error getting sub job metrics: {str(e)}")
            return None
