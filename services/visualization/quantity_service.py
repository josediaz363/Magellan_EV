"""
Quantity distribution visualization service for Magellan EV Tracker v2.0
This service provides data for the quantity distribution chart.
"""
from services.visualization.data_service import VisualizationDataService
from models import Project, WorkItem, CostCode, DISCIPLINE_CHOICES

class QuantityService(VisualizationDataService):
    """Service for quantity distribution visualization data"""
    
    def get_data(self, project_id):
        """Get data for the quantity distribution chart"""
        # Check cache first
        if project_id in self.cache:
            return self.cache[project_id]
        
        try:
            project = self.get_by_id(Project, project_id)
            if not project:
                return {
                    'error': 'Project not found',
                    'data': {
                        'by_discipline': [],
                        'by_unit': []
                    }
                }
            
            # Get all work items for this project
            work_items = WorkItem.query.filter_by(project_id=project_id).all()
            
            # Group quantities by discipline
            quantities_by_discipline = {}
            for discipline in DISCIPLINE_CHOICES:
                quantities_by_discipline[discipline] = {
                    'budgeted': 0,
                    'earned': 0
                }
            
            # Group quantities by unit of measure
            quantities_by_unit = {}
            
            for item in work_items:
                try:
                    # Get cost code to determine discipline
                    cost_code = CostCode.query.get(item.cost_code_id)
                    if cost_code:
                        discipline = cost_code.discipline
                        
                        # Add to discipline totals
                        if discipline in quantities_by_discipline:
                            quantities_by_discipline[discipline]['budgeted'] += item.budgeted_quantity or 0
                            quantities_by_discipline[discipline]['earned'] += item.earned_quantity or 0
                        
                        # Add to unit totals
                        unit = item.unit_of_measure or 'Unknown'
                        if unit not in quantities_by_unit:
                            quantities_by_unit[unit] = {
                                'budgeted': 0,
                                'earned': 0
                            }
                        
                        quantities_by_unit[unit]['budgeted'] += item.budgeted_quantity or 0
                        quantities_by_unit[unit]['earned'] += item.earned_quantity or 0
                except Exception as e:
                    print(f"Error processing work item: {str(e)}")
            
            # Format data for quantity distribution chart
            discipline_data = []
            for discipline, quantities in quantities_by_discipline.items():
                if quantities['budgeted'] > 0:
                    discipline_data.append({
                        'discipline': discipline,
                        'budgeted': round(quantities['budgeted'], 2),
                        'earned': round(quantities['earned'], 2),
                        'percentage': round((quantities['earned'] / quantities['budgeted'] * 100) 
                                           if quantities['budgeted'] > 0 else 0, 1)
                    })
            
            unit_data = []
            for unit, quantities in quantities_by_unit.items():
                if quantities['budgeted'] > 0:
                    unit_data.append({
                        'unit': unit,
                        'budgeted': round(quantities['budgeted'], 2),
                        'earned': round(quantities['earned'], 2),
                        'percentage': round((quantities['earned'] / quantities['budgeted'] * 100) 
                                           if quantities['budgeted'] > 0 else 0, 1)
                    })
            
            # Sort by budgeted quantity (descending)
            discipline_data.sort(key=lambda x: x['budgeted'], reverse=True)
            unit_data.sort(key=lambda x: x['budgeted'], reverse=True)
            
            result = {
                'project_name': project.name,
                'data': {
                    'by_discipline': discipline_data,
                    'by_unit': unit_data
                }
            }
            
            # Cache the result
            self.cache[project_id] = result
            
            return result
        except Exception as e:
            print(f"Error getting quantity distribution data: {str(e)}")
            return {
                'error': str(e),
                'data': {
                    'by_discipline': [],
                    'by_unit': []
                }
            }
