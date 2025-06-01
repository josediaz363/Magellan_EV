"""
Project service for Magellan EV Tracker v3.0
- Provides methods for project management
- Ensures proper database session handling
- Adds extensive logging for debugging
"""

from models import db, Project
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProjectService:
    @staticmethod
    def create_project(name, project_id_str, description=""):
        """Create a new project"""
        try:
            logger.info(f"Creating project: {name}, {project_id_str}")
            project = Project(
                name=name,
                project_id_str=project_id_str,
                description=description
            )
            db.session.add(project)
            db.session.commit()
            logger.info(f"Project created with ID: {project.id}")
            return project
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating project: {str(e)}")
            raise

    @staticmethod
    def get_all_projects():
        """Get all projects"""
        try:
            logger.info("Fetching all projects")
            projects = Project.query.all()
            logger.info(f"Found {len(projects)} projects")
            for project in projects:
                logger.info(f"Project: {project.id}, {project.name}, {project.project_id_str}")
            return projects
        except Exception as e:
            logger.error(f"Error fetching projects: {str(e)}")
            raise

    @staticmethod
    def get_project_details(project_id):
        """Get project by ID"""
        try:
            logger.info(f"Fetching project with ID: {project_id}")
            project = Project.query.get(project_id)
            if project:
                logger.info(f"Found project: {project.name}")
            else:
                logger.warning(f"No project found with ID: {project_id}")
            return project
        except Exception as e:
            logger.error(f"Error fetching project: {str(e)}")
            raise

    @staticmethod
    def update_project(project_id, name, description):
        """Update project"""
        try:
            logger.info(f"Updating project with ID: {project_id}")
            project = Project.query.get(project_id)
            if not project:
                logger.warning(f"No project found with ID: {project_id}")
                raise ValueError(f"Project with ID {project_id} not found")
            
            project.name = name
            project.description = description
            db.session.commit()
            logger.info(f"Project updated: {project.name}")
            return project
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating project: {str(e)}")
            raise

    @staticmethod
    def delete_project(project_id):
        """Delete project"""
        try:
            logger.info(f"Deleting project with ID: {project_id}")
            project = Project.query.get(project_id)
            if not project:
                logger.warning(f"No project found with ID: {project_id}")
                raise ValueError(f"Project with ID {project_id} not found")
            
            db.session.delete(project)
            db.session.commit()
            logger.info(f"Project deleted: {project_id}")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting project: {str(e)}")
            raise

    @staticmethod
    def count_projects():
        """Count all projects"""
        try:
            logger.info("Counting projects")
            count = Project.query.count()
            logger.info(f"Project count: {count}")
            return count
        except Exception as e:
            logger.error(f"Error counting projects: {str(e)}")
            raise
