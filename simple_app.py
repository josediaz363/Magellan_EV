"""
Updated simple_app.py for Magellan EV Tracker v3.0
- Redirects root URL to dashboard page
- Integrates automatic database migration on startup
- Ensures database schema is always in sync with application models
- Uses persistent database location for Railway.app environment
- Includes proper error handling
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

# Configure database with persistent storage path
# Use absolute path for SQLite to ensure persistence in Railway.app environment
if os.environ.get('DATABASE_URL'):
    # Use provided DATABASE_URL if available
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
else:
    # Use absolute path for SQLite in a persistent location
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'data')
    os.makedirs(db_path, exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(db_path, "magellan.db")}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,  # Verify connections before use
    'pool_recycle': 300,    # Recycle connections every 5 minutes
}
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_for_magellan')

# Initialize database
db.init_app(app)

# Register blueprints
app.register_blueprint(main_bp)

# Root route redirects to dashboard
@app.route('/')
def index():
    # Redirect to dashboard instead of rules_of_credit
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
    logging.info(f"Using database: {app.config['SQLALCHEMY_DATABASE_URI']}")

if __name__ == '__main__':
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
