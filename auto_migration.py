"""
Auto-migration implementation for Magellan EV Tracker v3.0
- Automatically adds the budgeted_hours column to the sub_job table on application startup
- Ensures database schema is always in sync with application models
- Eliminates need for manual migration steps
"""

from flask import Flask
from models import db, SubJob
import os
import logging
from sqlalchemy import inspect, Column, Float
from sqlalchemy.exc import OperationalError

def setup_auto_migration(app):
    """
    Configure automatic database migrations on application startup
    """
    with app.app_context():
        inspector = inspect(db.engine)
        
        # Check if the sub_job table exists
        if 'sub_job' in inspector.get_table_names():
            # Get columns in the sub_job table
            columns = [column['name'] for column in inspector.get_columns('sub_job')]
            
            # Check if budgeted_hours column exists
            if 'budgeted_hours' not in columns:
                try:
                    # Add the budgeted_hours column
                    db.engine.execute("ALTER TABLE sub_job ADD COLUMN budgeted_hours FLOAT DEFAULT 0.0")
                    app.logger.info("Added budgeted_hours column to sub_job table")
                except OperationalError as e:
                    app.logger.error(f"Error adding budgeted_hours column: {str(e)}")
                    # Try alternative approach for SQLite
                    try:
                        with db.engine.begin() as conn:
                            conn.execute("ALTER TABLE sub_job ADD COLUMN budgeted_hours FLOAT DEFAULT 0.0")
                        app.logger.info("Added budgeted_hours column to sub_job table (alternative method)")
                    except Exception as e2:
                        app.logger.error(f"Failed to add budgeted_hours column (alternative method): {str(e2)}")
            else:
                app.logger.info("budgeted_hours column already exists in sub_job table")
        else:
            app.logger.info("sub_job table doesn't exist yet, will be created with all columns")
            
        # Ensure tables are created if they don't exist
        db.create_all()
        app.logger.info("Database schema check and migration completed")
