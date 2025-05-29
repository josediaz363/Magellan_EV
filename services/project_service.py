"""
Project service for Magellan EV Tracker v2.0
This service handles operations related to projects.
"""
from models import Project, WorkItem
from services.base_service import BaseService

class ProjectService(BaseService):
    """Service for project-related operations"""
    
    def get_project_by_id(self, project_id):
        """Get a project by its ID"""
        return self.get_by_id(Project, project_id)
    
    def get_all_projects(self):
        """Get all projects"""
        return self.get_all(Project)
    
    def create_project(self, name, description, project_id_str):
        """Create a new project"""
        try:
            new_project = Project(
                name=name,
                description=description,
                project_id_str=project_id_str
            )
            self.add(new_project)
            self.commit()
            return new_project
        except Exception as e:
            print(f"Error creating project: {str(e)}")
            return None
    
    def update_project(self, project_id, name=None, description=None):
        """Update an existing project"""
        try:
            project = self.get_project_by_id(project_id)
            if not project:
                return None
            
            if name is not None:
                project.name = name
            if description is not None:
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
        """Get all projects with calculated metrics"""
        try:
            all_projects = self.get_all_projects()
            projects_with_data = []
            
            for project in all_projects:
                # Get all work items for this project
                work_items = WorkItem.query.filter_by(project_id=project.id).all()
                
                # Calculate totals
                total_budgeted_hours = sum(item.budgeted_man_hours or 0 for item in work_items)
                total_earned_hours = sum(item.earned_man_hours or 0 for item in work_items)
                total_budgeted_quantity = sum(item.budgeted_quantity or 0 for item in work_items)
                total_earned_quantity = sum(item.earned_quantity or 0 for item in work_items)
                
                # Calculate overall progress percentage
                overall_progress = 0
                if total_budgeted_hours > 0:
                    overall_progress = (total_earned_hours / total_budgeted_hours) * 100
                
                # Create a dictionary with project and its calculated values
                project_data = {
                    'project': project,
                    'total_budgeted_hours': total_budgeted_hours,
                    'total_earned_hours': total_earned_hours,
                    'total_budgeted_quantity': total_budgeted_quantity,
                    'total_earned_quantity': total_earned_quantity,
                    'overall_progress': overall_progress
                }
                
                projects_with_data.append(project_data)
            
            return projects_with_data
        except Exception as e:
            print(f"Error getting projects with metrics: {str(e)}")
            return []
