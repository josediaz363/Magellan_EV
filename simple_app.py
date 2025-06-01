"""
Updated simple_app.py for Magellan EV Tracker v3.0
- Integrates automatic database migration on startup
- Ensures database schema is always in sync with application models
- Eliminates need for manual migration steps
- Uses persistent PostgreSQL database for Railway deployment
- Adds extensive logging for debugging database issues
"""

from flask import Flask, render_template, redirect, url_for
from models import db
from routes import main_bp
import os
from auto_migration import setup_auto_migration
import logging

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
    # Use PostgreSQL for Railway deployment (more reliable than SQLite for persistence)
    db_url = os.environ.get('DATABASE_URL')
    if db_url and db_url.startswith('postgres://'):
        # Replace postgres:// with postgresql:// for SQLAlchemy 1.4+
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    if not db_url:
        # Fallback to persistent SQLite if PostgreSQL URL not provided
        db_url = 'sqlite:////data/magellan.db'
        # Ensure the directory exists
        os.makedirs('/data', exist_ok=True)
        logger.info("Using persistent SQLite database at /data/magellan.db")
    else:
        logger.info("Using PostgreSQL database from Railway")
    
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
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
        from models import Project
        project_count = Project.query.count()
        logger.info(f"Database connection test: Found {project_count} projects")
        
    except Exception as e:
        logger.error(f"Error during application startup: {str(e)}")
        raise

if __name__ == '__main__':
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
