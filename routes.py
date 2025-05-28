from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from models import db, Project, SubJob, RuleOfCredit, CostCode, WorkItem, DISCIPLINE_CHOICES
import json
import uuid
import traceback
import os
import datetime
import io

# Create a blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page route"""
    try:
        projects = Project.query.all()
        work_items = WorkItem.query.order_by(WorkItem.id.desc()).limit(10).all()
        return render_template('index.html', projects=projects, work_items=work_items)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('index.html', projects=[], work_items=[])

@main_bp.route('/settings')
def settings():
    """Settings page route"""
    return render_template('settings.html')

@main_bp.route('/save_dashboard_settings', methods=['POST'])
def save_dashboard_settings():
    """Save dashboard settings"""
    try:
        # In a real implementation, this would save settings to the database
        # For now, we'll just return success
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ===== PROJECT ROUTES =====

@main_bp.route('/projects')
def projects():
    """List all projects"""
    try:
        all_projects = Project.query.all()
        
        # Create a list to hold projects with their calculated values
        projects_with_data = []
        
        # Calculate project-level totals for each project
        for project in all_projects:
            # Get all work items for this project
            work_items = WorkItem.query.filter_by(project_id=project.id).all()
            
            # Calculate totals using local variables instead of setting properties directly
            total_budgeted_hours = sum(item.budgeted_man_hours or 0 for item in work_items)
            total_earned_hours = sum(item.earned_man_hours or 0 for item in work_items)
            total_budgeted_quantity = sum(item.budgeted_quantity or 0 for item in work_items)
            total_earned_quantity = sum(item.earned_quantity or 0 for item in work_items)
            
            # Calculate overall progress percentage
            overall_progress = 0
            if total_budgeted_hours > 0:
                overall_progress = (total_earned_hours / total_budgeted_hours) * 100
            
            # Create a dictionary with project and its calculated values
            project_data = {
                'project': project,
                'total_budgeted_hours': total_budgeted_hours,
                'total_earned_hours': total_earned_hours,
                'total_budgeted_quantity': total_budgeted_quantity,
                'total_earned_quantity': total_earned_quantity,
                'overall_progress': overall_progress
            }
            
            projects_with_data.append(project_data)
                
        return render_template('projects.html', projects_with_data=projects_with_data)
    except Exception as e:
        flash(f'Error loading projects: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('projects.html', projects_with_data=[])

@main_bp.route('/add_project', methods=['GET', 'POST'])
def add_project():
    """Add a new project"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        project_id_str = request.form.get('project_id_str') or f"PRJ-{uuid.uuid4().hex[:8].upper()}"
        
        new_project = Project(
            name=name, 
            description=description,
            project_id_str=project_id_str
        )
        db.session.add(new_project)
        db.session.commit()
        
        flash('Project added successfully!', 'success')
        return redirect(url_for('main.projects'))
    
    return render_template('add_project.html')

@main_bp.route('/project/<int:project_id>')
def view_project(project_id):
    """View a specific project"""
    try:
        project = Project.query.get_or_404(project_id)
        sub_jobs = SubJob.query.filter_by(project_id=project_id).all()
        
        # Calculate project-level totals
        total_budgeted_hours = 0
        total_earned_hours = 0
        total_budgeted_quantity = 0
        total_earned_quantity = 0
        
        # Get all work items for this project
        work_items = WorkItem.query.filter_by(project_id=project_id).all()
        
        # Sum up the values
        for item in work_items:
            total_budgeted_hours += item.budgeted_man_hours or 0
            total_earned_hours += item.earned_man_hours or 0
            total_budgeted_quantity += item.budgeted_quantity or 0
            total_earned_quantity += item.earned_quantity or 0
        
        # Calculate overall progress percentage
        overall_progress = 0
        if total_budgeted_hours > 0:
            overall_progress = (total_earned_hours / total_budgeted_hours) * 100
        
        return render_template('view_project.html', 
                              project=project, 
                              sub_jobs=sub_jobs,
                              total_budgeted_hours=total_budgeted_hours,
                              total_earned_hours=total_earned_hours,
                              total_budgeted_quantity=total_budgeted_quantity,
                              total_earned_quantity=total_earned_quantity,
                              overall_progress=overall_progress)
    except Exception as e:
        flash(f'Error loading project: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.projects'))

@main_bp.route('/edit_project/<int:project_id>', methods=['GET', 'POST'])
def edit_project(project_id):
    """Edit an existing project"""
    project = Project.query.get_or_404(project_id)
    
    if request.method == 'POST':
        project.name = request.form.get('name')
        project.description = request.form.get('description')
        project.project_id_str = request.form.get('project_id_str')
        
        db.session.commit()
        flash('Project updated successfully!', 'success')
        return redirect(url_for('main.view_project', project_id=project.id))
    
    return render_template('edit_project.html', project=project)

@main_bp.route('/delete_project/<int:project_id>', methods=['POST'])
def delete_project(project_id):
    """Delete a project"""
    project = Project.query.get_or_404(project_id)
    
    # Check if project has sub jobs
    sub_jobs = SubJob.query.filter_by(project_id=project_id).all()
    if sub_jobs:
        flash('Cannot delete project as it has sub jobs. Delete the sub jobs first.', 'danger')
        return redirect(url_for('main.projects'))
    
    db.session.delete(project)
    db.session.commit()
    
    flash('Project deleted successfully!', 'success')
    return redirect(url_for('main.projects'))

# ===== SUB JOB ROUTES =====

@main_bp.route('/add_sub_job/<int:project_id>', methods=['GET', 'POST'])
def add_sub_job(project_id):
    """Add a new sub job to a project"""
    project = Project.query.get_or_404(project_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        area = request.form.get('area')
        sub_job_id_str = request.form.get('sub_job_id_str') or f"SJ-{uuid.uuid4().hex[:8].upper()}"
        
        new_sub_job = SubJob(
            name=name,
            description=description,
            area=area,
            sub_job_id_str=sub_job_id_str,
            project_id=project_id
        )
        db.session.add(new_sub_job)
        db.session.commit()
        
        flash('Sub Job added successfully!', 'success')
        return redirect(url_for('main.view_project', project_id=project_id))
    
    return render_template('add_sub_job.html', project=project)

@main_bp.route('/sub_job/<int:sub_job_id>')
def view_sub_job(sub_job_id):
    """View a specific sub job"""
    try:
        sub_job = SubJob.query.get_or_404(sub_job_id)
        work_items = WorkItem.query.filter_by(sub_job_id=sub_job_id).all()
        
        # Calculate total budgeted hours
        total_budgeted_hours = sum(wi.budgeted_man_hours for wi in work_items if wi.budgeted_man_hours)
        total_earned_hours = sum(wi.earned_man_hours for wi in work_items if wi.earned_man_hours)
        
        # Calculate total budgeted quantity and earned quantity
        total_budgeted_quantity = sum(wi.budgeted_quantity for wi in work_items if wi.budgeted_quantity)
        total_earned_quantity = sum(wi.earned_quantity for wi in work_items if wi.earned_quantity)
        
        # Calculate overall progress
        overall_progress = 0
        if total_budgeted_hours > 0:
            overall_progress = (total_earned_hours / total_budgeted_hours) * 100
        
        return render_template('view_sub_job.html', 
                              sub_job=sub_job, 
                              work_items=work_items,
                              total_budgeted_hours=total_budgeted_hours,
                              total_earned_hours=total_earned_hours,
                              total_budgeted_quantity=total_budgeted_quantity,
                              total_earned_quantity=total_earned_quantity,
                              overall_progress=overall_progress)
    except Exception as e:
        flash(f'Error loading sub job: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.index'))

@main_bp.route('/edit_sub_job/<int:sub_job_id>', methods=['GET', 'POST'])
def edit_sub_job(sub_job_id):
    """Edit an existing sub job"""
    sub_job = SubJob.query.get_or_404(sub_job_id)
    
    if request.method == 'POST':
        sub_job.name = request.form.get('name')
        sub_job.description = request.form.get('description')
        sub_job.area = request.form.get('area')
        sub_job.sub_job_id_str = request.form.get('sub_job_id_str')
        
        db.session.commit()
        flash('Sub Job updated successfully!', 'success')
        return redirect(url_for('main.view_sub_job', sub_job_id=sub_job.id))
    
    return render_template('edit_sub_job.html', sub_job=sub_job)

@main_bp.route('/delete_sub_job/<int:sub_job_id>', methods=['POST'])
def delete_sub_job(sub_job_id):
    """Delete a sub job"""
    sub_job = SubJob.query.get_or_404(sub_job_id)
    project_id = sub_job.project_id
    
    # Check if sub job has work items
    work_items = WorkItem.query.filter_by(sub_job_id=sub_job_id).all()
    if work_items:
        flash('Cannot delete sub job as it has work items. Delete the work items first.', 'danger')
        return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))
    
    db.session.delete(sub_job)
    db.session.commit()
    
    flash('Sub Job deleted successfully!', 'success')
    return redirect(url_for('main.view_project', project_id=project_id))

# ===== RULES OF CREDIT ROUTES =====

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
    
    # Check if rule is being used by any cost codes
    cost_codes = CostCode.query.filter_by(rule_of_credit_id=rule_id).all()
    if cost_codes:
        flash('Cannot delete rule of credit as it is being used by cost codes.', 'danger')
        return redirect(url_for('main.list_rules_of_credit'))
    
    db.session.delete(rule)
    db.session.commit()
    
    flash('Rule of Credit deleted successfully!', 'success')
    return redirect(url_for('main.list_rules_of_credit'))

# ===== COST CODE ROUTES =====

@main_bp.route('/cost_codes')
def list_cost_codes():
    """List all cost codes"""
    try:
        all_cost_codes = CostCode.query.all()
        projects = Project.query.all()
        disciplines = DISCIPLINE_CHOICES
        return render_template('list_cost_codes.html', 
                              cost_codes=all_cost_codes, 
                              projects=projects, 
                              disciplines=disciplines)
    except Exception as e:
        flash(f'Error loading cost codes: {str(e)}', 'danger')
        return redirect(url_for('main.index'))
