"""
WorkItem service for Magellan EV Tracker v3.0
Provides data access and business logic for work items
"""
from models import WorkItem, SubJob, CostCode, db


class WorkItemService:
    """
    Service for work item-related operations
    """
    
    @staticmethod
    def get_all_work_items():
        """
        Get all work items
        
        Returns:
            list: List of all work items
        """
        return WorkItem.query.all()
    
    @staticmethod
    def get_recent_work_items(limit=10):
        """
        Get recent work items
        
        Args:
            limit (int): Maximum number of work items to return
            
        Returns:
            list: List of recent work items
        """
        return WorkItem.query.order_by(WorkItem.id.desc()).limit(limit).all()
    
    @staticmethod
    def get_work_item_details(work_item_id):
        """
        Get work item details with all necessary related data
        
        Args:
            work_item_id (int): Work Item ID
            
        Returns:
            WorkItem: Work Item object with related data
        """
        if not work_item_id:
            return None
            
        return WorkItem.query.get(work_item_id)
    
    @staticmethod
    def get_sub_job_work_items(sub_job_id):
        """
        Get all work items for a sub job
        
        Args:
            sub_job_id (int): Sub Job ID
            
        Returns:
            list: List of work items for the sub job
        """
        return WorkItem.query.filter_by(sub_job_id=sub_job_id).all()
    
    @staticmethod
    def create_work_item(sub_job_id, cost_code_id, description, budgeted_quantity, 
                        budgeted_man_hours, earned_quantity=0, earned_man_hours=0):
        """
        Create a new work item
        
        Args:
            sub_job_id (int): Sub Job ID
            cost_code_id (int): Cost Code ID
            description (str): Work item description
            budgeted_quantity (float): Budgeted quantity
            budgeted_man_hours (float): Budgeted man hours
            earned_quantity (float, optional): Earned quantity
            earned_man_hours (float, optional): Earned man hours
            
        Returns:
            WorkItem: Newly created work item
        """
        # Get the sub job to associate with project
        sub_job = SubJob.query.get(sub_job_id)
        if not sub_job:
            return None
            
        # Get the cost code to validate it exists
        cost_code = CostCode.query.get(cost_code_id)
        if not cost_code:
            return None
            
        work_item = WorkItem(
            sub_job_id=sub_job_id,
            project_id=sub_job.project_id,
            cost_code_id=cost_code_id,
            description=description,
            budgeted_quantity=budgeted_quantity,
            budgeted_man_hours=budgeted_man_hours,
            earned_quantity=earned_quantity,
            earned_man_hours=earned_man_hours
        )
        db.session.add(work_item)
        db.session.commit()
        return work_item
    
    @staticmethod
    def update_work_item(work_item_id, description=None, budgeted_quantity=None, 
                        budgeted_man_hours=None, earned_quantity=None, earned_man_hours=None):
        """
        Update an existing work item
        
        Args:
            work_item_id (int): Work Item ID
            description (str, optional): New work item description
            budgeted_quantity (float, optional): New budgeted quantity
            budgeted_man_hours (float, optional): New budgeted man hours
            earned_quantity (float, optional): New earned quantity
            earned_man_hours (float, optional): New earned man hours
            
        Returns:
            WorkItem: Updated work item
        """
        work_item = WorkItem.query.get(work_item_id)
        if work_item:
            if description is not None:
                work_item.description = description
            if budgeted_quantity is not None:
                work_item.budgeted_quantity = budgeted_quantity
            if budgeted_man_hours is not None:
                work_item.budgeted_man_hours = budgeted_man_hours
            if earned_quantity is not None:
                work_item.earned_quantity = earned_quantity
            if earned_man_hours is not None:
                work_item.earned_man_hours = earned_man_hours
            
            db.session.commit()
        return work_item
    
    @staticmethod
    def delete_work_item(work_item_id):
        """
        Delete a work item
        
        Args:
            work_item_id (int): Work Item ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        work_item = WorkItem.query.get(work_item_id)
        if work_item:
            db.session.delete(work_item)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def calculate_work_item_metrics(work_item):
        """
        Calculate metrics for a work item
        
        Args:
            work_item (WorkItem): Work Item object
            
        Returns:
            dict: Dictionary of work item metrics
        """
        # Calculate percent complete
        percent_complete = 0.0
        if work_item.budgeted_man_hours and work_item.budgeted_man_hours > 0:
            percent_complete = (work_item.earned_man_hours / work_item.budgeted_man_hours) * 100
            
        return {
            'percent_complete': round(percent_complete, 1),
            'earned_hours': round(work_item.earned_man_hours or 0, 1),
            'budgeted_hours': round(work_item.budgeted_man_hours or 0, 1),
            'earned_quantity': round(work_item.earned_quantity or 0, 1),
            'budgeted_quantity': round(work_item.budgeted_quantity or 0, 1)
        }
