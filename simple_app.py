from flask import Flask
from .routes import main_bp
from .models import db
import os
import sqlite3

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configure the SQLite database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///magellan_ev.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'magellan-ev-secret-key'  # Required for flash messages
    
    # Initialize the database with the app
    db.init_app(app)
    
    # Register the blueprint
    app.register_blueprint(main_bp)
    
    # Create database tables and perform migrations
    with app.app_context():
        # First, create all tables that don't exist yet
        db.create_all()
        
        # Then, perform manual migration for cost_code table
        try:
            # Connect directly to SQLite to modify the schema
            conn = sqlite3.connect('instance/magellan_ev.db')
            cursor = conn.cursor()
            
            # Check if project_id column exists and has NOT NULL constraint
            cursor.execute("PRAGMA table_info(cost_code)")
            columns = cursor.fetchall()
            project_id_column = None
            for col in columns:
                if col[1] == 'project_id':
                    project_id_column = col
                    break
            
            if project_id_column and project_id_column[3] == 1:  # 1 means NOT NULL
                # SQLite doesn't support ALTER COLUMN, so we need to:
                # 1. Create a new table with the desired schema
                # 2. Copy data from the old table
                # 3. Drop the old table
                # 4. Rename the new table
                
                # Create a temporary table with the new schema
                cursor.execute("""
                CREATE TABLE cost_code_new (
                    id INTEGER PRIMARY KEY,
                    cost_code_id_str VARCHAR(50) NOT NULL,
                    description VARCHAR(200) NOT NULL,
                    discipline VARCHAR(100) NOT NULL,
                    project_id INTEGER,
                    rule_of_credit_id INTEGER,
                    FOREIGN KEY(rule_of_credit_id) REFERENCES rule_of_credit(id)
                )
                """)
                
                # Copy data from the old table
                cursor.execute("""
                INSERT INTO cost_code_new (id, cost_code_id_str, description, discipline, project_id, rule_of_credit_id)
                SELECT id, cost_code_id_str, description, discipline, project_id, rule_of_credit_id FROM cost_code
                """)
                
                # Drop the old table
                cursor.execute("DROP TABLE cost_code")
                
                # Rename the new table
                cursor.execute("ALTER TABLE cost_code_new RENAME TO cost_code")
                
                # Create the project_cost_code join table if it doesn't exist
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_cost_code (
                    id INTEGER PRIMARY KEY,
                    project_id INTEGER NOT NULL,
                    cost_code_id INTEGER NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES project(id),
                    FOREIGN KEY(cost_code_id) REFERENCES cost_code(id)
                )
                """)
                
                # Populate the join table with existing relationships
                cursor.execute("""
                INSERT INTO project_cost_code (project_id, cost_code_id)
                SELECT project_id, id FROM cost_code WHERE project_id IS NOT NULL
                """)
                
                conn.commit()
                print("Successfully migrated cost_code table schema")
            
            conn.close()
        except Exception as e:
            print(f"Error during migration: {e}")
    
    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
