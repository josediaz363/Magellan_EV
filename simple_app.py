"""
Updated simple_app.py for Magellan EV Tracker v3.0
- Integrates automatic database migration on startup
- Ensures database schema is always in sync with application models
- Eliminates need for manual migration steps
- Uses persistent SQLite database for Railway deployment
- Adds extensive logging for debugging database issues
- Fixes database persistence issues with explicit transaction management
"""

from flask import Flask, render_template, redirect, url_for
from models import db
from routes import main_bp
import os
from auto_migration import setup_auto_migration
import logging
import sqlite3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Configure database - ensure persistent storage on Railway
if os.environ.get('RAILWAY_ENVIRONMENT'):
    # Use SQLite for Railway deployment (per user preference for stability)
    db_path = '/data/magellan.db'
    # Ensure the directory exists
    os.makedirs('/data', exist_ok=True)
    
    # Test if the directory is writable
    try:
        test_file = '/data/write_test.txt'
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        logger.info("Directory /data is writable")
    except Exception as e:
        logger.error(f"Directory /data is not writable: {str(e)}")
        # Fallback to tmp directory which should be writable
        db_path = '/tmp/magellan.db'
        logger.info(f"Falling back to {db_path}")
    
    # Test SQLite connection directly
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")  # Use WAL mode for better concurrency
        cursor.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY)")
        cursor.execute("INSERT INTO test_table VALUES (1)")
        conn.commit()
        cursor.execute("SELECT * FROM test_table")
        result = cursor.fetchall()
        logger.info(f"SQLite direct test: {result}")
        cursor.execute("DROP TABLE test_table")
        conn.commit()
        conn.close()
        logger.info(f"SQLite database at {db_path} is writable")
    except Exception as e:
        logger.error(f"SQLite database test failed: {str(e)}")
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    logger.info(f"Using persistent SQLite database at {db_path}")
else:
    # Local development uses local file
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///magellan.db'
    logger.info("Using local SQLite database at magellan.db")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_for_magellan')

# Initialize database
db.init_app(app)

# Register blueprints
app.register_blueprint(main_bp)

# Root route redirects to dashboard
@app.route('/')
def index():
    return redirect(url_for('main.dashboard'))

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"500 error: {str(e)}")
    return render_template('500.html'), 500

# Run auto-migration on startup
with app.app_context():
    try:
        # Log database configuration
        logger.info(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        # Ensure database tables exist
        db.create_all()
        logger.info("Database tables created successfully")
        
        # Run automatic migration to add budgeted_hours column
        setup_auto_migration(app)
        logger.info("Auto-migration completed successfully")
        
        # Test database connection by counting projects
        from models import Project, CostCode
        project_count = Project.query.count()
        logger.info(f"Database connection test: Found {project_count} projects")
        
        # Test database write capability by creating and immediately deleting a test cost code
        try:
            test_cost_code = CostCode(
                project_id=1,
                cost_code_id_str="TEST-DELETE-ME",
                description="Test cost code to verify database writes",
                discipline="Test"
            )
            db.session.add(test_cost_code)
            db.session.commit()
            logger.info(f"Test cost code created with ID: {test_cost_code.id}")
            
            # Verify it was saved
            saved_code = CostCode.query.filter_by(cost_code_id_str="TEST-DELETE-ME").first()
            if saved_code:
                logger.info("Test cost code was successfully saved and retrieved")
                # Delete the test cost code
                db.session.delete(saved_code)
                db.session.commit()
                logger.info("Test cost code was successfully deleted")
            else:
                logger.error("Test cost code was not found after creation - database write issue detected")
        except Exception as e:
            logger.error(f"Error during database write test: {str(e)}")
            db.session.rollback()
        
    except Exception as e:
        logger.error(f"Error during application startup: {str(e)}")
        raise

# Add a custom SQLAlchemy event listener to log all commits
from sqlalchemy import event

@event.listens_for(db.session, 'before_commit')
def before_commit(session):
    logger.info(f"Before commit: {len(session.new)} new, {len(session.dirty)} dirty, {len(session.deleted)} deleted objects")
    for obj in session.new:
        logger.info(f"New object to be committed: {type(obj).__name__} {getattr(obj, 'id', 'no id')}")

@event.listens_for(db.session, 'after_commit')
def after_commit(session):
    logger.info("Transaction committed successfully")

@event.listens_for(db.session, 'after_rollback')
def after_rollback(session):
    logger.error("Transaction rolled back")

if __name__ == '__main__':
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
