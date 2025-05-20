from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import db, Project, RuleOfCredit, CostCode, WorkItem
import json

# Create a blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page route"""
    return render_template('index.html')

@main_bp.route('/projects')
def projects():
    """List all projects"""
    all_projects = Project.query.all()
    return render_template('projects.html', projects=all_projects)

@main_bp.route('/add_project', methods=['GET', 'POST'])
def add_project():
    """Add a new project"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        new_project = Project(name=name, description=description)
        db.session.add(new_project)
        db.session.commit()
        
        flash('Project added successfully!', 'success')
        return redirect(url_for('main.projects'))
    
    return render_template('add_project.html')

@main_bp.route('/project/<int:project_id>')
def view_project(project_id):
    """View a specific project"""
    project = Project.query.get_or_404(project_id)
    work_items = WorkItem.query.filter_by(project_id=project_id).all()
    return render_template('view_project.html', project=project, work_items=work_items)

@main_bp.route('/list_rules_of_credit')
def list_rules_of_credit():
    """List all rules of credit"""
    all_rules = RuleOfCredit.query.all()
    return render_template('list_rules_of_credit.html', rules=all_rules)

@main_bp.route('/add_rule_of_credit', methods=['GET', 'POST'])
def add_rule_of_credit():
    """Add a new rule of credit with steps"""
    if request.method == 'POST':
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
            flash("Error: The total weight of all steps must equal 100%", "danger")
            return render_template('add_rule_of_credit.html')
        
        # Create new rule
        new_rule = RuleOfCredit(
            name=name,
            description=description
        )
        new_rule.set_steps(steps)
        
        # Add to database
        db.session.add(new_rule)
        db.session.commit()
        
        flash('Rule of Credit added successfully!', 'success')
        # Redirect to rules page
        return redirect(url_for('main.list_rules_of_credit'))
    
    return render_template('add_rule_of_credit.html')

@main_bp.route('/edit_rule_of_credit/<int:rule_id>', methods=['GET', 'POST'])
def edit_rule_of_credit(rule_id):
    """Edit an existing rule of credit"""
    rule = RuleOfCredit.query.get_or_404(rule_id)
    
    if request.method == 'POST':
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
            flash("Error: The total weight of all steps must equal 100%", "danger")
            return render_template('edit_rule_of_credit.html', rule=rule)
        
        # Update rule
        rule.name = name
        rule.description = description
        rule.set_steps(steps)
        
        db.session.commit()
        
        flash('Rule of Credit updated successfully!', 'success')
        return redirect(url_for('main.list_rules_of_credit'))
    
    return render_template('edit_rule_of_credit.html', rule=rule)

@main_bp.route('/delete_rule_of_credit/<int:rule_id>', methods=['POST'])
def delete_rule_of_credit(rule_id):
    """Delete a rule of credit"""
    rule = RuleOfCredit.query.get_or_404(rule_id)
    
    # Check if rule is being used by any work items
    work_items = WorkItem.query.filter_by(rule_of_credit_id=rule_id).all()
    if work_items:
        flash('Cannot delete rule of credit as it is being used by work items.', 'danger')
        return redirect(url_for('main.list_rules_of_credit'))
    
    db.session.delete(rule)
    db.session.commit()
    
    flash('Rule of Credit deleted successfully!', 'success')
    return redirect(url_for('main.list_rules_of_credit'))

@main_bp.route('/list_cost_codes')
def list_cost_codes():
    """List all cost codes"""
    all_cost_codes = CostCode.query.all()
    return render_template('list_cost_codes.html', cost_codes=all_cost_codes)

@main_bp.route('/add_cost_code', methods=['GET', 'POST'])
def add_cost_code():
    """Add a new cost code"""
    if request.method == 'POST':
        code = request.form.get('code')
        description = request.form.get('description')
        
        # Check if code already exists
        existing_code = CostCode.query.filter_by(code=code).first()
        if existing_code:
            flash('Cost code already exists!', 'danger')
            return render_template('add_cost_code.html')
        
        new_cost_code = CostCode(code=code, description=description)
        db.session.add(new_cost_code)
        db.session.commit()
        
        flash('Cost code added successfully!', 'success')
        return redirect(url_for('main.list_cost_codes'))
    
    return render_template('add_cost_code.html')

@main_bp.route('/reports_index')
def reports_index():
    """Reports index page"""
    return render_template('reports_index.html')

@main_bp.route('/reports')
def reports():
    """Generate reports"""
    return render_template('reports.html')
