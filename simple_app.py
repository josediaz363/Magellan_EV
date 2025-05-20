from flask import Flask, render_template, render_template_string, Blueprint
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize SQLAlchemy
db = SQLAlchemy()

# Create a blueprint
main_bp = Blueprint('main', __name__)

# Define database models
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
class RuleOfCredit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
class WorkItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    description = db.Column(db.Text)
    manhours = db.Column(db.Float, default=0)
    quantity = db.Column(db.Float, default=0)
    unit_of_measure = db.Column(db.String(50))
    percent_complete = db.Column(db.Float, default=0)
    
    # Define relationship
    project = db.relationship('Project', backref=db.backref('work_items', lazy=True))

# Template with styling
def get_base_template(title, content):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Magellan EV Tracker - {title}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f3f3f3;
            }}
            .header {{
                background-color: #0078D4;
                color: white;
                padding: 15px;
                text-align: center;
            }}
            .container {{
                padding: 20px;
            }}
            .nav {{
                background-color: #f8f8f8;
                padding: 10px;
                border-bottom: 1px solid #ddd;
            }}
            .nav a {{
                margin-right: 15px;
                text-decoration: none;
                color: #0078D4;
            }}
            .dashboard-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }}
            .card {{
                background: white;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                padding: 15px;
            }}
            .card h3 {{
                margin-top: 0;
                color: #0078D4;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Magellan EV Tracker</h1>
        </div>
        <div class="nav">
            <a href="/">Dashboard</a>
            <a href="/projects">Projects</a>
            <a href="/reports">Reports</a>
        </div>
        <div class="container">
            {content}
        </div>
    </body>
    </html>
    """

@main_bp.route('/')
def index():
    try:
        content = """
        <h2>Welcome to Magellan EV Tracker</h2>
        <p>Track your Earned Value with our PowerBI-inspired interface.</p>
        
        <div class="dashboard-grid">
            <div class="card">
                <h3>Projects Overview</h3>
                <p>View and manage your active projects.</p>
            </div>
            <div class="card">
                <h3>Rules of Credit</h3>
                <p>Manage different sets of Rules of Credit.</p>
            </div>
            <div class="card">
                <h3>Reports</h3>
                <p>Generate Excel and PDF reports.</p>
            </div>
        </div>
        """
        return render_template_string(get_base_template("Dashboard", content))
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

@main_bp.route('/projects')
def projects():
    try:
        # Get all projects from the database
        all_projects = Project.query.all()
        
        # Generate HTML for projects
        projects_html = ""
        if all_projects:
            for project in all_projects:
                projects_html += f"""
                <div class="card">
                    <h3>{project.name}</h3>
                    <p>{project.description}</p>
                </div>
                """
        else:
            projects_html = """
            <div class="card">
                <h3>No Projects</h3>
                <p>No projects available yet. Add your first project to get started.</p>
            </div>
            """
        
        content = f"""
        <h2>Projects</h2>
        <p>View and manage your projects.</p>
        
        {projects_html}
        """
        return render_template_string(get_base_template("Projects", content))
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

@main_bp.route('/reports')
def reports():
    try:
        content = """
        <h2>Reports</h2>
        <p>Generate and view reports.</p>
        
        <div class="card">
            <h3>Available Reports</h3>
            <p>No reports available yet. This feature will be implemented in the next iteration.</p>
        </div>
        """
        return render_template_string(get_base_template("Reports", content))
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

# Create the Flask app
def create_app():
    app = Flask(__name__)
    
    # Configure the SQLite database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///magellan_ev.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize the database with the app
    db.init_app(app)
    
    # Register the blueprint
    app.register_blueprint(main_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
