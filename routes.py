from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from models import db, Project, SubJob, RuleOfCredit, CostCode, WorkItem, DISCIPLINE_CHOICES
import json
import uuid
import traceback
import os
import datetime
from reports import generate_hours_report_pdf, generate_quantities_report_pdf, generate_hours_report_excel, generate_quantities_report_excel

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
        
        # Calculate project-level totals for each project
        for project in all_projects:
            # Initialize totals
            project.total_budgeted_hours = 0
            project.total_earned_hours = 0
            project.total_budgeted_quantity = 0
            project.total_earned_quantity = 0
            
            # Get all work items for this project
            work_items = WorkItem.query.filter_by(project_id=project.id).all()
            
            # Sum up the values
            for item in work_items:
                project.total_budgeted_hours += item.budgeted_man_hours or 0
                project.total_earned_hours += item.earned_man_hours or 0
                
                # For quantity, we need to be careful about different units of measure
                # For simplicity, we're just summing them up here
                project.total_budgeted_quantity += item.budgeted_quantity or 0
                project.total_earned_quantity += item.earned_quantity or 0
            
            # Calculate overall progress percentage
            if project.total_budgeted_hours > 0:
                project.overall_progress = (project.total_earned_hours / project.total_budgeted_hours) * 100
            else:
                project.overall_progress = 0
                
        return render_template('projects.html', projects=all_projects)
    except Exception as e:
        flash(f'Error loading projects: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('projects.html', projects=[])

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
                    projects = Project.query.all()
                    rules = RuleOfCredit.query.all()
                    return render_template('add_cost_code.html', projects=projects, rules=rules, disciplines=DISCIPLINE_CHOICES)
                
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
                db.session.rollback()
                flash(f'Error adding cost code: {str(e)}', 'danger')
                traceback.print_exc()
        
        projects = Project.query.all()
        rules = RuleOfCredit.query.all()
        return render_template('add_cost_code.html', projects=projects, rules=rules, disciplines=DISCIPLINE_CHOICES)
    except Exception as e:
        flash(f'Error loading add cost code form: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

@main_bp.route('/edit_cost_code/<int:cost_code_id>', methods=['GET', 'POST'])
def edit_cost_code(cost_code_id):
    """Edit an existing cost code"""
    try:
        cost_code = CostCode.query.get_or_404(cost_code_id)
        
        if request.method == 'POST':
            try:
                code = request.form.get('code')
                description = request.form.get('description')
                discipline = request.form.get('discipline')
                project_id = request.form.get('project_id')
                rule_of_credit_id = request.form.get('rule_of_credit_id') or None
                
                # Check if code already exists and is not this one
                existing_code = CostCode.query.filter_by(cost_code_id_str=code).first()
                if existing_code and existing_code.id != cost_code_id:
                    flash('Cost code already exists!', 'danger')
                    projects = Project.query.all()
                    rules = RuleOfCredit.query.all()
                    return render_template('edit_cost_code.html', cost_code=cost_code, projects=projects, rules=rules, disciplines=DISCIPLINE_CHOICES)
                
                cost_code.cost_code_id_str = code
                cost_code.description = description
                cost_code.discipline = discipline
                cost_code.project_id = project_id
                cost_code.rule_of_credit_id = rule_of_credit_id
                
                db.session.commit()
                flash('Cost code updated successfully!', 'success')
                return redirect(url_for('main.list_cost_codes'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating cost code: {str(e)}', 'danger')
        
        projects = Project.query.all()
        rules = RuleOfCredit.query.all()
        return render_template('edit_cost_code.html', cost_code=cost_code, projects=projects, rules=rules, disciplines=DISCIPLINE_CHOICES)
    except Exception as e:
        flash(f'Error loading edit cost code form: {str(e)}', 'danger')
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
        return redirect(url_for('main.list_cost_codes'))

# ===== WORK ITEM ROUTES =====

@main_bp.route('/work_items')
def work_items():
    """List all work items with filtering options"""
    try:
        # Get filter parameters
        project_id = request.args.get('project_id', type=int)
        sub_job_id = request.args.get('sub_job_id', type=int)
        search = request.args.get('search', '')
        discipline = request.args.get('discipline', '')
        status = request.args.get('status', '')
        sort_by = request.args.get('sort_by', '')
        
        # Base query
        query = WorkItem.query
        
        # Apply filters
        if project_id:
            query = query.filter(WorkItem.project_id == project_id)
        if sub_job_id:
            query = query.filter(WorkItem.sub_job_id == sub_job_id)
        if search:
            query = query.filter(WorkItem.description.ilike(f'%{search}%') | 
                                WorkItem.work_item_id_str.ilike(f'%{search}%'))
        if discipline:
            query = query.join(CostCode).filter(CostCode.discipline == discipline)
        if status:
            if status == 'not_started':
                query = query.filter(WorkItem.percent_complete_hours == 0)
            elif status == 'in_progress':
                query = query.filter(WorkItem.percent_complete_hours > 0, 
                                    WorkItem.percent_complete_hours < 100)
            elif status == 'completed':
                query = query.filter(WorkItem.percent_complete_hours == 100)
        
        # Apply sorting
        if sort_by:
            if sort_by == 'id':
                query = query.order_by(WorkItem.work_item_id_str)
            elif sort_by == 'description':
                query = query.order_by(WorkItem.description)
            elif sort_by == 'progress':
                query = query.order_by(WorkItem.percent_complete_hours.desc())
            elif sort_by == 'cost_code':
                query = query.join(CostCode).order_by(CostCode.cost_code_id_str)
        else:
            # Default sort by ID
            query = query.order_by(WorkItem.id.desc())
        
        # Execute query
        work_items = query.all()
        
        # Get all projects and sub jobs for filters
        projects = Project.query.all()
        sub_jobs = SubJob.query.all()
        if project_id:
            sub_jobs = SubJob.query.filter_by(project_id=project_id).all()
        
        # Get all disciplines
        disciplines = DISCIPLINE_CHOICES
        
        return render_template('work_items.html', 
                              work_items=work_items,
                              projects=projects,
                              sub_jobs=sub_jobs,
                              disciplines=disciplines)
    except Exception as e:
        flash(f'Error loading work items: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('work_items.html', 
                              work_items=[],
                              projects=[],
                              sub_jobs=[],
                              disciplines=DISCIPLINE_CHOICES)

@main_bp.route('/add_work_item', methods=['GET', 'POST'])
def add_work_item():
    """Add a new work item"""
    try:
        if request.method == 'POST':
            try:
                # Get form data
                description = request.form.get('description')
                project_id = request.form.get('project_id')
                sub_job_id = request.form.get('sub_job_id')
                cost_code_id = request.form.get('cost_code_id')
                budgeted_quantity = request.form.get('budgeted_quantity')
                unit_of_measure = request.form.get('unit_of_measure')
                budgeted_man_hours = request.form.get('budgeted_man_hours')
                
                # Generate work item ID if not provided
                work_item_id_str = request.form.get('work_item_id_str') or f"WI-{uuid.uuid4().hex[:8].upper()}"
                
                # Create new work item
                new_work_item = WorkItem(
                    work_item_id_str=work_item_id_str,
                    description=description,
                    project_id=project_id,
                    sub_job_id=sub_job_id,
                    cost_code_id=cost_code_id,
                    budgeted_quantity=float(budgeted_quantity) if budgeted_quantity else None,
                    unit_of_measure=unit_of_measure,
                    budgeted_man_hours=float(budgeted_man_hours) if budgeted_man_hours else None
                )
                
                # Initialize progress data
                cost_code = CostCode.query.get(cost_code_id)
                if cost_code and cost_code.rule_of_credit:
                    rule = cost_code.rule_of_credit
                    steps = rule.get_steps()
                    progress_data = {}
                    for step in steps:
                        progress_data[step['name']] = 0
                    new_work_item.set_progress_data(progress_data)
                
                db.session.add(new_work_item)
                db.session.commit()
                
                flash('Work item added successfully!', 'success')
                
                # Redirect based on where the user came from
                if sub_job_id:
                    return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))
                else:
                    return redirect(url_for('main.work_items'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error adding work item: {str(e)}', 'danger')
                traceback.print_exc()
        
        # Get projects, sub jobs, and cost codes for the form
        projects = Project.query.all()
        
        # Check if sub_job_id is provided in the URL
        pre_selected_sub_job_id = request.args.get('sub_job_id', type=int)
        pre_selected_project_id = None
        
        if pre_selected_sub_job_id:
            sub_job = SubJob.query.get(pre_selected_sub_job_id)
            if sub_job:
                pre_selected_project_id = sub_job.project_id
                sub_jobs = SubJob.query.filter_by(project_id=pre_selected_project_id).all()
                cost_codes = CostCode.query.filter_by(project_id=pre_selected_project_id).all()
            else:
                sub_jobs = []
                cost_codes = []
        else:
            sub_jobs = []
            cost_codes = []
        
        return render_template('add_work_item.html', 
                              projects=projects,
                              sub_jobs=sub_jobs,
                              cost_codes=cost_codes,
                              pre_selected_project_id=pre_selected_project_id,
                              pre_selected_sub_job_id=pre_selected_sub_job_id)
    except Exception as e:
        flash(f'Error loading add work item form: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.index'))

@main_bp.route('/edit_work_item/<int:work_item_id>', methods=['GET', 'POST'])
def edit_work_item(work_item_id):
    """Edit an existing work item"""
    try:
        work_item = WorkItem.query.get_or_404(work_item_id)
        
        if request.method == 'POST':
            try:
                # Get form data
                description = request.form.get('description')
                project_id = request.form.get('project_id')
                sub_job_id = request.form.get('sub_job_id')
                cost_code_id = request.form.get('cost_code_id')
                budgeted_quantity = request.form.get('budgeted_quantity')
                unit_of_measure = request.form.get('unit_of_measure')
                budgeted_man_hours = request.form.get('budgeted_man_hours')
                work_item_id_str = request.form.get('work_item_id_str')
                
                # Update work item
                work_item.description = description
                work_item.project_id = project_id
                work_item.sub_job_id = sub_job_id
                work_item.cost_code_id = cost_code_id
                work_item.budgeted_quantity = float(budgeted_quantity) if budgeted_quantity else None
                work_item.unit_of_measure = unit_of_measure
                work_item.budgeted_man_hours = float(budgeted_man_hours) if budgeted_man_hours else None
                work_item.work_item_id_str = work_item_id_str
                
                # Recalculate earned values
                work_item.calculate_earned_values()
                
                db.session.commit()
                flash('Work item updated successfully!', 'success')
                return redirect(url_for('main.view_work_item', work_item_id=work_item.id))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating work item: {str(e)}', 'danger')
                traceback.print_exc()
        
        # Get projects, sub jobs, and cost codes for the form
        projects = Project.query.all()
        sub_jobs = SubJob.query.filter_by(project_id=work_item.project_id).all()
        cost_codes = CostCode.query.filter_by(project_id=work_item.project_id).all()
        
        return render_template('edit_work_item.html', 
                              work_item=work_item,
                              projects=projects,
                              sub_jobs=sub_jobs,
                              cost_codes=cost_codes)
    except Exception as e:
        flash(f'Error loading edit work item form: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.work_items'))

@main_bp.route('/view_work_item/<int:work_item_id>')
def view_work_item(work_item_id):
    """View a specific work item"""
    try:
        work_item = WorkItem.query.get_or_404(work_item_id)
        
        # Get rule of credit steps and progress
        steps = []
        progress_data = work_item.get_steps_progress()
        
        if work_item.cost_code and work_item.cost_code.rule_of_credit:
            rule = work_item.cost_code.rule_of_credit
            steps = rule.get_steps()
            
            # Add progress to steps
            for step in steps:
                step_name = step['name']
                step['progress'] = progress_data.get(step_name, 0)
        
        return render_template('view_work_item.html', 
                              work_item=work_item,
                              steps=steps)
    except Exception as e:
        flash(f'Error loading work item: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.work_items'))

@main_bp.route('/update_work_item_progress/<int:work_item_id>', methods=['GET', 'POST'])
def update_work_item_progress(work_item_id):
    """Update progress for a work item"""
    try:
        work_item = WorkItem.query.get_or_404(work_item_id)
        
        if request.method == 'POST':
            try:
                # Get progress data from form
                progress_data = {}
                for key, value in request.form.items():
                    if key.startswith('step_'):
                        step_name = key.replace('step_', '')
                        progress_data[step_name] = float(value) if value else 0
                
                # Update progress
                work_item.set_steps_progress(progress_data)
                
                # Calculate earned values
                work_item.calculate_earned_values()
                
                db.session.commit()
                flash('Progress updated successfully!', 'success')
                return redirect(url_for('main.view_work_item', work_item_id=work_item.id))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating progress: {str(e)}', 'danger')
                traceback.print_exc()
        
        # Get rule of credit steps and progress
        steps = []
        progress_data = work_item.get_steps_progress()
        
        if work_item.cost_code and work_item.cost_code.rule_of_credit:
            rule = work_item.cost_code.rule_of_credit
            steps = rule.get_steps()
            
            # Add progress to steps
            for step in steps:
                step_name = step['name']
                step['progress'] = progress_data.get(step_name, 0)
        
        return render_template('update_work_item_progress.html', 
                              work_item=work_item,
                              steps=steps)
    except Exception as e:
        flash(f'Error loading progress update form: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.work_items'))

