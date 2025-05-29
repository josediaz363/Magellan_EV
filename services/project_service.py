"""
Project service for Magellan EV Tracker v2.0
This service handles operations related to projects.
"""

from models import Project, SubJob, WorkItem
from services.base_service import BaseService

class ProjectService(BaseService):
    """Service for project-related operations"""
    
    def get_all_projects(self):
        """Get all projects"""
        try:
            return Project.query.all()
        except Exception as e:
            print(f"Error getting projects: {str(e)}")
            return []
            
    def get_project_by_id(self, project_id):
        """Get project by ID"""
        try:
            return Project.query.get(project_id)
        except Exception as e:
            print(f"Error getting project: {str(e)}")
            return None
            
    def create_project(self, name, description, project_id_str):
        """Create a new project"""
        try:
            project = Project(
                name=name,
                description=description,
                project_id_str=project_id_str
            )
            self.add(project)
            self.commit()
            return project
        except Exception as e:
            print(f"Error creating project: {str(e)}")
            return None
            
    def update_project(self, project_id, name, description):
        """Update an existing project"""
        try:
            project = self.get_project_by_id(project_id)
            if not project:
                return None
                
            project.name = name
            project.description = description
            
            self.commit()
            return project
        except Exception as e:
            print(f"Error updating project: {str(e)}")
            return None
            
    def delete_project(self, project_id):
        """Delete a project"""
        try:
            project = self.get_project_by_id(project_id)
            if not project:
                return False
                
            self.delete(project)
            self.commit()
            return True
        except Exception as e:
            print(f"Error deleting project: {str(e)}")
            return False
            
    def get_projects_with_metrics(self):
        """Get all projects with metrics data"""
        try:
            projects = self.get_all_projects()
            projects_with_data = []
            
            for project in projects:
                # Get sub jobs
                sub_jobs = SubJob.query.filter_by(project_id=project.id).all()
                
                # Get work items
                work_items = WorkItem.query.filter_by(project_id=project.id).all()
                
                # Calculate metrics
                total_budgeted_hours = sum(item.budgeted_man_hours or 0 for item in work_items)
                total_earned_hours = sum(item.earned_man_hours or 0 for item in work_items)
                
                # Calculate progress
                progress = 0
                if total_budgeted_hours > 0:
                    progress = (total_earned_hours / total_budgeted_hours) * 100
                
                projects_with_data.append({
                    'project': project,
                    'sub_jobs_count': len(sub_jobs),
                    'work_items_count': len(work_items),
                    'budgeted_hours': total_budgeted_hours,
                    'earned_hours': total_earned_hours,
                    'progress': progress
                })
                
            return projects_with_data
        except Exception as e:
            print(f"Error getting projects with metrics: {str(e)}")
            return []
