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

@main_bp.route('/add_cost_code', methods=['GET', 'POST'])
def add_cost_code():
    """Add a new cost code"""
    try:
        if request.method == 'POST':
            try:
                code = request.form.get('code')
                description = request.form.get('description')
                discipline = request.form.get('discipline')
                project_id = request.form.get('project_id')
                rule_of_credit_id = request.form.get('rule_of_credit_id') or None
                
                # Check if code already exists
                existing_code = CostCode.query.filter_by(cost_code_id_str=code).first()
                if existing_code:
                    flash('Cost code already exists!', 'danger')
                    return redirect(url_for('main.list_cost_codes'))
                
                # Create new cost code
                new_cost_code = CostCode(
                    cost_code_id_str=code,
                    description=description,
                    discipline=discipline,
                    project_id=project_id,
                    rule_of_credit_id=rule_of_credit_id
                )
                
                db.session.add(new_cost_code)
                db.session.commit()
                
                flash('Cost code added successfully!', 'success')
                return redirect(url_for('main.list_cost_codes'))
            except Exception as e:
                flash(f'Error adding cost code: {str(e)}', 'danger')
                traceback.print_exc()
                return redirect(url_for('main.list_cost_codes'))
        
        # GET request
        projects = Project.query.all()
        rules = RuleOfCredit.query.all()
        disciplines = DISCIPLINE_CHOICES
        
        return render_template('add_cost_code.html', 
                              projects=projects, 
                              rules=rules, 
                              disciplines=disciplines)
    except Exception as e:
        flash(f'Error loading add cost code form: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_cost_codes'))

@main_bp.route('/edit_cost_code/<int:cost_code_id>', methods=['GET', 'POST'])
def edit_cost_code(cost_code_id):
    """Edit an existing cost code"""
    try:
        cost_code = CostCode.query.get_or_404(cost_code_id)
        
        if request.method == 'POST':
            try:
                cost_code.cost_code_id_str = request.form.get('code')
                cost_code.description = request.form.get('description')
                cost_code.discipline = request.form.get('discipline')
                cost_code.project_id = request.form.get('project_id')
                cost_code.rule_of_credit_id = request.form.get('rule_of_credit_id') or None
                
                db.session.commit()
                
                flash('Cost code updated successfully!', 'success')
                return redirect(url_for('main.list_cost_codes'))
            except Exception as e:
                flash(f'Error updating cost code: {str(e)}', 'danger')
                traceback.print_exc()
                return redirect(url_for('main.list_cost_codes'))
        
        # GET request
        projects = Project.query.all()
        rules = RuleOfCredit.query.all()
        disciplines = DISCIPLINE_CHOICES
        
        return render_template('edit_cost_code.html', 
                              cost_code=cost_code,
                              projects=projects, 
                              rules=rules, 
                              disciplines=disciplines)
    except Exception as e:
        flash(f'Error loading edit cost code form: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_cost_codes'))

@main_bp.route('/delete_cost_code/<int:cost_code_id>', methods=['POST'])
def delete_cost_code(cost_code_id):
    """Delete a cost code"""
    try:
        cost_code = CostCode.query.get_or_404(cost_code_id)
        
        # Check if cost code is being used by any work items
        work_items = WorkItem.query.filter_by(cost_code_id=cost_code_id).all()
        if work_items:
            flash('Cannot delete cost code as it is being used by work items.', 'danger')
            return redirect(url_for('main.list_cost_codes'))
        
        db.session.delete(cost_code)
        db.session.commit()
        
        flash('Cost code deleted successfully!', 'success')
        return redirect(url_for('main.list_cost_codes'))
    except Exception as e:
        flash(f'Error deleting cost code: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_cost_codes'))

# ===== WORK ITEM ROUTES =====

