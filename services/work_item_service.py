"""
Fixed WorkItemService with count_work_items method for Magellan EV Tracker v3.0
- Added missing count_work_items method required by dashboard
- Enhanced error handling and logging
"""
from models import WorkItem, db
import logging

# Configure logging
logger = logging.getLogger(__name__)

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
        try:
            work_items = WorkItem.query.all()
            logger.info(f"Retrieved {len(work_items)} work items")
            return work_items
        except Exception as e:
            logger.error(f"Error retrieving all work items: {str(e)}")
            return []
    
    @staticmethod
    def get_work_item_by_id(work_item_id):
        """
        Get work item by ID
        
        Args:
            work_item_id (int): Work Item ID
            
        Returns:
            WorkItem: Work Item object
        """
        try:
            work_item = WorkItem.query.get(work_item_id)
            if work_item:
                logger.info(f"Retrieved work item: {work_item.id}, {work_item.name}")
            return work_item
        except Exception as e:
            logger.error(f"Error retrieving work item {work_item_id}: {str(e)}")
            return None
    
    @staticmethod
    def get_sub_job_work_items(sub_job_id):
        """
        Get all work items for a sub job
        
        Args:
            sub_job_id (int): Sub Job ID
            
        Returns:
            list: List of work items for the sub job
        """
        try:
            work_items = WorkItem.query.filter_by(sub_job_id=sub_job_id).all()
            logger.info(f"Retrieved {len(work_items)} work items for sub job {sub_job_id}")
            return work_items
        except Exception as e:
            logger.error(f"Error retrieving work items for sub job {sub_job_id}: {str(e)}")
            return []
    
    @staticmethod
    def get_recent_work_items(limit=10):
        """
        Get most recent work items
        
        Args:
            limit (int): Maximum number of work items to return
            
        Returns:
            list: List of recent work items
        """
        try:
            work_items = WorkItem.query.order_by(WorkItem.id.desc()).limit(limit).all()
            logger.info(f"Retrieved {len(work_items)} recent work items")
            return work_items
        except Exception as e:
            logger.error(f"Error retrieving recent work items: {str(e)}")
            return []
    
    @staticmethod
    def count_work_items():
        """
        Count total number of work items
        
        Returns:
            int: Count of work items
        """
        try:
            count = WorkItem.query.count()
            logger.info(f"Counted {count} work items")
            return count
        except Exception as e:
            logger.error(f"Error counting work items: {str(e)}")
            return 0
    
    @staticmethod
    def create_work_item(sub_job_id, name, work_item_id_str, description, quantity, unit, cost_code_id=None):
        """
        Create a new work item
        
        Args:
            sub_job_id (int): Sub Job ID
            name (str): Work item name
            work_item_id_str (str): Work item ID string
            description (str): Work item description
            quantity (float): Quantity
            unit (str): Unit of measurement
            cost_code_id (int, optional): Cost Code ID
            
        Returns:
            WorkItem: Newly created work item
        """
        try:
            work_item = WorkItem(
                sub_job_id=sub_job_id,
                name=name,
                work_item_id_str=work_item_id_str,
                description=description,
                quantity=quantity,
                unit=unit,
                cost_code_id=cost_code_id
            )
            db.session.add(work_item)
            db.session.commit()
            logger.info(f"Work item created successfully: {work_item.id}, {work_item.name}")
            return work_item
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating work item: {str(e)}")
            raise
    
    @staticmethod
    def update_work_item(work_item_id, name, description, quantity, unit, cost_code_id=None):
        """
        Update an existing work item
        
        Args:
            work_item_id (int): Work Item ID
            name (str): New work item name
            description (str): New work item description
            quantity (float): New quantity
            unit (str): New unit of measurement
            cost_code_id (int, optional): New Cost Code ID
            
        Returns:
            WorkItem: Updated work item
        """
        try:
            work_item = WorkItem.query.get(work_item_id)
            if work_item:
                work_item.name = name
                work_item.description = description
                work_item.quantity = quantity
                work_item.unit = unit
                work_item.cost_code_id = cost_code_id
                db.session.commit()
                logger.info(f"Work item updated successfully: {work_item.id}, {work_item.name}")
            return work_item
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating work item {work_item_id}: {str(e)}")
            raise
    
    @staticmethod
    def delete_work_item(work_item_id):
        """
        Delete a work item
        
        Args:
            work_item_id (int): Work Item ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            work_item = WorkItem.query.get(work_item_id)
            if work_item:
                db.session.delete(work_item)
                db.session.commit()
                logger.info(f"Work item deleted successfully: {work_item_id}")
                return True
            return False
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting work item {work_item_id}: {str(e)}")
            return False
