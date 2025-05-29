"""
Progress histogram visualization service for Magellan EV Tracker v2.0
This service provides data for the progress histogram chart.
"""
from services.visualization.data_service import VisualizationDataService
from models import Project, WorkItem
import json
import datetime

class HistogramService(VisualizationDataService):
    """Service for progress histogram visualization data"""
    
    def get_data(self, project_id):
        """Get data for the progress histogram chart"""
        # Check cache first
        if project_id in self.cache:
            return self.cache[project_id]
        
        try:
            project = self.get_by_id(Project, project_id)
            if not project:
                return {
                    'error': 'Project not found',
                    'data': {
                        'actual': [],
                        'planned': []
                    }
                }
            
            # Get all work items for this project
            work_items = WorkItem.query.filter_by(project_id=project_id).all()
            
            # Calculate weekly actual and planned progress
            weekly_actual = []
            weekly_planned = []
            
            # Get progress history for each work item
            for item in work_items:
                try:
                    # Get progress history (if available)
                    history = json.loads(getattr(item, 'progress_history', '[]') or '[]')
                    
                    for entry in history:
                        if 'date' in entry and 'progress' in entry:
                            try:
                                # Parse date
                                date_obj = datetime.datetime.fromisoformat(entry['date'])
                                week_key = f"{date_obj.year}-W{date_obj.isocalendar()[1]}"
                                
                                # Add to weekly actual
                                found = False
                                for week_data in weekly_actual:
                                    if week_data['week'] == week_key:
                                        week_data['progress'] += entry['progress'] * (item.budgeted_man_hours or 0) / 100
                                        found = True
                                        break
                                
                                if not found:
                                    weekly_actual.append({
                                        'week': week_key,
                                        'progress': entry['progress'] * (item.budgeted_man_hours or 0) / 100
                                    })
                            except Exception as e:
                                print(f"Error processing history entry: {str(e)}")
                except Exception as e:
                    print(f"Error processing work item history: {str(e)}")
            
            # Sort weekly data by week
            weekly_actual.sort(key=lambda x: x['week'])
            
            # Calculate cumulative progress
            cumulative_actual = []
            cumulative_planned = []
            
            total_budgeted_hours = sum(item.budgeted_man_hours or 0 for item in work_items)
            
            if total_budgeted_hours > 0:
                cumulative_progress = 0
                for week_data in weekly_actual:
                    cumulative_progress += week_data['progress']
                    cumulative_actual.append({
                        'week': week_data['week'],
                        'progress': (cumulative_progress / total_budgeted_hours) * 100
                    })
            
            # Format data for histogram chart
            result = {
                'project_name': project.name,
                'data': {
                    'weekly': {
                        'actual': weekly_actual,
                        'planned': weekly_planned
                    },
                    'cumulative': {
                        'actual': cumulative_actual,
                        'planned': cumulative_planned
                    }
                }
            }
            
            # Cache the result
            self.cache[project_id] = result
            
            return result
        except Exception as e:
            print(f"Error getting histogram data: {str(e)}")
            return {
                'error': str(e),
                'data': {
                    'weekly': {
                        'actual': [],
                        'planned': []
                    },
                    'cumulative': {
                        'actual': [],
                        'planned': []
                    }
                }
            }
