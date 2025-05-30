"""
S-curve visualization service for Magellan EV Tracker v2.0
This service provides data for the S-curve chart showing actual, planned, and forecasted progress.
"""
from services.visualization.data_service import VisualizationDataService
from models import Project, WorkItem
import json
import datetime
from datetime import timedelta

class SCurveService(VisualizationDataService):
    """Service for S-curve visualization data"""
    
    def get_data(self, project_id):
        """Get data for the S-curve chart"""
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
                        'planned': [],
                        'forecast': []
                    }
                }
            
            # Get all work items for this project
            work_items = WorkItem.query.filter_by(project_id=project_id).all()
            
            # Calculate total budgeted hours
            total_budgeted_hours = sum(item.budgeted_man_hours or 0 for item in work_items)
            
            if total_budgeted_hours == 0:
                return {
                    'error': 'No budgeted hours found',
                    'data': {
                        'actual': [],
                        'planned': [],
                        'forecast': []
                    }
                }
            
            # Get progress history for each work item and organize by date
            progress_by_date = {}
            
            for item in work_items:
                try:
                    # Get progress history (if available)
                    history = json.loads(getattr(item, 'progress_history', '[]') or '[]')
                    
                    for entry in history:
                        if 'date' in entry and 'progress' in entry:
                            try:
                                # Parse date
                                date_str = entry['date'].split('T')[0]  # Get just the date part
                                
                                if date_str not in progress_by_date:
                                    progress_by_date[date_str] = 0
                                
                                # Add weighted progress
                                progress_by_date[date_str] += (entry['progress'] * (item.budgeted_man_hours or 0) / 100)
                            except Exception as e:
                                print(f"Error processing history entry: {str(e)}")
                except Exception as e:
                    print(f"Error processing work item history: {str(e)}")
            
            # Convert to cumulative progress
            dates = sorted(progress_by_date.keys())
            actual_curve = []
            cumulative_progress = 0
            
            for date_str in dates:
                cumulative_progress += progress_by_date[date_str]
                percentage = (cumulative_progress / total_budgeted_hours) * 100
                actual_curve.append({
                    'date': date_str,
                    'percentage': round(percentage, 1)
                })
            
            # Generate planned curve (simplified S-curve)
            # In a real implementation, this would come from project schedule data
            planned_curve = []
            
            # If we have actual data, use the first and last dates as boundaries
            if dates:
                start_date = datetime.datetime.fromisoformat(dates[0])
                
                # Assume project end date is 3 months from start if no other data
                if len(dates) > 1:
                    end_date = datetime.datetime.fromisoformat(dates[-1])
                    # Add 1 month buffer to end date
                    end_date = end_date + timedelta(days=30)
                else:
                    end_date = start_date + timedelta(days=90)
                
                # Generate planned S-curve points
                total_days = (end_date - start_date).days
                if total_days > 0:
                    for day in range(0, total_days + 1, max(1, total_days // 20)):  # Max 20 points
                        current_date = start_date + timedelta(days=day)
                        date_str = current_date.strftime('%Y-%m-%d')
                        
                        # S-curve formula (simplified)
                        # Slow start, faster middle, slow end
                        x = day / total_days
                        if x < 0.2:
                            # Slow start (0-10%)
                            percentage = 10 * (x / 0.2)
                        elif x < 0.8:
                            # Faster middle (10-90%)
                            percentage = 10 + 80 * ((x - 0.2) / 0.6)
                        else:
                            # Slow end (90-100%)
                            percentage = 90 + 10 * ((x - 0.8) / 0.2)
                        
                        planned_curve.append({
                            'date': date_str,
                            'percentage': round(percentage, 1)
                        })
            
            # Generate forecast curve
            forecast_curve = []
            
            # If we have actual data, use the last point as starting point for forecast
            if actual_curve:
                last_actual = actual_curve[-1]
                last_date = datetime.datetime.fromisoformat(last_actual['date'])
                last_percentage = last_actual['percentage']
                
                # Find corresponding planned percentage for this date
                planned_percentage = 0
                for point in planned_curve:
                    if point['date'] == last_actual['date']:
                        planned_percentage = point['percentage']
                        break
                
                # Calculate performance factor
                performance_factor = 1.0
                if planned_percentage > 0:
                    performance_factor = last_percentage / planned_percentage
                
                # Ensure factor is reasonable
                performance_factor = max(0.5, min(1.5, performance_factor))
                
                # Generate forecast points
                for point in planned_curve:
                    point_date = datetime.datetime.fromisoformat(point['date'])
                    if point_date > last_date:
                        # Adjust planned percentage by performance factor
                        adjusted_percentage = min(100, point['percentage'] * performance_factor)
                        
                        forecast_curve.append({
                            'date': point['date'],
                            'percentage': round(adjusted_percentage, 1)
                        })
            
            # Format data for S-curve chart
            result = {
                'project_name': project.name,
                'data': {
                    'actual': actual_curve,
                    'planned': planned_curve,
                    'forecast': forecast_curve
                }
            }
            
            # Cache the result
            self.cache[project_id] = result
            
            return result
        except Exception as e:
            print(f"Error getting S-curve data: {str(e)}")
            return {
                'error': str(e),
                'data': {
                    'actual': [],
                    'planned': [],
                    'forecast': []
                }
            }