@main_bp.route('/work_items')
def list_work_items():
    """List all work items"""
    try:
        # Get filter parameters
        project_id = request.args.get('project_id')
        sub_job_id = request.args.get('sub_job_id')
        cost_code_id = request.args.get('cost_code_id')
        
        # Base query
        query = WorkItem.query
        
        # Apply filters
        if project_id:
            query = query.filter_by(project_id=project_id)
        if sub_job_id:
            query = query.filter_by(sub_job_id=sub_job_id)
        if cost_code_id:
            query = query.filter_by(cost_code_id=cost_code_id)
        
        # Get all work items with filters applied
        work_items = query.all()
        
        # Get projects, sub jobs, and cost codes for filter dropdowns
        projects = Project.query.all()
        sub_jobs = SubJob.query.all() if not project_id else SubJob.query.filter_by(project_id=project_id).all()
        cost_codes = CostCode.query.all()
        
        return render_template('work_items.html', 
                              work_items=work_items,
                              projects=projects,
                              sub_jobs=sub_jobs,
                              cost_codes=cost_codes,
                              selected_project_id=project_id,
                              selected_sub_job_id=sub_job_id,
                              selected_cost_code_id=cost_code_id)
    except Exception as e:
        flash(f'Error loading work items: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('work_items.html', 
                              work_items=[],
                              projects=[],
                              sub_jobs=[],
                              cost_codes=[])

@main_bp.route('/add_work_item', methods=['GET', 'POST'])
def add_work_item():
    """Add a new work item"""
    try:
        if request.method == 'POST':
            try:
                # Get form data
                project_id = request.form.get('project_id')
                sub_job_id = request.form.get('sub_job_id')
                cost_code_id = request.form.get('cost_code_id')
                work_item_id_str = request.form.get('work_item_id_str') or f"WI-{uuid.uuid4().hex[:8].upper()}"
                description = request.form.get('description')
                unit_of_measure = request.form.get('unit_of_measure')
                budgeted_quantity = request.form.get('budgeted_quantity')
                budgeted_man_hours = request.form.get('budgeted_man_hours')
                
                # Convert to appropriate types
                budgeted_quantity = float(budgeted_quantity) if budgeted_quantity else None
                budgeted_man_hours = float(budgeted_man_hours) if budgeted_man_hours else None
                
                # Create new work item
                new_work_item = WorkItem(
                    project_id=project_id,
                    sub_job_id=sub_job_id,
                    cost_code_id=cost_code_id,
                    work_item_id_str=work_item_id_str,
                    description=description,
                    unit_of_measure=unit_of_measure,
                    budgeted_quantity=budgeted_quantity,
                    budgeted_man_hours=budgeted_man_hours
                )
                
                db.session.add(new_work_item)
                db.session.commit()
                
                flash('Work item added successfully!', 'success')
                
                # Redirect based on context
                if sub_job_id:
                    return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))
                elif project_id:
                    return redirect(url_for('main.view_project', project_id=project_id))
                else:
                    return redirect(url_for('main.list_work_items'))
            except Exception as e:
                flash(f'Error adding work item: {str(e)}', 'danger')
                traceback.print_exc()
                return redirect(url_for('main.list_work_items'))
        
        # GET request
        # Get context parameters
        project_id = request.args.get('project_id')
        sub_job_id = request.args.get('sub_job_id')
        
        # Get projects
        projects = Project.query.all()
        
        # Get sub jobs based on project_id if provided
        if project_id:
            sub_jobs = SubJob.query.filter_by(project_id=project_id).all()
            project = Project.query.get(project_id)
        else:
            sub_jobs = []
            project = None
        
        # Get sub job if sub_job_id is provided
        sub_job = SubJob.query.get(sub_job_id) if sub_job_id else None
        
        # Get cost codes
        cost_codes = CostCode.query.all()
        
        return render_template('add_work_item.html',
                              projects=projects,
                              sub_jobs=sub_jobs,
                              cost_codes=cost_codes,
                              selected_project=project,
                              selected_sub_job=sub_job)
    except Exception as e:
        flash(f'Error loading add work item form: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_work_items'))

@main_bp.route('/view_work_item/<int:work_item_id>')
def view_work_item(work_item_id):
    """View a specific work item"""
    try:
        work_item = WorkItem.query.get_or_404(work_item_id)
        
        # Get progress data
        progress_data = work_item.get_steps_progress()
        
        # Get rule of credit steps if available
        steps = []
        if work_item.cost_code and work_item.cost_code.rule_of_credit:
            steps = work_item.cost_code.rule_of_credit.get_steps()
        
        return render_template('view_work_item.html', 
                              work_item=work_item,
                              progress_data=progress_data,
                              steps=steps)
    except Exception as e:
        flash(f'Error loading work item: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_work_items'))

