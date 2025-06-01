"""
Updated SubJobService for Magellan EV Tracker v3.0
- Adds support for sub_job_id_str parameter in create_sub_job method
- Removes 'discipline' references from SubJob workflows
- Maintains 'area' field for SubJob
"""
from models import SubJob, WorkItem, db
import uuid


class SubJobService:
    """
    Service for sub job-related operations
    """
    
    @staticmethod
    def get_all_sub_jobs():
        """
        Get all sub jobs
        
        Returns:
            list: List of all sub jobs
        """
        return SubJob.query.all()
    
    @staticmethod
    def get_project_sub_jobs(project_id):
        """
        Get all sub jobs for a project
        
        Args:
            project_id (int): Project ID
            
        Returns:
            list: List of sub jobs for the project
        """
        return SubJob.query.filter_by(project_id=project_id).all()
    
    @staticmethod
    def get_sub_job_by_id(sub_job_id):
        """
        Get sub job by ID
        
        Args:
            sub_job_id (int): Sub Job ID
            
        Returns:
            SubJob: Sub Job object
        """
        if not sub_job_id:
            return None
            
        return SubJob.query.get(sub_job_id)
    
    @staticmethod
    def get_sub_job_details(sub_job_id):
        """
        Get sub job details with all necessary related data
        
        Args:
            sub_job_id (int): Sub Job ID
            
        Returns:
            SubJob: Sub Job object with related data
        """
        if not sub_job_id:
            return None
            
        return SubJob.query.get(sub_job_id)
    
    @staticmethod
    def get_sub_job_work_items(sub_job_id):
        """
        Get all work items for a sub job
        
        Args:
            sub_job_id (int): Sub Job ID
            
        Returns:
            list: List of work items for the sub job
        """
        return WorkItem.query.filter_by(sub_job_id=sub_job_id).all()
    
    @staticmethod
    def create_sub_job(project_id, name, area="", description="", sub_job_id_str=None, budgeted_hours=0):
        """
        Create a new sub job
        
        Args:
            project_id (int): Project ID
            name (str): Sub job name
            area (str, optional): Area
            description (str, optional): Sub job description
            sub_job_id_str (str, optional): Sub job ID string. If None, auto-generated.
            budgeted_hours (float, optional): Budgeted hours
            
        Returns:
            SubJob: Newly created sub job
        """
        try:
            # Auto-generate sub_job_id_str if not provided
            if not sub_job_id_str:
                # Generate a sub_job_id_str based on project and name
                prefix = name[:3].upper() if name else "SJ"
                # Ensure prefix is at least 2 characters
                while len(prefix) < 2:
                    prefix += "X"
                    
                # Get the next number for this prefix in this project
                similar_sub_jobs = SubJob.query.filter(
                    SubJob.project_id == project_id,
                    SubJob.sub_job_id_str.like(f"{prefix}-%")
                ).all()
                
                next_number = 1
                if similar_sub_jobs:
                    # Extract numbers from existing IDs
                    numbers = []
                    for sj in similar_sub_jobs:
                        try:
                            num_part = sj.sub_job_id_str.split('-')[1]
                            numbers.append(int(num_part))
                        except (IndexError, ValueError):
                            pass
                    
                    if numbers:
                        next_number = max(numbers) + 1
                
                sub_job_id_str = f"{prefix}-{next_number:03d}"
            
            # Check if a sub job with this ID already exists
            existing = SubJob.query.filter_by(sub_job_id_str=sub_job_id_str).first()
            if existing:
                # Append a unique identifier to make it unique
                unique_suffix = str(uuid.uuid4())[:8]
                sub_job_id_str = f"{sub_job_id_str}-{unique_suffix}"
            
            sub_job = SubJob(
                project_id=project_id,
                name=name,
                area=area,
                description=description,
                sub_job_id_str=sub_job_id_str,
                budgeted_hours=budgeted_hours
            )
            db.session.add(sub_job)
            db.session.commit()
            return sub_job
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def update_sub_job(sub_job_id, name, sub_job_id_str=None, description=None, area=None, budgeted_hours=None):
        """
        Update an existing sub job
        
        Args:
            sub_job_id (int): Sub Job ID
            name (str): New sub job name
            sub_job_id_str (str, optional): New sub job ID string
            description (str, optional): New sub job description
            area (str, optional): New area
            budgeted_hours (float, optional): New budgeted hours
            
        Returns:
            SubJob: Updated sub job
        """
        sub_job = SubJob.query.get(sub_job_id)
        if sub_job:
            sub_job.name = name
            if sub_job_id_str:
                sub_job.sub_job_id_str = sub_job_id_str
            if description is not None:
                sub_job.description = description
            if area is not None:
                sub_job.area = area
            if budgeted_hours is not None:
                sub_job.budgeted_hours = budgeted_hours
            db.session.commit()
        return sub_job
    
    @staticmethod
    def delete_sub_job(sub_job_id):
        """
        Delete a sub job
        
        Args:
            sub_job_id (int): Sub Job ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        sub_job = SubJob.query.get(sub_job_id)
        if sub_job:
            db.session.delete(sub_job)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def get_sub_job_metrics(sub_job_id):
        """
        Get metrics for a sub job
        
        Args:
            sub_job_id (int): Sub Job ID
            
        Returns:
            dict: Dictionary of sub job metrics
        """
        if not sub_job_id:
            return {
                'percent_complete': 0.0,
                'earned_hours': 0.0,
                'budgeted_hours': 0.0,
                'earned_quantity': 0.0,
                'budgeted_quantity': 0.0
            }
            
        # Get all work items for the sub job
        work_items = WorkItem.query.filter_by(sub_job_id=sub_job_id).all()
        
        # Calculate metrics
        total_earned_hours = sum(work_item.earned_man_hours or 0 for work_item in work_items)
        total_budgeted_hours = sum(work_item.budgeted_man_hours or 0 for work_item in work_items)
        total_earned_quantity = sum(work_item.earned_quantity or 0 for work_item in work_items)
        total_budgeted_quantity = sum(work_item.budgeted_quantity or 0 for work_item in work_items)
        
        # Calculate percent complete
        percent_complete = 0.0
        if total_budgeted_hours > 0:
            percent_complete = (total_earned_hours / total_budgeted_hours) * 100
            
        return {
            'percent_complete': round(percent_complete, 1),
            'earned_hours': round(total_earned_hours, 1),
            'budgeted_hours': round(total_budgeted_hours, 1),
            'earned_quantity': round(total_earned_quantity, 1),
            'budgeted_quantity': round(total_budgeted_quantity, 1)
        }
