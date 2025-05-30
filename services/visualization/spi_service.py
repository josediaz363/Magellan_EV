"""
Schedule Performance Index (SPI) visualization service for Magellan EV Tracker v2.0
This service provides data for the Schedule Performance Index chart.
"""
from services.visualization.data_service import VisualizationDataService
from models import Project, WorkItem
import json
import datetime

class SPIService(VisualizationDataService):
    """Service for Schedule Performance Index visualization data"""
    
    def get_data(self, project_id):
        """Get data for the Schedule Performance Index chart"""
        # Check cache first
        if project_id in self.cache:
            return self.cache[project_id]
        
        try:
            project = self.get_by_id(Project, project_id)
            if not project:
                return {
                    'error': 'Project not found',
                    'data': {
                        'spi_values': [],
                        'current_spi': 0
                    }
                }
            
            # Get all work items for this project
            work_items = WorkItem.query.filter_by(project_id=project_id).all()
            
            # Get progress history for each work item and organize by date
            actual_by_date = {}
            planned_by_date = {}
            
            for item in work_items:
                try:
                    # Get progress history (if available)
                    history = json.loads(getattr(item, 'progress_history', '[]') or '[]')
                    
                    for entry in history:
                        if 'date' in entry and 'progress' in entry:
                            try:
                                # Parse date
                                date_str = entry['date'].split('T')[0]  # Get just the date part
                                
                                if date_str not in actual_by_date:
                                    actual_by_date[date_str] = 0
                                    planned_by_date[date_str] = 0
                                
                                # Add weighted progress to actual
                                actual_by_date[date_str] += (entry['progress'] * (item.budgeted_man_hours or 0) / 100)
                                
                                # For planned progress, we would ideally use project schedule data
                                # For this implementation, we'll use a simplified approach
                                # Assume linear progress based on project duration
                                # In a real implementation, this would come from project schedule data
                                planned_by_date[date_str] += ((item.budgeted_man_hours or 0) * 0.03)  # Simplified assumption
                            except Exception as e:
                                print(f"Error processing history entry: {str(e)}")
                except Exception as e:
                    print(f"Error processing work item history: {str(e)}")
            
            # Calculate SPI for each date
            spi_values = []
            current_spi = 0
            
            dates = sorted(actual_by_date.keys())
            cumulative_actual = 0
            cumulative_planned = 0
            
            for date_str in dates:
                cumulative_actual += actual_by_date[date_str]
                cumulative_planned += planned_by_date[date_str]
                
                spi = 1.0  # Default to 1.0 (on schedule)
                if cumulative_planned > 0:
                    spi = cumulative_actual / cumulative_planned
                
                spi_values.append({
                    'date': date_str,
                    'spi': round(spi, 2)
                })
            
            # Get current SPI (most recent value)
            if spi_values:
                current_spi = spi_values[-1]['spi']
            
            # Format data for SPI chart
            result = {
                'project_name': project.name,
                'data': {
                    'spi_values': spi_values,
                    'current_spi': current_spi
                }
            }
            
            # Cache the result
            self.cache[project_id] = result
            
            return result
        except Exception as e:
            print(f"Error getting SPI data: {str(e)}")
            return {
                'error': str(e),
                'data': {
                    'spi_values': [],
                    'current_spi': 0
                }
            }
