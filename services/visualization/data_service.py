"""
Base visualization data service for Magellan EV Tracker v2.0
This service provides common functionality for all visualization data services.
"""
from services.base_service import BaseService
from models import Project, SubJob, WorkItem

class VisualizationDataService(BaseService):
    """Base service for visualization data operations"""
    
    def __init__(self):
        """Initialize the service"""
        super().__init__()
        self.cache = {}
    
    def get_data(self, project_id):
        """
        Get data for visualization
        This method should be overridden by subclasses
        """
        raise NotImplementedError("Subclasses must implement get_data method")
    
    def clear_cache(self):
        """Clear the data cache"""
        self.cache = {}
    
    def clear_project_cache(self, project_id):
        """Clear cache for a specific project"""
        if project_id in self.cache:
            del self.cache[project_id]
    
    def get_project_metrics(self, project_id):
        """Get basic metrics for a project"""
        try:
            project = self.get_by_id(Project, project_id)
            if not project:
                return None
            
            # Get all work items for this project
            work_items = WorkItem.query.filter_by(project_id=project_id).all()
            
            # Calculate totals
            total_budgeted_hours = sum(item.budgeted_man_hours or 0 for item in work_items)
            total_earned_hours = sum(item.earned_man_hours or 0 for item in work_items)
            total_budgeted_quantity = sum(item.budgeted_quantity or 0 for item in work_items)
            total_earned_quantity = sum(item.earned_quantity or 0 for item in work_items)
            
            # Calculate overall progress percentage
            overall_progress = 0
            if total_budgeted_hours > 0:
                overall_progress = (total_earned_hours / total_budgeted_hours) * 100
            
            return {
                'project': project.serialize(),
                'total_budgeted_hours': total_budgeted_hours,
                'total_earned_hours': total_earned_hours,
                'total_budgeted_quantity': total_budgeted_quantity,
                'total_earned_quantity': total_earned_quantity,
                'overall_progress': overall_progress
            }
        except Exception as e:
            print(f"Error getting project metrics: {str(e)}")
            return None
    
    def get_subjob_metrics(self, project_id):
        """Get metrics for all sub jobs in a project"""
        try:
            # Get all sub jobs for this project
            sub_jobs = SubJob.query.filter_by(project_id=project_id).all()
            
            result = []
            for sub_job in sub_jobs:
                # Get all work items for this sub job
                work_items = WorkItem.query.filter_by(sub_job_id=sub_job.id).all()
                
                # Calculate totals
                total_budgeted_hours = sum(item.budgeted_man_hours or 0 for item in work_items)
                total_earned_hours = sum(item.earned_man_hours or 0 for item in work_items)
                total_budgeted_quantity = sum(item.budgeted_quantity or 0 for item in work_items)
                total_earned_quantity = sum(item.earned_quantity or 0 for item in work_items)
                
                # Calculate overall progress percentage
                overall_progress = 0
                if total_budgeted_hours > 0:
                    overall_progress = (total_earned_hours / total_budgeted_hours) * 100
                
                result.append({
                    'sub_job': sub_job.serialize(),
                    'total_budgeted_hours': total_budgeted_hours,
                    'total_earned_hours': total_earned_hours,
                    'total_budgeted_quantity': total_budgeted_quantity,
                    'total_earned_quantity': total_earned_quantity,
                    'overall_progress': overall_progress
                })
            
            return result
        except Exception as e:
            print(f"Error getting sub job metrics: {str(e)}")
            return []
