"""
Updated simple_app.py for Magellan EV Tracker v3.0
- Integrates automatic database migration on startup
- Ensures database schema is always in sync with application models
- Eliminates need for manual migration steps
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

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///magellan.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_for_magellan')

# Initialize database
db.init_app(app)

# Register blueprints
app.register_blueprint(main_bp)

# Root route redirects to main blueprint
@app.route('/')
def index():
    return redirect(url_for('main.projects'))

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

if __name__ == '__main__':
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