@main_bp.route('/delete_work_item/<int:work_item_id>', methods=['POST'])
def delete_work_item(work_item_id):
    """Delete a work item"""
    try:
        work_item = WorkItem.query.get_or_404(work_item_id)
        sub_job_id = work_item.sub_job_id
        
        db.session.delete(work_item)
        db.session.commit()
        
        flash('Work item deleted successfully!', 'success')
        return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))
    except Exception as e:
        flash(f'Error deleting work item: {str(e)}', 'danger')
        return redirect(url_for('main.work_items'))

# ===== EXPORT ROUTES =====

@main_bp.route('/export/pdf/hours/<int:project_id>')
def export_hours_pdf_project(project_id):
    """Export hours report as PDF for a project"""
    try:
        project = Project.query.get_or_404(project_id)
        
        # Generate PDF
        pdf_file = generate_hours_report_pdf(project_id)
        
        # Create filename
        filename = f"hours_report_{project.project_id_str}_{datetime.datetime.now().strftime('%Y%m%d')}.pdf"
        
        # Send file to user
        return send_file(
            pdf_file,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.view_project', project_id=project_id))

@main_bp.route('/export/pdf/hours/<int:project_id>/<int:sub_job_id>')
def export_hours_pdf_sub_job(project_id, sub_job_id):
    """Export hours report as PDF for a sub job"""
    try:
        project = Project.query.get_or_404(project_id)
        sub_job = SubJob.query.get_or_404(sub_job_id)
        
        # Generate PDF
        pdf_file = generate_hours_report_pdf(project_id, sub_job_id)
        
        # Create filename
        filename = f"hours_report_{project.project_id_str}_{sub_job.sub_job_id_str}_{datetime.datetime.now().strftime('%Y%m%d')}.pdf"
        
        # Send file to user
        return send_file(
            pdf_file,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))