@main_bp.route('/edit_work_item/<int:work_item_id>', methods=['GET', 'POST'])
def edit_work_item(work_item_id):
    """Edit an existing work item"""
    try:
        work_item = WorkItem.query.get_or_404(work_item_id)
        
        if request.method == 'POST':
            try:
                # Get form data
                work_item.project_id = request.form.get('project_id')
                work_item.sub_job_id = request.form.get('sub_job_id')
                work_item.cost_code_id = request.form.get('cost_code_id')
                work_item.work_item_id_str = request.form.get('work_item_id_str')
                work_item.description = request.form.get('description')
                work_item.unit_of_measure = request.form.get('unit_of_measure')
                
                # Convert to appropriate types
                budgeted_quantity = request.form.get('budgeted_quantity')
                budgeted_man_hours = request.form.get('budgeted_man_hours')
                earned_quantity = request.form.get('earned_quantity')
                earned_man_hours = request.form.get('earned_man_hours')
                
                work_item.budgeted_quantity = float(budgeted_quantity) if budgeted_quantity else None
                work_item.budgeted_man_hours = float(budgeted_man_hours) if budgeted_man_hours else None
                work_item.earned_quantity = float(earned_quantity) if earned_quantity else None
                work_item.earned_man_hours = float(earned_man_hours) if earned_man_hours else None
                
                db.session.commit()
                
                flash('Work item updated successfully!', 'success')
                return redirect(url_for('main.view_work_item', work_item_id=work_item.id))
            except Exception as e:
                flash(f'Error updating work item: {str(e)}', 'danger')
                traceback.print_exc()
                return redirect(url_for('main.view_work_item', work_item_id=work_item.id))
        
        # GET request
        # Get projects
        projects = Project.query.all()
        
        # Get sub jobs based on project_id
        sub_jobs = SubJob.query.filter_by(project_id=work_item.project_id).all() if work_item.project_id else []
        
        # Get cost codes
        cost_codes = CostCode.query.all()
        
        return render_template('edit_work_item.html',
                              work_item=work_item,
                              projects=projects,
                              sub_jobs=sub_jobs,
                              cost_codes=cost_codes)
    except Exception as e:
        flash(f'Error loading edit work item form: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_work_items'))

@main_bp.route('/delete_work_item/<int:work_item_id>', methods=['POST'])
def delete_work_item(work_item_id):
    """Delete a work item"""
    try:
        work_item = WorkItem.query.get_or_404(work_item_id)
        
        # Store context for redirect
        project_id = work_item.project_id
        sub_job_id = work_item.sub_job_id
        
        db.session.delete(work_item)
        db.session.commit()
        
        flash('Work item deleted successfully!', 'success')
        
        # Redirect based on context
        if sub_job_id:
            return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))
        elif project_id:
            return redirect(url_for('main.view_project', project_id=project_id))
        else:
            return redirect(url_for('main.list_work_items'))
    except Exception as e:
        flash(f'Error deleting work item: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_work_items'))

@main_bp.route('/update_work_item_progress/<int:work_item_id>', methods=['GET', 'POST'])
def update_work_item_progress(work_item_id):
    """Update progress for a work item"""
    try:
        work_item = WorkItem.query.get_or_404(work_item_id)
        
        # Check if cost code has rule of credit
        if not work_item.cost_code or not work_item.cost_code.rule_of_credit:
            flash('No rule of credit steps defined for this work item\'s cost code.', 'danger')
            return redirect(url_for('main.view_work_item', work_item_id=work_item_id))
        
        # Get rule of credit steps
        rule_steps = work_item.cost_code.rule_of_credit.get_steps()
        
        if request.method == 'POST':
            try:
                # Get progress values for each step
                progress_data = {}
                for step in rule_steps:
                    step_name = step['name']
                    progress_value = request.form.get(f'progress_{step_name}')
                    if progress_value:
                        progress_data[step_name] = float(progress_value)
                
                # Update progress data
                work_item.set_steps_progress(progress_data)
                
                # Calculate earned values based on progress
                if work_item.budgeted_quantity:
                    # Calculate weighted average progress
                    total_progress = 0
                    for step in rule_steps:
                        step_name = step['name']
                        step_weight = step['weight']
                        step_progress = progress_data.get(step_name, 0)
                        total_progress += (step_progress * step_weight / 100)
                    
                    # Update earned quantity
                    work_item.earned_quantity = work_item.budgeted_quantity * (total_progress / 100)
                
                if work_item.budgeted_man_hours:
                    # Calculate weighted average progress
                    total_progress = 0
                    for step in rule_steps:
                        step_name = step['name']
                        step_weight = step['weight']
                        step_progress = progress_data.get(step_name, 0)
                        total_progress += (step_progress * step_weight / 100)
                    
                    # Update earned man hours
                    work_item.earned_man_hours = work_item.budgeted_man_hours * (total_progress / 100)
                
                db.session.commit()
                
                flash('Work item progress updated successfully!', 'success')
                return redirect(url_for('main.view_work_item', work_item_id=work_item_id))
            except Exception as e:
                flash(f'Error updating work item progress: {str(e)}', 'danger')
                traceback.print_exc()
                return redirect(url_for('main.view_work_item', work_item_id=work_item_id))
        
        # GET request
        # Get current progress data
        progress_data = work_item.get_steps_progress()
        
        return render_template('update_work_item_progress.html',
                              work_item=work_item,
                              rule_steps=rule_steps,
                              progress_data=progress_data)
    except Exception as e:
        flash(f'Error loading update progress form: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.view_work_item', work_item_id=work_item_id))

