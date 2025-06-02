"""
Fixed SubJobService with count_sub_jobs method for Magellan EV Tracker v3.0
- Added missing count_sub_jobs method required by dashboard
- Enhanced error handling and logging
"""
from models import SubJob, db
import logging

# Configure logging
logger = logging.getLogger(__name__)

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
        try:
            sub_jobs = SubJob.query.all()
            logger.info(f"Retrieved {len(sub_jobs)} sub jobs")
            return sub_jobs
        except Exception as e:
            logger.error(f"Error retrieving all sub jobs: {str(e)}")
            return []
    
    @staticmethod
    def get_sub_job_by_id(sub_job_id):
        """
        Get sub job by ID
        
        Args:
            sub_job_id (int): Sub Job ID
            
        Returns:
            SubJob: Sub Job object
        """
        try:
            sub_job = SubJob.query.get(sub_job_id)
            if sub_job:
                logger.info(f"Retrieved sub job: {sub_job.id}, {sub_job.name}")
            return sub_job
        except Exception as e:
            logger.error(f"Error retrieving sub job {sub_job_id}: {str(e)}")
            return None
    
    @staticmethod
    def get_project_sub_jobs(project_id):
        """
        Get all sub jobs for a project
        
        Args:
            project_id (int): Project ID
            
        Returns:
            list: List of sub jobs for the project
        """
        try:
            sub_jobs = SubJob.query.filter_by(project_id=project_id).all()
            logger.info(f"Retrieved {len(sub_jobs)} sub jobs for project {project_id}")
            return sub_jobs
        except Exception as e:
            logger.error(f"Error retrieving sub jobs for project {project_id}: {str(e)}")
            return []
    
    @staticmethod
    def create_sub_job(project_id, name, sub_job_id_str, description, area, budgeted_hours=0.0):
        """
        Create a new sub job
        
        Args:
            project_id (int): Project ID
            name (str): Sub job name
            sub_job_id_str (str): Sub job ID string
            description (str): Sub job description
            area (str): Area
            budgeted_hours (float, optional): Budgeted hours
            
        Returns:
            SubJob: Newly created sub job
        """
        try:
            sub_job = SubJob(
                project_id=project_id,
                name=name,
                sub_job_id_str=sub_job_id_str,
                description=description,
                area=area,
                budgeted_hours=budgeted_hours
            )
            db.session.add(sub_job)
            db.session.commit()
            logger.info(f"Sub job created successfully: {sub_job.id}, {sub_job.name}")
            return sub_job
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating sub job: {str(e)}")
            raise
    
    @staticmethod
    def update_sub_job(sub_job_id, name, description, area, budgeted_hours=0.0):
        """
        Update an existing sub job
        
        Args:
            sub_job_id (int): Sub Job ID
            name (str): New sub job name
            description (str): New sub job description
            area (str): New area
            budgeted_hours (float, optional): New budgeted hours
            
        Returns:
            SubJob: Updated sub job
        """
        try:
            sub_job = SubJob.query.get(sub_job_id)
            if sub_job:
                sub_job.name = name
                sub_job.description = description
                sub_job.area = area
                sub_job.budgeted_hours = budgeted_hours
                db.session.commit()
                logger.info(f"Sub job updated successfully: {sub_job.id}, {sub_job.name}")
            return sub_job
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating sub job {sub_job_id}: {str(e)}")
            raise
    
    @staticmethod
    def delete_sub_job(sub_job_id):
        """
        Delete a sub job
        
        Args:
            sub_job_id (int): Sub Job ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            sub_job = SubJob.query.get(sub_job_id)
            if sub_job:
                db.session.delete(sub_job)
                db.session.commit()
                logger.info(f"Sub job deleted successfully: {sub_job_id}")
                return True
            return False
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting sub job {sub_job_id}: {str(e)}")
            return False
            
    @staticmethod
    def count_sub_jobs():
        """
        Count total number of sub jobs
        
        Returns:
            int: Count of sub jobs
        """
        try:
            count = SubJob.query.count()
            logger.info(f"Counted {count} sub jobs")
            return count
        except Exception as e:
            logger.error(f"Error counting sub jobs: {str(e)}")
            return 0