@main_bp.route('/export/pdf/quantities/<int:project_id>')
def export_quantities_pdf_project(project_id):
    """Export quantities report as PDF for a project"""
    try:
        project = Project.query.get_or_404(project_id)
        
        # Generate PDF
        pdf_file = generate_quantities_report_pdf(project_id)
        
        # Create filename
        filename = f"quantities_report_{project.project_id_str}_{datetime.datetime.now().strftime('%Y%m%d')}.pdf"
        
        # Send file to user
        return send_file(
            pdf_file,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.view_project', project_id=project_id))

@main_bp.route('/export/pdf/quantities/<int:project_id>/<int:sub_job_id>')
def export_quantities_pdf_sub_job(project_id, sub_job_id):
    """Export quantities report as PDF for a sub job"""
    try:
        project = Project.query.get_or_404(project_id)
        sub_job = SubJob.query.get_or_404(sub_job_id)
        
        # Generate PDF
        pdf_file = generate_quantities_report_pdf(project_id, sub_job_id)
        
        # Create filename
        filename = f"quantities_report_{project.project_id_str}_{sub_job.sub_job_id_str}_{datetime.datetime.now().strftime('%Y%m%d')}.pdf"
        
        # Send file to user
        return send_file(
            pdf_file,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))

@main_bp.route('/export/excel/hours/<int:project_id>')
def export_hours_excel_project(project_id):
    """Export hours report as Excel for a project"""
    try:
        project = Project.query.get_or_404(project_id)
        
        # Generate Excel
        excel_file = generate_hours_report_excel(project_id)
        
        # Create filename
        filename = f"hours_report_{project.project_id_str}_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx"
        
        # Send file to user
        return send_file(
            excel_file,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        flash(f'Error generating Excel: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.view_project', project_id=project_id))