# ===== API ROUTES =====

@main_bp.route('/api/get_sub_jobs/<int:project_id>')
def get_sub_jobs(project_id):
    """API to get sub jobs for a project"""
    try:
        sub_jobs = SubJob.query.filter_by(project_id=project_id).all()
        return jsonify([{'id': sj.id, 'name': sj.name} for sj in sub_jobs])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== REPORT ROUTES =====

@main_bp.route('/reports')
def reports_index():
    """Reports index page"""
    try:
        projects = Project.query.all()
        return render_template('reports_index.html', projects=projects)
    except Exception as e:
        flash(f'Error loading reports page: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.index'))

@main_bp.route('/export/quantities/pdf/<int:project_id>')
@main_bp.route('/export/quantities/pdf/<int:project_id>/<int:sub_job_id>')
def export_quantities_pdf(project_id, sub_job_id=None):
    """Export quantities report as PDF"""
    try:
        from reports.pdf_export import generate_quantities_report_pdf
        
        # Generate PDF data
        if sub_job_id:
            pdf_data = generate_quantities_report_pdf(sub_job_id=sub_job_id)
            sub_job = SubJob.query.get_or_404(sub_job_id)
            filename = f"{sub_job.project.project_id_str}_{sub_job.sub_job_id_str}_quantities_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        else:
            pdf_data = generate_quantities_report_pdf(project_id=project_id)
            project = Project.query.get_or_404(project_id)
            filename = f"{project.project_id_str}_quantities_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Create a BytesIO object
        pdf_io = io.BytesIO(pdf_data)
        pdf_io.seek(0)
        
        # Return the PDF file
        return send_file(
            pdf_io,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.reports_index'))

@main_bp.route('/export/hours/pdf/<int:project_id>')
@main_bp.route('/export/hours/pdf/<int:project_id>/<int:sub_job_id>')
def export_hours_pdf(project_id, sub_job_id=None):
    """Export hours report as PDF"""
    try:
        from reports.pdf_export import generate_hours_report_pdf
        
        # Generate PDF data
        if sub_job_id:
            pdf_data = generate_hours_report_pdf(sub_job_id=sub_job_id)
            sub_job = SubJob.query.get_or_404(sub_job_id)
            filename = f"{sub_job.project.project_id_str}_{sub_job.sub_job_id_str}_hours_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        else:
            pdf_data = generate_hours_report_pdf(project_id=project_id)
            project = Project.query.get_or_404(project_id)
            filename = f"{project.project_id_str}_hours_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Create a BytesIO object
        pdf_io = io.BytesIO(pdf_data)
        pdf_io.seek(0)
        
        # Return the PDF file
        return send_file(
            pdf_io,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.reports_index'))

@main_bp.route('/export/quantities/excel/<int:project_id>')
@main_bp.route('/export/quantities/excel/<int:project_id>/<int:sub_job_id>')
def export_quantities_excel(project_id, sub_job_id=None):
    """Export quantities report as Excel"""
    # Placeholder for Excel export
    flash('Excel export not implemented yet.', 'info')
    return redirect(url_for('main.reports_index'))

@main_bp.route('/export/hours/excel/<int:project_id>')
@main_bp.route('/export/hours/excel/<int:project_id>/<int:sub_job_id>')
def export_hours_excel(project_id, sub_job_id=None):
    """Export hours report as Excel"""
    # Placeholder for Excel export
    flash('Excel export not implemented yet.', 'info')
    return redirect(url_for('main.reports_index'))
