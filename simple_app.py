"""
Updated simple_app.py for Magellan EV Tracker v3.0
- Integrates automatic database migration on startup
- Ensures database schema is always in sync with application models
- Eliminates need for manual migration steps
- Uses persistent database storage for Railway deployment
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

# Create Flask app
app = Flask(__name__)

# Configure database - ensure persistent storage on Railway
if os.environ.get('RAILWAY_ENVIRONMENT'):
    # Use persistent storage path for Railway deployment
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////data/magellan.db'
    # Ensure the directory exists
    os.makedirs('/data', exist_ok=True)
    logging.info("Using persistent database at /data/magellan.db")
else:
    # Local development uses local file
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///magellan.db'
    logging.info("Using local database at magellan.db")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_for_magellan')

# Initialize database
db.init_app(app)

# Register blueprints
app.register_blueprint(main_bp)

# Root route redirects to main blueprint
@app.route('/')
def index():
    return redirect(url_for('main.dashboard'))

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# Run auto-migration on startup
with app.app_context():
    # Ensure database tables exist
    db.create_all()
    
    # Run automatic migration to add budgeted_hours column
    setup_auto_migration(app)
    
    # Log database location for debugging
    logging.info(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

if __name__ == '__main__':
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
