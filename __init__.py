import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Configure database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'ev_data.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    
    # Register blueprints
    from .routes import main_bp
    from .routes_reports import reports_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(reports_bp)
    
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
    
    return app
