from flask import Flask, render_template, render_template_string, Blueprint, request, redirect, url_for
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
    
    # Add relationship to RuleCreditStep
    steps = db.relationship('RuleCreditStep', backref='rule', cascade='all, delete-orphan')
    
class RuleCreditStep(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rule_id = db.Column(db.Integer, db.ForeignKey('rule_of_credit.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    weight = db.Column(db.Float, default=0)  # Weight as percentage (0-100)
    
class WorkItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    rule_id = db.Column(db.Integer, db.ForeignKey('rule_of_credit.id'), nullable=True)
    description = db.Column(db.Text)
    manhours = db.Column(db.Float, default=0)
    quantity = db.Column(db.Float, default=0)
    unit_of_measure = db.Column(db.String(50))
    percent_complete = db.Column(db.Float, default=0)
    
    # Define relationships
    project = db.relationship('Project', backref=db.backref('work_items', lazy=True))
    rule_of_credit = db.relationship('RuleOfCredit', backref=db.backref('work_items', lazy=True))
    
class WorkItemProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    work_item_id = db.Column(db.Integer, db.ForeignKey('work_item.id'), nullable=False)
    step_id = db.Column(db.Integer, db.ForeignKey('rule_credit_step.id'), nullable=False)
    percent_complete = db.Column(db.Float, default=0)
    
    # Define relationships
    work_item = db.relationship('WorkItem', backref=db.backref('progress_items', lazy=True))
    step = db.relationship('RuleCreditStep')

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
            .form-group {{
                margin-bottom: 15px;
            }}
            .form-group label {{
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
            }}
            .form-group input, .form-group textarea, .form-group select {{
                width: 100%;
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }}
            .btn {{
                background-color: #0078D4;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 4px;
                cursor: pointer;
            }}
            .btn:hover {{
                background-color: #005a9e;
            }}
            .add-new {{
                margin-bottom: 20px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}
            table, th, td {{
                border: 1px solid #ddd;
            }}
            th, td {{
                padding: 10px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            .step-container {{
                margin-top: 20px;
                border-top: 1px solid #ddd;
                padding-top: 20px;
            }}
            .step-row {{
                display: flex;
                margin-bottom: 10px;
                align-items: center;
            }}
            .step-name {{
                flex: 3;
                padding-right: 10px;
            }}
            .step-weight {{
                flex: 1;
                padding-right: 10px;
            }}
            .step-actions {{
                flex: 1;
            }}
            .remove-step {{
                color: red;
                cursor: pointer;
            }}
            #steps-container {{
                margin-bottom: 20px;
            }}
        </style>
        <script>
            function addStep() {
                const container = document.getElementById('steps-container');
                const stepCount = container.getElementsByClassName('step-row').length;
                
                const newRow = document.createElement('div');
                newRow.className = 'step-row';
                newRow.innerHTML = `
                    <div class="step-name">
                        <input type="text" name="step_name_${stepCount}" placeholder="Step Name" required>
                    </div>
                    <div class="step-weight">
                        <input type="number" name="step_weight_${stepCount}" placeholder="Weight %" min="0" max="100" required>
                    </div>
                    <div class="step-actions">
                        <span class="remove-step" onclick="this.parentElement.parentElement.remove()">Remove</span>
                    </div>
                `;
                
                container.appendChild(newRow);
                
                // Update the step count hidden field
                document.getElementById('step_count').value = stepCount + 1;
            }
        </script>
    </head>
    <body>
        <div class="header">
            <h1>Magellan EV Tracker</h1>
        </div>
        <div class="nav">
            <a href="/">Dashboard</a>
            <a href="/projects">Projects</a>
            <a href="/rules">Rules of Credit</a>
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
                <a href="/projects" class="btn">View Projects</a>
            </div>
            <div class="card">
                <h3>Rules of Credit</h3>
                <p>Manage different sets of Rules of Credit.</p>
                <a href="/rules" class="btn">View Rules</a>
            </div>
            <div class="card">
                <h3>Reports</h3>
                <p>Generate Excel and PDF reports.</p>
                <a href="/reports" class="btn">View Reports</a>
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
                    <a href="/project/{project.id}" class="btn">View Details</a>
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
        
        <div class="add-new">
            <a href="/add_project" class="btn">Add New Project</a>
        </div>
        
        <div class="dashboard-grid">
            {projects_html}
        </div>
        """
        return render_template_string(get_base_template("Projects", content))
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

@main_bp.route('/add_project', methods=['GET', 'POST'])
def add_project():
    try:
        if request.method == 'POST':
            # Get form data
            name = request.form.get('name')
            description = request.form.get('description')
            
            # Create new project
            new_project = Project(name=name, description=description)
            
            # Add to database
            db.session.add(new_project)
            db.session.commit()
            
            # Redirect to projects page
            return redirect(url_for('main.projects'))
        
        # If GET request, show the form
        content = """
        <h2>Add New Project</h2>
        <p>Enter the details for your new project.</p>
        
        <div class="card">
            <form method="POST">
                <div class="form-group">
                    <label for="name">Project Name</label>
                    <input type="text" id="name" name="name" required>
                </div>
                <div class="form-group">
                    <label for="description">Description</label>
                    <textarea id="description" name="description" rows="4"></textarea>
                </div>
                <button type="submit" class="btn">Create Project</button>
            </form>
        </div>
        """
        return render_template_string(get_base_template("Add Project", content))
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

@main_bp.route('/project/<int:project_id>')
def view_project(project_id):
    try:
        # Get project by ID
        project = Project.query.get_or_404(project_id)
        
        # Get work items for this project
        work_items = WorkItem.query.filter_by(project_id=project_id).all()
        
        # Generate HTML for work items
        work_items_html = ""
        if work_items:
            for item in work_items:
                rule_name = item.rule_of_credit.name if item.rule_of_credit else "No Rule of Credit"
                work_items_html += f"""
                <div class="card">
                    <h3>Work Item</h3>
                    <p>{item.description}</p>
                    <p>Manhours: {item.manhours}</p>
                    <p>Quantity: {item.quantity} {item.unit_of_measure}</p>
                    <p>Rule of Credit: {rule_name}</p>
                    <p>Percent Complete: {item.percent_complete}%</p>
                    <a href="/work_item/{item.id}" class="btn">View Details</a>
                </div>
                """
        else:
            work_items_html = """
            <div class="card">
                <h3>No Work Items</h3>
                <p>No work items available for this project yet.</p>
            </div>
            """
        
        content = f"""
        <h2>{project.name}</h2>
        <p>{project.description}</p>
        
        <div class="add-new">
            <a href="/add_work_item/{project_id}" class="btn">Add Work Item</a>
        </div>
        
        <h3>Work Items</h3>
        <div class="dashboard-grid">
            {work_items_html}
        </div>
        """
        return render_template_string(get_base_template(f"Project: {project.name}", content))
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

@main_bp.route('/rules')
def rules():
    try:
        # Get all rules of credit from the database
        all_rules = RuleOfCredit.query.all()
        
        # Generate HTML for rules
        rules_html = ""
        if all_rules:
            for rule in all_rules:
                # Count steps for this rule
                step_count = len(rule.steps)
                rules_html += f"""
                <div class="card">
                    <h3>{rule.name}</h3>
                    <p>{rule.description}</p>
                    <p>Steps: {step_count}</p>
                    <a href="/rule/{rule.id}" class="btn">View Details</a>
                </div>
                """
        else:
            rules_html = """
            <div class="card">
                <h3>No Rules of Credit</h3>
                <p>No rules of credit available yet. Add your first rule to get started.</p>
            </div>
            """
        
        content = f"""
        <h2>Rules of Credit</h2>
        <p>Manage different sets of Rules of Credit.</p>
        
        <div class="add-new">
            <a href="/add_rule" class="btn">Add New Rule</a>
        </div>
        
        <div class="dashboard-grid">
            {rules_html}
        </div>
        """
        return render_template_string(get_base_template("Rules of Credit", content))
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

@main_bp.route('/add_rule', methods=['GET', 'POST'])
def add_rule():
    try:
        if request.method == 'POST':
            # Get form data
            name = request.form.get('name')
            description = request.form.get('description')
            step_count = int(request.form.get('step_count', 0))
            
            # Create new rule
            new_rule = RuleOfCredit(name=name, description=description)
            db.session.add(new_rule)
            db.session.flush()  # Get the ID without committing
            
            # Add steps
            total_weight = 0
            for i in range(step_count):
                step_name = request.form.get(f'step_name_{i}')
                step_weight = float(request.form.get(f'step_weight_{i}', 0))
                
                if step_name and step_weight > 0:
                    new_step = RuleCreditStep(
                        rule_id=new_rule.id,
                        name=step_name,
                        weight=step_weight
                    )
                    db.session.add(new_step)
                    total_weight += step_weight
            
            # Validate total weight is 100%
            if total_weight != 100:
                return "Error: The total weight of all steps must equal 100%", 400
            
            # Commit to database
            db.session.commit()
            
            # Redirect to rules page
            return redirect(url_for('main.rules'))
        
        # If GET request, show the form
        content = """
        <h2>Add New Rule of Credit</h2>
        <p>Enter the details for your new rule of credit.</p>
        
        <div class="card">
            <form method="POST">
                <div class="form-group">
                    <label for="name">Rule Name</label>
                    <input type="text" id="name" name="name" required>
                </div>
                <div class="form-group">
                    <label for="description">Description</label>
                    <textarea id="description" name="description" rows="4"></textarea>
                </div>
                
                <h3>Steps</h3>
                <p>Add steps for this rule of credit. The total weight must equal 100%.</p>
                
                <div id="steps-container">
                    <!-- Steps will be added here -->
                </div>
                
                <input type="hidden" id="step_count" name="step_count" value="0">
                
                <button type="button" class="btn" onclick="addStep()" style="margin-bottom: 20px;">Add Step</button>
                
                <button type="submit" class="btn">Create Rule of Credit</button>
            </form>
        </div>
        """
        return render_template_string(get_base_template("Add Rule of Credit", content))
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

@main_bp.route('/rule/<int:rule_id>')
def view_rule(rule_id):
    try:
        # Get rule by ID
        rule = RuleOfCredit.query.get_or_404(rule_id)
        
        # Get steps for this rule
        steps = RuleCreditStep.query.filter_by(rule_id=rule_id).all()
        
        # Generate HTML for steps
        steps_html = ""
        if steps:
            steps_html = """
            <table>
                <thead>
                    <tr>
                        <th>Step Name</th>
                        <th>Weight (%)</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for step in steps:
                steps_html += f"""
                <tr>
                    <td>{step.name}</td>
                    <td>{step.weight}%</td>
                </tr>
                """
            
            steps_html += """
                </tbody>
            </table>
            """
        else:
            steps_html = "<p>No steps defined for this rule of credit.</p>"
        
        content = f"""
        <h2>{rule.name}</h2>
        <p>{rule.description}</p>
        
        <h3>Steps</h3>
        {steps_html}
        
        <div class="add-new">
            <a href="/edit_rule/{rule_id}" class="btn">Edit Rule</a>
        </div>
        """
        return render_template_string(get_base_template(f"Rule: {rule.name}", content))
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
    app.config['SECRET_KEY'] = 'your-secret-key'  # Required for forms
    
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
