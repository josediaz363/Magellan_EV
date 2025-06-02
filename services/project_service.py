"""
Fixed ProjectService with count_projects method for Magellan EV Tracker v3.0
- Added missing count_projects method required by dashboard
- Enhanced error handling and logging
"""
from models import Project, db
import logging

# Configure logging
logger = logging.getLogger(__name__)

class ProjectService:
    """
    Service for project-related operations
    """
    
    @staticmethod
    def get_all_projects():
        """
        Get all projects
        
        Returns:
            list: List of all projects
        """
        try:
            projects = Project.query.all()
            logger.info(f"Retrieved {len(projects)} projects")
            return projects
        except Exception as e:
            logger.error(f"Error retrieving all projects: {str(e)}")
            return []
    
    @staticmethod
    def get_project_details(project_id):
        """
        Get project details with all necessary related data
        
        Args:
            project_id (int): Project ID
            
        Returns:
            Project: Project object with related data
        """
        try:
            project = Project.query.get(project_id)
            if project:
                logger.info(f"Retrieved project: {project.id}, {project.name}")
            return project
        except Exception as e:
            logger.error(f"Error retrieving project {project_id}: {str(e)}")
            return None
    
    @staticmethod
    def count_projects():
        """
        Count total number of projects
        
        Returns:
            int: Count of projects
        """
        try:
            count = Project.query.count()
            logger.info(f"Counted {count} projects")
            return count
        except Exception as e:
            logger.error(f"Error counting projects: {str(e)}")
            return 0
    
    @staticmethod
    def create_project(name, project_id_str, description):
        """
        Create a new project
        
        Args:
            name (str): Project name
            project_id_str (str): Project ID string
            description (str): Project description
            
        Returns:
            Project: Newly created project
        """
        try:
            project = Project(
                name=name,
                project_id_str=project_id_str,
                description=description
            )
            db.session.add(project)
            db.session.commit()
            logger.info(f"Project created successfully: {project.id}, {project.name}")
            return project
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating project: {str(e)}")
            raise
    
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
        try:
            project = Project.query.get(project_id)
            if project:
                project.name = name
                project.description = description
                db.session.commit()
                logger.info(f"Project updated successfully: {project.id}, {project.name}")
            return project
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating project {project_id}: {str(e)}")
            raise
    
    @staticmethod
    def delete_project(project_id):
        """
        Delete a project
        
        Args:
            project_id (int): Project ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            project = Project.query.get(project_id)
            if project:
                db.session.delete(project)
                db.session.commit()
                logger.info(f"Project deleted successfully: {project_id}")
                return True
            return False
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting project {project_id}: {str(e)}")
            return False
