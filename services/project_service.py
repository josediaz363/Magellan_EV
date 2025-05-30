from models import SubJob, Project
from services.base_service import BaseService
from sqlalchemy.orm import joinedload
import traceback

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
            traceback.print_exc()
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
        """Get all projects with their metrics"""
        try:
            # Use joinedload to efficiently load related sub jobs and work items
            projects = self.db.session.query(Project).options(
                joinedload(Project.sub_jobs),
                joinedload(Project.work_items)
            ).all()
            
            result = []
            for project in projects:
                # Calculate project-level totals
                total_budgeted_hours = sum(item.budgeted_man_hours or 0 for item in project.work_items)
                total_earned_hours = sum(item.earned_man_hours or 0 for item in project.work_items)
                
                # Calculate overall progress percentage
                overall_progress = 0
                if total_budgeted_hours > 0:
                    overall_progress = (total_earned_hours / total_budgeted_hours) * 100
                
                # Create a dictionary with project and its calculated values
                project_data = {
                    'project': project,
                    'total_budgeted_hours': total_budgeted_hours,
                    'total_earned_hours': total_earned_hours,
                    'overall_progress': overall_progress,
                    'sub_job_count': len(project.sub_jobs),
                    'work_item_count': len(project.work_items)
                }
                
                result.append(project_data)
            
            return result
        except Exception as e:
            print(f"Error getting projects with metrics: {str(e)}")
            traceback.print_exc()
            return []
