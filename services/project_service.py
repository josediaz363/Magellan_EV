"""
Project service for Magellan EV Tracker v3.0
Provides data access and business logic for projects
"""
from models import Project, SubJob, CostCode, WorkItem, db
import uuid
import re


class ProjectService:
    """
    Service for project-related operations
    """
    
    @staticmethod
    def count_projects():
        """
        Count all projects
        
        Returns:
            int: Count of all projects
        """
        return Project.query.count()
    
    @staticmethod
    def get_all_projects():
        """
        Get all projects
        
        Returns:
            list: List of all projects
        """
        return Project.query.all()
    
    @staticmethod
    def get_project_details(project_id):
        """
        Get project details with all necessary related data
        
        Args:
            project_id (int): Project ID
            
        Returns:
            Project: Project object with related data
        """
        if not project_id:
            return None
            
        return Project.query.get(project_id)
    
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
    def get_project_cost_codes(project_id):
        """
        Get all cost codes for a project
        
        Args:
            project_id (int): Project ID
            
        Returns:
            list: List of cost codes for the project
        """
        return CostCode.query.filter_by(project_id=project_id).all()
    
    @staticmethod
    def create_project(name, description, project_id_str=None):
        """
        Create a new project
        
        Args:
            name (str): Project name
            description (str): Project description
            project_id_str (str, optional): Project ID string. If None, auto-generated.
            
        Returns:
            Project: Newly created project
        """
        # Auto-generate project_id_str if not provided
        if not project_id_str:
            # Create a project ID based on the name
            prefix = re.sub(r'[^A-Z]', '', name.upper()[:3])
            if not prefix:
                prefix = "PRJ"
            
            # Ensure prefix is at least 3 characters
            while len(prefix) < 3:
                prefix += "X"
            
            # Get the next number for this prefix
            similar_projects = Project.query.filter(
                Project.project_id_str.like(f"{prefix}-%")
            ).all()
            
            next_number = 1
            if similar_projects:
                # Extract numbers from existing IDs
                numbers = []
                for p in similar_projects:
                    try:
                        num_part = p.project_id_str.split('-')[1]
                        numbers.append(int(num_part))
                    except (IndexError, ValueError):
                        pass
                
                if numbers:
                    next_number = max(numbers) + 1
            
            project_id_str = f"{prefix}-{next_number:03d}"
        
        project = Project(name=name, description=description, project_id_str=project_id_str)
        db.session.add(project)
        db.session.commit()
        return project
    
    @staticmethod
    def update_project(project_id, name, description):
        """
        Update an existing project
        
        Args:
            project_id (int): Project ID
            name (str): New project name
            description (str): New project description
            
        Returns:
            Project: Updated project
        """
        project = Project.query.get(project_id)
        if project:
            project.name = name
            project.description = description
            db.session.commit()
        return project
    
    @staticmethod
    def delete_project(project_id):
        """
        Delete a project
        
        Args:
            project_id (int): Project ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        project = Project.query.get(project_id)
        if project:
            db.session.delete(project)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def get_project_metrics(project_id):
        """
        Get metrics for a project
        
        Args:
            project_id (int): Project ID
            
        Returns:
            dict: Dictionary of project metrics
        """
        if not project_id:
            return {
                'percent_complete': 0.0,
                'earned_hours': 0.0,
                'budgeted_hours': 0.0,
                'earned_quantity': 0.0,
                'budgeted_quantity': 0.0
            }
            
        # Get all work items for the project
        sub_jobs = SubJob.query.filter_by(project_id=project_id).all()
        sub_job_ids = [sub_job.id for sub_job in sub_jobs]
        
        work_items = WorkItem.query.filter(WorkItem.sub_job_id.in_(sub_job_ids)).all()
        
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
