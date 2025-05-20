from flask import Flask, render_template, render_template_string, Blueprint, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import json

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
    steps_json = db.Column(db.Text, default="[]")  # JSON string to store steps and weights
    
    def get_steps(self):
        """Return steps as a Python list of dictionaries"""
        try:
            return json.loads(self.steps_json)
        except:
            return []
    
    def set_steps(self, steps_list):
        """Set steps from a list of dictionaries with name and weight"""
        self.steps_json = json.dumps(steps_list)
    
    def add_step(self, name, weight):
        """Add a single step with name and weight"""
        steps = self.get_steps()
        steps.append({"name": name, "weight": float(weight)})
        self.steps_json = json.dumps(steps)

class WorkItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    description = db.Column(db.Text)
    manhours = db.Column(db.Float, default=0)
    quantity = db.Column(db.Float, default=0)
    unit_of_measure = db.Column(db.String(50))
    percent_complete = db.Column(db.Float, default=0)
    rule_of_credit_id = db.Column(db.Integer, db.ForeignKey('rule_of_credit.id'), nullable=True)
    progress_json = db.Column(db.Text, default="[]")  # JSON string to store progress for each step
    
    # Define relationships
    project = db.relationship('Project', backref=db.backref('work_items', lazy=True))
    rule_of_credit = db.relationship('RuleOfCredit', backref=db.backref('work_items', lazy=True))
    
    def get_progress(self):
        """Return progress as a Python dictionary"""
        try:
            return json.loads(self.progress_json)
        except:
            return []
    
    def set_progress(self, progress_list):
        """Set progress from a list of dictionaries with step_name and percentage"""
        self.progress_json = json.dumps(progress_list)
    
    def update_step_progress(self, step_name, percentage):
        """Update progress for a specific step"""
        progress = self.get_progress()
        
        # Check if step exists in progress
        step_found = False
        for step in progress:
            if step.get("step_name") == step_name:
                step["percentage"] = float(percentage)
                step_found = True
                break
        
        # If step not found, add it
        if not step_found:
            progress.append({"step_name": step_name, "percentage": float(percentage)})
        
        self.progress_json = json.dumps(progress)
        self.calculate_percent_complete()
    
    def calculate_percent_complete(self):
        """Calculate overall percent complete based on rule of credit steps and progress"""
        if not self.rule_of_credit_id:
            return
        
        rule = RuleOfCredit.query.get(self.rule_of_credit_id)
        if not rule:
            return
        
        steps = rule.get_steps()
        progress = self.get_progress()
        
        # Create a dictionary for easier lookup
        progress_dict = {}
        for p in progress:
            progress_dict[p.get("step_name")] = p.get("percentage", 0)
        
        # Calculate weighted percentage
        total_weighted_percentage = 0
        for step in steps:
            step_name = step.get("name")
            step_weight = float(step.get("weight", 0))
            step_progress = float(progress_dict.get(step_name, 0))
            
            weighted_progress = (step_progress / 100.0) * step_weight
            total_weighted_percentage += weighted_progress
        
        self.percent_complete = total_weighted_percentage

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
            .steps-container {{
                margin-top: 15px;
                border-top: 1px solid #eee;
                padding-top: 10px;
            }}
            .step-row {{
                display: flex;
                margin-bottom: 10px;
                align-items: center;
            }}
            .step-name {{
                flex: 3;
                margin-right: 10px;
            }}
            .step-weight {{
                flex: 1;
            }}
            .step-actions {{
                flex: 0 0 40px;
                text-align: center;
            }}
            .step-item {{
                background-color: #f9f9f9;
                padding: 8px;
                border-radius: 4px;
                margin-bottom: 5px;
                display: flex;
                justify-content: space-between;
            }}
            .step-item .step-name {{
                font-weight: bold;
            }}
            .step-item .step-weight {{
                color: #0078D4;
            }}
            .error-message {{
                color: #d9534f;
                margin-top: 5px;
                font-size: 0.9em;
            }}
            .success-message {{
                color: #5cb85c;
                margin-top: 5px;
                font-size: 0.9em;
            }}
        </style>
        <script>
            function addStep() {
                const container = document.getElementById('steps-container');
                const stepCount = document.getElementById('step_count');
                const count = parseInt(stepCount.value) + 1;
                
                const stepRow = document.createElement('div');
                stepRow.className = 'step-row';
                stepRow.id = 'step_row_' + count;
                
                stepRow.innerHTML = `
                    <div class="step-name">
                        <input type="text" name="step_name[]" placeholder="Step name" required>
                    </div>
                    <div class="step-weight">
                        <input type="number" name="step_weight[]" min="0" max="100" step="0.1" placeholder="Weight %" required>
                    </div>
                    <div class="step-actions">
                        <button type="button" class="btn" style="background-color: #d9534f;" onclick="removeStep(${count})">×</button>
                    </div>
                `;
                
                container.appendChild(stepRow);
                stepCount.value = count;
                
                // Update total weight
                updateTotalWeight();
            }
            
            function removeStep(id) {
                const stepRow = document.getElementById('step_row_' + id);
                if (stepRow) {
                    stepRow.remove();
                    updateTotalWeight();
                }
            }
            
            function updateTotalWeight() {
                const weightInputs = document.querySelectorAll('input[name="step_weight[]"]');
                let total = 0;
                
                weightInputs.forEach(input => {
                    const weight = parseFloat(input.value) || 0;
                    total += weight;
                });
                
                const totalWeightElement = document.getElementById('total_weight');
                if (totalWeightElement) {
                    totalWeightElement.textContent = total.toFixed(1);
                    
                    // Update validation message
                    const validationMessage = document.getElementById('weight_validation');
                    if (validationMessage) {
                        if (Math.abs(total - 100) < 0.1) {
                            validationMessage.className = 'success-message';
                            validationMessage.textContent = 'Total weight is 100% ✓';
                        } else {
                            validationMessage.className = 'error-message';
                            validationMessage.textContent = 'Total weight must equal 100%';
                        }
                    }
                }
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
                rule_name = "No Rule of Credit"
                if item.rule_of_credit:
                    rule_name = item.rule_of_credit.name
                
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
                # Get steps for this rule
                steps = rule.get_steps()
                
                # Generate HTML for steps
                steps_html = ""
                for step in steps:
                    steps_html += f"""
                    <div class="step-item">
                        <span class="step-name">{step.get('name')}</span>
                        <span class="step-weight">{step.get('weight')}%</span>
                    </div>
                    """
                
                if not steps:
                    steps_html = "<p>No steps defined for this rule.</p>"
                
                rules_html += f"""
                <div class="card">
                    <h3>{rule.name}</h3>
                    <p>{rule.description}</p>
                    <div class="steps-container">
                        <h4>Steps:</h4>
                        {steps_html}
                    </div>
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
            
            # Get step data
            step_names = request.form.getlist('step_name[]')
            step_weights = request.form.getlist('step_weight[]')
            
            # Create steps list
            steps = []
            total_weight = 0
            
            for i in range(len(step_names)):
                if step_names[i].strip():  # Only add non-empty steps
                    weight = float(step_weights[i]) if step_weights[i] else 0
                    steps.append({
                        "name": step_names[i],
                        "weight": weight
                    })
                    total_weight += weight
            
            # Validate total weight
            if abs(total_weight - 100) > 0.1:  # Allow small rounding errors
                return "Error: The total weight of all steps must equal 100%", 400
            
            # Create new rule
            new_rule = RuleOfCredit(
                name=name,
                description=description,
                steps_json=json.dumps(steps)
            )
            
            # Add to database
            db.session.add(new_rule)
            db.session.commit()
            
            # Redirect to rules page
            return redirect(url_for('main.rules'))
        
        # If GET request, show the form
        content = """
        <h2>Add New Rule of Credit</h2>
        <p>Enter the details for your new rule of credit.</p>
        
        <div class="card">
            <form method="POST" onsubmit="return validateForm()">
                <div class="form-group">
                    <label for="name">Rule Name</label>
                    <input type="text" id="name" name="name" required>
                </div>
                <div class="form-group">
                    <label for="description">Description</label>
                    <textarea id="description" name="description" rows="4"></textarea>
                </div>
                
                <h3>Steps</h3>
                <p>Add steps for this Rule of Credit. The weights should total 100%.</p>
                
                <div id="steps-container">
                    <div class="step-row" id="step_row_1">
                        <div class="step-name">
                            <input type="text" name="step_name[]" placeholder="Step name" required>
                        </div>
                        <div class="step-weight">
                            <input type="number" name="step_weight[]" min="0" max="100" step="0.1" placeholder="Weight %" required onchange="updateTotalWeight()">
                        </div>
                        <div class="step-actions">
                            <!-- No remove button for first step -->
                        </div>
                    </div>
                </div>
                
                <div style="margin: 15px 0;">
                    <button type="button" class="btn" style="background-color: #5cb85c;" onclick="addStep()">+ Add Step</button>
                    <div style="margin-top: 10px;">
                        <strong>Total Weight: <span id="total_weight">0.0</span>%</strong>
                        <div id="weight_validation" class="error-message">Total weight must equal 100%</div>
                    </div>
                </div>
                
                <input type="hidden" id="step_count" name="step_count" value="1">
                
                <button type="submit" class="btn">Create Rule of Credit</button>
            </form>
        </div>
        
        <script>
            // Initialize total weight calculation
            document.addEventListener('DOMContentLoaded', function() {
                updateTotalWeight();
            });
            
            function validateForm() {
                const totalWeight = parseFloat(document.getElementById('total_weight').textContent);
                if (Math.abs(totalWeight - 100) > 0.1) {
                    alert('The total weight of all steps must equal 100%');
                    return false;
                }
                return true;
            }
        </script>
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
        steps = rule.get_steps()
        
        # Generate HTML for steps
        steps_html = ""
        if steps:
            steps_html = """
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                <thead>
                    <tr style="background-color: #f3f3f3;">
                        <th style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">Step Name</th>
                        <th style="padding: 8px; text-align: right; border-bottom: 1px solid #ddd;">Weight (%)</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for step in steps:
                steps_html += f"""
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;">{step.get('name')}</td>
                    <td style="padding: 8px; text-align: right; border-bottom: 1px solid #eee;">{step.get('weight')}%</td>
                </tr>
                """
            
            steps_html += """
                </tbody>
            </table>
            """
        else:
            steps_html = "<p>No steps defined for this rule of credit.</p>"
        
        # Get work items using this rule
        work_items = WorkItem.query.filter_by(rule_of_credit_id=rule_id).all()
        work_items_html = ""
        
        if work_items:
            work_items_html = """
            <h3>Work Items Using This Rule</h3>
            <ul>
            """
            
            for item in work_items:
                project = Project.query.get(item.project_id)
                project_name = project.name if project else "Unknown Project"
                
                work_items_html += f"""
                <li>
                    <a href="/work_item/{item.id}">{item.description}</a> 
                    (Project: <a href="/project/{item.project_id}">{project_name}</a>)
                </li>
                """
            
            work_items_html += "</ul>"
        
        content = f"""
        <h2>{rule.name}</h2>
        <p>{rule.description}</p>
        
        <div class="add-new">
            <a href="/edit_rule/{rule.id}" class="btn">Edit Rule</a>
        </div>
        
        <h3>Steps</h3>
        {steps_html}
        
        {work_items_html}
        """
        return render_template_string(get_base_template(f"Rule: {rule.name}", content))
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

@main_bp.route('/edit_rule/<int:rule_id>', methods=['GET', 'POST'])
def edit_rule(rule_id):
    try:
        # Get rule by ID
        rule = RuleOfCredit.query.get_or_404(rule_id)
        
        if request.method == 'POST':
            # Get form data
            name = request.form.get('name')
            description = request.form.get('description')
            
            # Get step data
            step_names = request.form.getlist('step_name[]')
            step_weights = request.form.getlist('step_weight[]')
            
            # Create steps list
            steps = []
            total_weight = 0
            
            for i in range(len(step_names)):
                if step_names[i].strip():  # Only add non-empty steps
                    weight = float(step_weights[i]) if step_weights[i] else 0
                    steps.append({
                        "name": step_names[i],
                        "weight": weight
                    })
                    total_weight += weight
            
            # Validate total weight
            if abs(total_weight - 100) > 0.1:  # Allow small rounding errors
                return "Error: The total weight of all steps must equal 100%", 400
            
            # Update rule
            rule.name = name
            rule.description = description
            rule.steps_json = json.dumps(steps)
            
            # Save to database
            db.session.commit()
            
            # Redirect to rule details page
            return redirect(url_for('main.view_rule', rule_id=rule.id))
        
        # If GET request, show the form with current data
        steps = rule.get_steps()
        steps_html = ""
        
        for i, step in enumerate(steps):
            step_id = i + 1
            remove_button = ""
            if i > 0:  # Only add remove button after first step
                remove_button = f"""
                <button type="button" class="btn" style="background-color: #d9534f;" onclick="removeStep({step_id})">×</button>
                """
            
            steps_html += f"""
            <div class="step-row" id="step_row_{step_id}">
                <div class="step-name">
                    <input type="text" name="step_name[]" value="{step.get('name')}" placeholder="Step name" required>
                </div>
                <div class="step-weight">
                    <input type="number" name="step_weight[]" min="0" max="100" step="0.1" value="{step.get('weight')}" placeholder="Weight %" required onchange="updateTotalWeight()">
                </div>
                <div class="step-actions">
                    {remove_button}
                </div>
            </div>
            """
        
        # If no steps, add one empty step
        if not steps:
            steps_html = """
            <div class="step-row" id="step_row_1">
                <div class="step-name">
                    <input type="text" name="step_name[]" placeholder="Step name" required>
                </div>
                <div class="step-weight">
                    <input type="number" name="step_weight[]" min="0" max="100" step="0.1" placeholder="Weight %" required onchange="updateTotalWeight()">
                </div>
                <div class="step-actions">
                    <!-- No remove button for first step -->
                </div>
            </div>
            """
        
        content = f"""
        <h2>Edit Rule of Credit</h2>
        <p>Update the details for this rule of credit.</p>
        
        <div class="card">
            <form method="POST" onsubmit="return validateForm()">
                <div class="form-group">
                    <label for="name">Rule Name</label>
                    <input type="text" id="name" name="name" value="{rule.name}" required>
                </div>
                <div class="form-group">
                    <label for="description">Description</label>
                    <textarea id="description" name="description" rows="4">{rule.description or ''}</textarea>
                </div>
                
                <h3>Steps</h3>
                <p>Update steps for this Rule of Credit. The weights should total 100%.</p>
                
                <div id="steps-container">
                    {steps_html}
                </div>
                
                <div style="margin: 15px 0;">
                    <button type="button" class="btn" style="background-color: #5cb85c;" onclick="addStep()">+ Add Step</button>
                    <div style="margin-top: 10px;">
                        <strong>Total Weight: <span id="total_weight">0.0</span>%</strong>
                        <div id="weight_validation" class="error-message">Total weight must equal 100%</div>
                    </div>
                </div>
                
                <input type="hidden" id="step_count" name="step_count" value="{len(steps) or 1}">
                
                <button type="submit" class="btn">Update Rule of Credit</button>
            </form>
        </div>
        
        <script>
            // Initialize total weight calculation
            document.addEventListener('DOMContentLoaded', function() {
                updateTotalWeight();
            });
            
            function validateForm() {
                const totalWeight = parseFloat(document.getElementById('total_weight').textContent);
                if (Math.abs(totalWeight - 100) > 0.1) {
                    alert('The total weight of all steps must equal 100%');
                    return false;
                }
                return true;
            }
        </script>
        """
        return render_template_string(get_base_template(f"Edit Rule: {rule.name}", content))
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

@main_bp.route('/add_work_item/<int:project_id>', methods=['GET', 'POST'])
def add_work_item(project_id):
    try:
        # Get project by ID
        project = Project.query.get_or_404(project_id)
        
        if request.method == 'POST':
            # Get form data
            description = request.form.get('description')
            manhours = float(request.form.get('manhours') or 0)
            quantity = float(request.form.get('quantity') or 0)
            unit_of_measure = request.form.get('unit_of_measure')
            rule_of_credit_id = request.form.get('rule_of_credit_id')
            
            # Convert empty string to None
            if not rule_of_credit_id:
                rule_of_credit_id = None
            
            # Create new work item
            new_work_item = WorkItem(
                project_id=project_id,
                description=description,
                manhours=manhours,
                quantity=quantity,
                unit_of_measure=unit_of_measure,
                rule_of_credit_id=rule_of_credit_id
            )
            
            # Add to database
            db.session.add(new_work_item)
            db.session.commit()
            
            # Redirect to project page
            return redirect(url_for('main.view_project', project_id=project_id))
        
        # Get all rules of credit for dropdown
        rules = RuleOfCredit.query.all()
        rules_options = ""
        
        for rule in rules:
            rules_options += f'<option value="{rule.id}">{rule.name}</option>'
        
        # If GET request, show the form
        content = f"""
        <h2>Add Work Item to {project.name}</h2>
        <p>Enter the details for your new work item.</p>
        
        <div class="card">
            <form method="POST">
                <div class="form-group">
                    <label for="description">Description</label>
                    <textarea id="description" name="description" rows="4" required></textarea>
                </div>
                <div class="form-group">
                    <label for="manhours">Budgeted Manhours</label>
                    <input type="number" id="manhours" name="manhours" min="0" step="0.1">
                </div>
                <div class="form-group">
                    <label for="quantity">Budgeted Quantity</label>
                    <input type="number" id="quantity" name="quantity" min="0" step="0.1">
                </div>
                <div class="form-group">
                    <label for="unit_of_measure">Unit of Measure</label>
                    <input type="text" id="unit_of_measure" name="unit_of_measure" placeholder="e.g., EA, LF, SF">
                </div>
                <div class="form-group">
                    <label for="rule_of_credit_id">Rule of Credit</label>
                    <select id="rule_of_credit_id" name="rule_of_credit_id">
                        <option value="">-- Select Rule of Credit --</option>
                        {rules_options}
                    </select>
                </div>
                <button type="submit" class="btn">Create Work Item</button>
            </form>
        </div>
        """
        return render_template_string(get_base_template(f"Add Work Item to {project.name}", content))
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

@main_bp.route('/work_item/<int:work_item_id>')
def view_work_item(work_item_id):
    try:
        # Get work item by ID
        work_item = WorkItem.query.get_or_404(work_item_id)
        
        # Get project
        project = Project.query.get(work_item.project_id)
        
        # Get rule of credit
        rule = None
        steps_html = ""
        
        if work_item.rule_of_credit_id:
            rule = RuleOfCredit.query.get(work_item.rule_of_credit_id)
            
            if rule:
                steps = rule.get_steps()
                progress = work_item.get_progress()
                
                # Create a dictionary for easier lookup
                progress_dict = {}
                for p in progress:
                    progress_dict[p.get("step_name")] = p.get("percentage", 0)
                
                if steps:
                    steps_html = """
                    <h3>Progress by Step</h3>
                    <form method="POST" action="/update_work_item_progress/{work_item.id}">
                        <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                            <thead>
                                <tr style="background-color: #f3f3f3;">
                                    <th style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">Step Name</th>
                                    <th style="padding: 8px; text-align: center; border-bottom: 1px solid #ddd;">Weight</th>
                                    <th style="padding: 8px; text-align: center; border-bottom: 1px solid #ddd;">Completion %</th>
                                </tr>
                            </thead>
                            <tbody>
                    """
                    
                    for step in steps:
                        step_name = step.get('name')
                        step_weight = step.get('weight')
                        step_progress = progress_dict.get(step_name, 0)
                        
                        steps_html += f"""
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #eee;">{step_name}</td>
                            <td style="padding: 8px; text-align: center; border-bottom: 1px solid #eee;">{step_weight}%</td>
                            <td style="padding: 8px; text-align: center; border-bottom: 1px solid #eee;">
                                <input type="number" name="progress_{step_name}" value="{step_progress}" min="0" max="100" step="1" style="width: 80px;">
                            </td>
                        </tr>
                        """
                    
                    steps_html += """
                            </tbody>
                        </table>
                        <button type="submit" class="btn" style="margin-top: 15px;">Update Progress</button>
                    </form>
                    """
        
        content = f"""
        <h2>Work Item Details</h2>
        
        <div class="card">
            <h3>Description</h3>
            <p>{work_item.description}</p>
            
            <h3>Project</h3>
            <p><a href="/project/{project.id}">{project.name}</a></p>
            
            <h3>Metrics</h3>
            <p>Budgeted Manhours: {work_item.manhours}</p>
            <p>Budgeted Quantity: {work_item.quantity} {work_item.unit_of_measure}</p>
            <p>Percent Complete: {work_item.percent_complete}%</p>
            
            <h3>Rule of Credit</h3>
            <p>{"<a href='/rule/" + str(rule.id) + "'>" + rule.name + "</a>" if rule else "No Rule of Credit assigned"}</p>
            
            {steps_html}
            
            <div class="add-new">
                <a href="/edit_work_item/{work_item.id}" class="btn">Edit Work Item</a>
            </div>
        </div>
        """
        return render_template_string(get_base_template("Work Item Details", content))
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

@main_bp.route('/update_work_item_progress/<int:work_item_id>', methods=['POST'])
def update_work_item_progress(work_item_id):
    try:
        # Get work item by ID
        work_item = WorkItem.query.get_or_404(work_item_id)
        
        # Get rule of credit
        if not work_item.rule_of_credit_id:
            return "Error: No Rule of Credit assigned to this Work Item", 400
        
        rule = RuleOfCredit.query.get(work_item.rule_of_credit_id)
        if not rule:
            return "Error: Rule of Credit not found", 404
        
        # Get steps
        steps = rule.get_steps()
        
        # Update progress for each step
        progress = []
        for step in steps:
            step_name = step.get('name')
            progress_key = f"progress_{step_name}"
            
            if progress_key in request.form:
                percentage = float(request.form.get(progress_key) or 0)
                progress.append({
                    "step_name": step_name,
                    "percentage": percentage
                })
        
        # Update work item progress
        work_item.set_progress(progress)
        work_item.calculate_percent_complete()
        
        # Save to database
        db.session.commit()
        
        # Redirect to work item page
        return redirect(url_for('main.view_work_item', work_item_id=work_item_id))
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

@main_bp.route('/edit_work_item/<int:work_item_id>', methods=['GET', 'POST'])
def edit_work_item(work_item_id):
    try:
        # Get work item by ID
        work_item = WorkItem.query.get_or_404(work_item_id)
        
        if request.method == 'POST':
            # Get form data
            description = request.form.get('description')
            manhours = float(request.form.get('manhours') or 0)
            quantity = float(request.form.get('quantity') or 0)
            unit_of_measure = request.form.get('unit_of_measure')
            rule_of_credit_id = request.form.get('rule_of_credit_id')
            
            # Convert empty string to None
            if not rule_of_credit_id:
                rule_of_credit_id = None
            
            # Update work item
            work_item.description = description
            work_item.manhours = manhours
            work_item.quantity = quantity
            work_item.unit_of_measure = unit_of_measure
            work_item.rule_of_credit_id = rule_of_credit_id
            
            # Save to database
            db.session.commit()
            
            # Redirect to work item page
            return redirect(url_for('main.view_work_item', work_item_id=work_item_id))
        
        # Get all rules of credit for dropdown
        rules = RuleOfCredit.query.all()
        rules_options = ""
        
        for rule in rules:
            selected = "selected" if work_item.rule_of_credit_id == rule.id else ""
            rules_options += f'<option value="{rule.id}" {selected}>{rule.name}</option>'
        
        # If GET request, show the form with current data
        content = f"""
        <h2>Edit Work Item</h2>
        <p>Update the details for this work item.</p>
        
        <div class="card">
            <form method="POST">
                <div class="form-group">
                    <label for="description">Description</label>
                    <textarea id="description" name="description" rows="4" required>{work_item.description or ''}</textarea>
                </div>
                <div class="form-group">
                    <label for="manhours">Budgeted Manhours</label>
                    <input type="number" id="manhours" name="manhours" min="0" step="0.1" value="{work_item.manhours or ''}">
                </div>
                <div class="form-group">
                    <label for="quantity">Budgeted Quantity</label>
                    <input type="number" id="quantity" name="quantity" min="0" step="0.1" value="{work_item.quantity or ''}">
                </div>
                <div class="form-group">
                    <label for="unit_of_measure">Unit of Measure</label>
                    <input type="text" id="unit_of_measure" name="unit_of_measure" value="{work_item.unit_of_measure or ''}" placeholder="e.g., EA, LF, SF">
                </div>
                <div class="form-group">
                    <label for="rule_of_credit_id">Rule of Credit</label>
                    <select id="rule_of_credit_id" name="rule_of_credit_id">
                        <option value="">-- Select Rule of Credit --</option>
                        {rules_options}
                    </select>
                </div>
                <button type="submit" class="btn">Update Work Item</button>
            </form>
        </div>
        """
        return render_template_string(get_base_template("Edit Work Item", content))
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
