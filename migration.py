"""
Migration script to fix database schema issues in Magellan EV Tracker v3.0
- Adds 'area' field to SubJob model
- Updates code to remove 'discipline' references from SubJob workflows
"""

from models import db, SubJob
import sqlalchemy as sa
import traceback

def run_migration():
    print("Starting database migration...")
    
    try:
        # Check if area column already exists
        with db.engine.connect() as conn:
            result = conn.execute(sa.text("PRAGMA table_info(sub_job)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'area' not in columns:
                print("Adding 'area' column to sub_job table...")
                conn.execute(sa.text("ALTER TABLE sub_job ADD COLUMN area TEXT"))
                conn.commit()
                print("Successfully added 'area' column")
            else:
                print("'area' column already exists in sub_job table")
                
        # Set default values for existing records
        print("Setting default values for existing records...")
        sub_jobs = SubJob.query.all()
        for sub_job in sub_jobs:
            if not hasattr(sub_job, 'area') or not sub_job.area:
                sub_job.area = "Main"  # Default value
        db.session.commit()
        print("Successfully updated existing records")
        
        print("Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    run_migration()
