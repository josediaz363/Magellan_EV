"""
Fixed simple_app.py for Magellan EV Tracker v3.0
- Simplified database configuration to match v1.32 pattern
- Uses consistent SQLite path that works reliably on Railway
- Maintains service architecture while ensuring database persistence
"""

from flask import Flask, render_template, redirect, url_for
from models import db
from routes import main_bp
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Configure database - simplified to match v1.32 pattern
# Use instance folder for SQLite database (works reliably on Railway)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///magellan_ev.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_for_magellan')

logger.info(f"Using SQLite database at: {app.config['SQLALCHEMY_DATABASE_URI']}")

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

# Create database tables on startup
with app.app_context():
    try:
        # Ensure database tables exist
        db.create_all()
        logger.info("Database tables created successfully")
        
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