@main_bp.route('/export/excel/hours/<int:project_id>/<int:sub_job_id>')
def export_hours_excel_sub_job(project_id, sub_job_id):
    """Export hours report as Excel for a sub job"""
    try:
        project = Project.query.get_or_404(project_id)
        sub_job = SubJob.query.get_or_404(sub_job_id)
        
        # Generate Excel
        excel_file = generate_hours_report_excel(project_id, sub_job_id)
        
        # Create filename
        filename = f"hours_report_{project.project_id_str}_{sub_job.sub_job_id_str}_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx"
        
        # Send file to user
        return send_file(
            excel_file,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        flash(f'Error generating Excel: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))

@main_bp.route('/export/excel/quantities/<int:project_id>')
def export_quantities_excel_project(project_id):
    """Export quantities report as Excel for a project"""
    try:
        project = Project.query.get_or_404(project_id)
        
        # Generate Excel
        excel_file = generate_quantities_report_excel(project_id)
        
        # Create filename
        filename = f"quantities_report_{project.project_id_str}_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx"
        
        # Send file to user
        return send_file(
            excel_file,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        flash(f'Error generating Excel: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.view_project', project_id=project_id))

@main_bp.route('/export/excel/quantities/<int:project_id>/<int:sub_job_id>')
def export_quantities_excel_sub_job(project_id, sub_job_id):
    """Export quantities report as Excel for a sub job"""
    try:
        project = Project.query.get_or_404(project_id)
        sub_job = SubJob.query.get_or_404(sub_job_id)
        
        # Generate Excel
        excel_file = generate_quantities_report_excel(project_id, sub_job_id)
        
        # Create filename
        filename = f"quantities_report_{project.project_id_str}_{sub_job.sub_job_id_str}_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx"
        
        # Send file to user
        return send_file(
            excel_file,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        flash(f'Error generating Excel: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))

# ===== API ROUTES =====

@main_bp.route('/api/get_sub_jobs/<int:project_id>')
def get_sub_jobs(project_id):
    """API to get sub jobs for a project"""
    sub_jobs = SubJob.query.filter_by(project_id=project_id).all()
    return jsonify([{'id': sj.id, 'name': sj.name} for sj in sub_jobs])

@main_bp.route('/api/get_cost_codes/<int:project_id>')
def get_cost_codes(project_id):
    """API to get cost codes for a project"""
    cost_codes = CostCode.query.filter_by(project_id=project_id).all()
    return jsonify([{'id': cc.id, 'name': f"{cc.cost_code_id_str} - {cc.description}"} for cc in cost_codes])

@main_bp.route('/api/get_rule_steps/<int:cost_code_id>')
def get_rule_steps(cost_code_id):
    """API to get rule of credit steps for a cost code"""
    try:
        cost_code = CostCode.query.get_or_404(cost_code_id)
        if not cost_code.rule_of_credit:
            return jsonify({'error': 'No rule of credit associated with this cost code'}), 404
        
        rule = cost_code.rule_of_credit
        steps = rule.get_steps()
        
        return jsonify({
            'rule_id': rule.id,
            'rule_name': rule.name,
            'steps': steps
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== REPORTS ROUTES =====

@main_bp.route('/reports')
def reports_index():
    """Reports index page"""
    return render_template('reports_index.html')
