"""
Migration script to add budgeted_hours field to SubJob model
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import sys
import alembic.command
import alembic.config
from sqlalchemy import Column, Float

# Create a minimal Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///magellan.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

def run_migration():
    """
    Add budgeted_hours column to sub_job table if it doesn't exist
    """
    print("Starting migration to add budgeted_hours field to SubJob model...")
    
    # Check if the column already exists to make the migration idempotent
    with app.app_context():
        try:
            # Connect to the database
            conn = db.engine.connect()
            
            # Check if the column exists in the sub_job table
            table_info = conn.execute("PRAGMA table_info(sub_job)").fetchall()
            column_names = [col[1] for col in table_info]
            
            if 'budgeted_hours' not in column_names:
                print("Adding budgeted_hours column to sub_job table...")
                conn.execute("ALTER TABLE sub_job ADD COLUMN budgeted_hours FLOAT DEFAULT 0.0")
                print("Migration completed successfully!")
            else:
                print("budgeted_hours column already exists in sub_job table. No migration needed.")
                
            conn.close()
            return True
        except Exception as e:
            print(f"Error during migration: {str(e)}")
            return False

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("Migration completed successfully.")
        sys.exit(0)
    else:
        print("Migration failed.")
        sys.exit(1)
