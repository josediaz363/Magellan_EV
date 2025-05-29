"""
Donut chart visualization service for Magellan EV Tracker v2.0
This service provides data for the overall progress donut chart.
"""
from services.visualization.data_service import VisualizationDataService
from models import Project, WorkItem

class DonutService(VisualizationDataService):
    """Service for donut chart visualization data"""
    
    def get_data(self, project_id):
        """Get data for the overall progress donut chart"""
        # Check cache first
        if project_id in self.cache:
            return self.cache[project_id]
        
        try:
            project = self.get_by_id(Project, project_id)
            if not project:
                return {
                    'error': 'Project not found',
                    'data': {
                        'percentage': 0,
                        'earned': 0,
                        'budgeted': 0
                    }
                }
            
            # Get all work items for this project
            work_items = WorkItem.query.filter_by(project_id=project_id).all()
            
            # Calculate totals
            total_budgeted_hours = sum(item.budgeted_man_hours or 0 for item in work_items)
            total_earned_hours = sum(item.earned_man_hours or 0 for item in work_items)
            
            # Calculate overall progress percentage
            overall_progress = 0
            if total_budgeted_hours > 0:
                overall_progress = (total_earned_hours / total_budgeted_hours) * 100
            
            # Format data for donut chart
            result = {
                'project_name': project.name,
                'data': {
                    'percentage': round(overall_progress, 1),
                    'earned': round(total_earned_hours, 1),
                    'budgeted': round(total_budgeted_hours, 1)
                }
            }
            
            # Cache the result
            self.cache[project_id] = result
            
            return result
        except Exception as e:
            print(f"Error getting donut chart data: {str(e)}")
            return {
                'error': str(e),
                'data': {
                    'percentage': 0,
                    'earned': 0,
                    'budgeted': 0
                }
            }
