from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from models import db, Project, SubJob, RuleOfCredit, CostCode, WorkItem, DISCIPLINE_CHOICES
from services import ProjectService, SubJobService, CostCodeService, WorkItemService, RuleOfCreditService
from utils.url_service import UrlService
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
        projects = ProjectService.get_all_projects()
        work_items = WorkItemService.get_recent_work_items(10)
        
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
        all_projects = ProjectService.get_all_projects()
        
        # Create a list to hold projects with their calculated values
        projects_with_data = []
        
        # Calculate project-level totals for each project
        for project in all_projects:
            # Get project metrics using the service
            metrics = ProjectService.get_project_metrics(project.id)
            
            # Create a dictionary with project and its calculated values
            project_data = {
                'project': project,
                'total_budgeted_hours': metrics['budgeted_hours'],
                'total_earned_hours': metrics['earned_hours'],
                'total_budgeted_quantity': metrics['budgeted_quantity'],
                'total_earned_quantity': metrics['earned_quantity'],
                'overall_progress': metrics['percent_complete']
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
        
        # Use the project service to create the project
        project = ProjectService.create_project(name, description)
        
        flash('Project added successfully!', 'success')
        return redirect(url_for('main.projects'))
        
    return render_template('add_project.html')

@main_bp.route('/view_project/<int:project_id>')
def view_project(project_id):
    """View a project"""
    try:
        # Use the project service to get project details
        project = ProjectService.get_project_details(project_id)
        if not project:
            flash('Project not found!', 'danger')
            return redirect(url_for('main.projects'))
            
        # Get sub jobs for this project using the sub job service
        sub_jobs = SubJobService.get_project_sub_jobs(project_id)
        
        # Get cost codes for this project using the cost code service
        cost_codes = CostCodeService.get_project_cost_codes(project_id)
        
        # Get project metrics using the project service
        metrics = ProjectService.get_project_metrics(project_id)
        
        return render_template('view_project.html', 
                              project=project, 
                              sub_jobs=sub_jobs, 
                              cost_codes=cost_codes,
                              metrics=metrics)
    except Exception as e:
        flash(f'Error viewing project: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.projects'))

@main_bp.route('/edit_project/<int:project_id>', methods=['GET', 'POST'])
def edit_project(project_id):
    """Edit a project"""
    # Use the project service to get project details
    project = ProjectService.get_project_details(project_id)
    if not project:
        flash('Project not found!', 'danger')
        return redirect(url_for('main.projects'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        # Use the project service to update the project
        ProjectService.update_project(project_id, name, description)
        
        flash('Project updated successfully!', 'success')
        return redirect(url_for('main.view_project', project_id=project_id))
        
    return render_template('edit_project.html', project=project)

@main_bp.route('/delete_project/<int:project_id>')
def delete_project(project_id):
    """Delete a project"""
    # Use the project service to delete the project
    success = ProjectService.delete_project(project_id)
    
    if success:
        flash('Project deleted successfully!', 'success')
    else:
        flash('Error deleting project!', 'danger')
        
    return redirect(url_for('main.projects'))

# ===== SUB JOB ROUTES =====

@main_bp.route('/sub_jobs')
def sub_jobs():
    """List all sub jobs"""
    try:
        # Get filter parameters
        discipline = request.args.get('discipline')
        area = request.args.get('area')
        
        # Get all sub jobs using the sub job service
        all_sub_jobs = SubJobService.get_all_sub_jobs()
        
        # Apply filters if provided
        if discipline:
            all_sub_jobs = [sj for sj in all_sub_jobs if sj.discipline == discipline]
        if area:
            all_sub_jobs = [sj for sj in all_sub_jobs if sj.area == area]
        
        # Get unique disciplines and areas for filtering
        disciplines = sorted(set(sj.discipline for sj in SubJobService.get_all_sub_jobs() if sj.discipline))
        areas = sorted(set(sj.area for sj in SubJobService.get_all_sub_jobs() if sj.area))
        
        return render_template('sub_jobs.html', 
                              sub_jobs=all_sub_jobs, 
                              disciplines=disciplines,
                              areas=areas,
                              selected_discipline=discipline,
                              selected_area=area)
    except Exception as e:
        flash(f'Error loading sub jobs: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('sub_jobs.html', sub_jobs=[])

@main_bp.route('/add_sub_job', methods=['GET', 'POST'])
def add_sub_job():
    """Add a new sub job"""
    # Get project_id from query parameter
    project_id = request.args.get('project_id', type=int)
    
    if request.method == 'POST':
        project_id = request.form.get('project_id', type=int)
        name = request.form.get('name')
        discipline = request.form.get('discipline')
        area = request.form.get('area')
        description = request.form.get('description')
        
        # Use the sub job service to create the sub job
        sub_job = SubJobService.create_sub_job(project_id, name, discipline, area, description)
        
        flash('Sub Job added successfully!', 'success')
        
        # Redirect to the project view if project_id is provided
        if project_id:
            return redirect(url_for('main.view_project', project_id=project_id))
        else:
            return redirect(url_for('main.sub_jobs'))
    
    # Get all projects for the dropdown
    projects = ProjectService.get_all_projects()
    
    # Get the selected project if project_id is provided
    selected_project = None
    if project_id:
        selected_project = ProjectService.get_project_details(project_id)
    
    return render_template('add_sub_job.html', 
                          projects=projects, 
                          selected_project=selected_project,
                          discipline_choices=DISCIPLINE_CHOICES)

@main_bp.route('/view_sub_job/<int:sub_job_id>')
def view_sub_job(sub_job_id):
    """View a sub job"""
    try:
        # Use the sub job service to get sub job details
        sub_job = SubJobService.get_sub_job_details(sub_job_id)
        if not sub_job:
            flash('Sub Job not found!', 'danger')
            return redirect(url_for('main.sub_jobs'))
            
        # Get the project for this sub job
        project = ProjectService.get_project_details(sub_job.project_id)
        
        # Get work items for this sub job using the work item service
        work_items = WorkItemService.get_sub_job_work_items(sub_job_id)
        
        # Get sub job metrics using the sub job service
        metrics = SubJobService.get_sub_job_metrics(sub_job_id)
        
        return render_template('view_sub_job.html', 
                              sub_job=sub_job, 
                              project=project, 
                              work_items=work_items,
                              metrics=metrics)
    except Exception as e:
        flash(f'Error viewing sub job: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.sub_jobs'))

@main_bp.route('/edit_sub_job/<int:sub_job_id>', methods=['GET', 'POST'])
def edit_sub_job(sub_job_id):
    """Edit a sub job"""
    # Use the sub job service to get sub job details
    sub_job = SubJobService.get_sub_job_details(sub_job_id)
    if not sub_job:
        flash('Sub Job not found!', 'danger')
        return redirect(url_for('main.sub_jobs'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        discipline = request.form.get('discipline')
        area = request.form.get('area')
        description = request.form.get('description')
        
        # Use the sub job service to update the sub job
        SubJobService.update_sub_job(sub_job_id, name, discipline, area, description)
        
        flash('Sub Job updated successfully!', 'success')
        return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))
        
    return render_template('edit_sub_job.html', 
                          sub_job=sub_job,
                          discipline_choices=DISCIPLINE_CHOICES)

@main_bp.route('/delete_sub_job/<int:sub_job_id>')
def delete_sub_job(sub_job_id):
    """Delete a sub job"""
    # Get the sub job to get its project_id for redirection
    sub_job = SubJobService.get_sub_job_details(sub_job_id)
    if not sub_job:
        flash('Sub Job not found!', 'danger')
        return redirect(url_for('main.sub_jobs'))
        
    project_id = sub_job.project_id
    
    # Use the sub job service to delete the sub job
    success = SubJobService.delete_sub_job(sub_job_id)
    
    if success:
        flash('Sub Job deleted successfully!', 'success')
    else:
        flash('Error deleting sub job!', 'danger')
        
    # Redirect to the project view if we have a project_id
    if project_id:
        return redirect(url_for('main.view_project', project_id=project_id))
    else:
        return redirect(url_for('main.sub_jobs'))

# ===== COST CODE ROUTES =====

@main_bp.route('/cost_codes')
def cost_codes():
    """List all cost codes"""
    try:
        # Get filter parameter
        project_id = request.args.get('project_id', type=int)
        
        # Get cost codes using the cost code service
        if project_id:
            all_cost_codes = CostCodeService.get_project_cost_codes(project_id)
            selected_project = ProjectService.get_project_details(project_id)
        else:
            all_cost_codes = CostCodeService.get_all_cost_codes()
            selected_project = None
        
        # Get all projects for the filter dropdown
        projects = ProjectService.get_all_projects()
        
        return render_template('cost_codes.html', 
                              cost_codes=all_cost_codes, 
                              projects=projects,
                              selected_project=selected_project)
    except Exception as e:
        flash(f'Error loading cost codes: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('cost_codes.html', cost_codes=[])

@main_bp.route('/add_cost_code', methods=['GET', 'POST'])
def add_cost_code():
    """Add a new cost code"""
    # Get project_id from query parameter
    project_id = request.args.get('project_id', type=int)
    
    if request.method == 'POST':
        project_id = request.form.get('project_id', type=int)
        code = request.form.get('code')
        description = request.form.get('description')
        rule_of_credit_id = request.form.get('rule_of_credit_id', type=int) or None
        
        # Use the cost code service to create the cost code
        cost_code = CostCodeService.create_cost_code(project_id, code, description, rule_of_credit_id)
        
        flash('Cost Code added successfully!', 'success')
        
        # Redirect to the project view if project_id is provided
        if project_id:
            return redirect(url_for('main.view_project', project_id=project_id))
        else:
            return redirect(url_for('main.cost_codes'))
    
    # Get all projects for the dropdown
    projects = ProjectService.get_all_projects()
    
    # Get all rules of credit for the dropdown
    rules_of_credit = RuleOfCreditService.get_all_rules_of_credit()
    
    # Get the selected project if project_id is provided
    selected_project = None
    if project_id:
        selected_project = ProjectService.get_project_details(project_id)
    
    return render_template('add_cost_code.html', 
                          projects=projects, 
                          rules_of_credit=rules_of_credit,
                          selected_project=selected_project)

@main_bp.route('/view_cost_code/<int:cost_code_id>')
def view_cost_code(cost_code_id):
    """View a cost code"""
    try:
        # Use the cost code service to get cost code details
        cost_code = CostCodeService.get_cost_code_details(cost_code_id)
        if not cost_code:
            flash('Cost Code not found!', 'danger')
            return redirect(url_for('main.cost_codes'))
            
        # Get the project for this cost code
        project = ProjectService.get_project_details(cost_code.project_id)
        
        # Get the rule of credit for this cost code if it has one
        rule_of_credit = None
        if cost_code.rule_of_credit_id:
            rule_of_credit = RuleOfCreditService.get_rule_of_credit_details(cost_code.rule_of_credit_id)
        
        return render_template('view_cost_code.html', 
                              cost_code=cost_code, 
                              project=project,
                              rule_of_credit=rule_of_credit)
    except Exception as e:
        flash(f'Error viewing cost code: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.cost_codes'))

@main_bp.route('/edit_cost_code/<int:cost_code_id>', methods=['GET', 'POST'])
def edit_cost_code(cost_code_id):
    """Edit a cost code"""
    # Use the cost code service to get cost code details
    cost_code = CostCodeService.get_cost_code_details(cost_code_id)
    if not cost_code:
        flash('Cost Code not found!', 'danger')
        return redirect(url_for('main.cost_codes'))
        
    if request.method == 'POST':
        code = request.form.get('code')
        description = request.form.get('description')
        rule_of_credit_id = request.form.get('rule_of_credit_id', type=int) or None
        
        # Use the cost code service to update the cost code
        CostCodeService.update_cost_code(cost_code_id, code, description, rule_of_credit_id)
        
        flash('Cost Code updated successfully!', 'success')
        return redirect(url_for('main.view_cost_code', cost_code_id=cost_code_id))
    
    # Get all rules of credit for the dropdown
    rules_of_credit = RuleOfCreditService.get_all_rules_of_credit()
        
    return render_template('edit_cost_code.html', 
                          cost_code=cost_code,
                          rules_of_credit=rules_of_credit)

@main_bp.route('/delete_cost_code/<int:cost_code_id>')
def delete_cost_code(cost_code_id):
    """Delete a cost code"""
    # Get the cost code to get its project_id for redirection
    cost_code = CostCodeService.get_cost_code_details(cost_code_id)
    if not cost_code:
        flash('Cost Code not found!', 'danger')
        return redirect(url_for('main.cost_codes'))
        
    project_id = cost_code.project_id
    
    # Use the cost code service to delete the cost code
    success = CostCodeService.delete_cost_code(cost_code_id)
    
    if success:
        flash('Cost Code deleted successfully!', 'success')
    else:
        flash('Error deleting cost code!', 'danger')
        
    # Redirect to the project view if we have a project_id
    if project_id:
        return redirect(url_for('main.view_project', project_id=project_id))
    else:
        return redirect(url_for('main.cost_codes'))

# ===== WORK ITEM ROUTES =====

@main_bp.route('/work_items')
def work_items():
    """List all work items"""
    try:
        # Get filter parameters
        sub_job_id = request.args.get('sub_job_id', type=int)
        project_id = request.args.get('project_id', type=int)
        
        # Get work items using the work item service
        if sub_job_id:
            all_work_items = WorkItemService.get_sub_job_work_items(sub_job_id)
            selected_sub_job = SubJobService.get_sub_job_details(sub_job_id)
            selected_project = ProjectService.get_project_details(selected_sub_job.project_id) if selected_sub_job else None
        elif project_id:
            # Get all sub jobs for this project
            sub_jobs = SubJobService.get_project_sub_jobs(project_id)
            sub_job_ids = [sub_job.id for sub_job in sub_jobs]
            
            # Get all work items for these sub jobs
            all_work_items = []
            for sub_job_id in sub_job_ids:
                all_work_items.extend(WorkItemService.get_sub_job_work_items(sub_job_id))
                
            selected_sub_job = None
            selected_project = ProjectService.get_project_details(project_id)
        else:
            all_work_items = WorkItemService.get_all_work_items()
            selected_sub_job = None
            selected_project = None
        
        # Get all projects and sub jobs for the filter dropdowns
        projects = ProjectService.get_all_projects()
        sub_jobs = SubJobService.get_all_sub_jobs()
        
        return render_template('work_items.html', 
                              work_items=all_work_items, 
                              projects=projects,
                              sub_jobs=sub_jobs,
                              selected_project=selected_project,
                              selected_sub_job=selected_sub_job)
    except Exception as e:
        flash(f'Error loading work items: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('work_items.html', work_items=[])

@main_bp.route('/add_work_item', methods=['GET', 'POST'])
def add_work_item():
    """Add a new work item"""
    # Get sub_job_id from query parameter
    sub_job_id = request.args.get('sub_job_id', type=int)
    
    if request.method == 'POST':
        sub_job_id = request.form.get('sub_job_id', type=int)
        cost_code_id = request.form.get('cost_code_id', type=int)
        description = request.form.get('description')
        budgeted_quantity = float(request.form.get('budgeted_quantity') or 0)
        budgeted_man_hours = float(request.form.get('budgeted_man_hours') or 0)
        earned_quantity = float(request.form.get('earned_quantity') or 0)
        earned_man_hours = float(request.form.get('earned_man_hours') or 0)
        
        # Use the work item service to create the work item
        work_item = WorkItemService.create_work_item(
            sub_job_id, 
            cost_code_id, 
            description, 
            budgeted_quantity, 
            budgeted_man_hours, 
            earned_quantity, 
            earned_man_hours
        )
        
        flash('Work Item added successfully!', 'success')
        
        # Redirect to the sub job view if sub_job_id is provided
        if sub_job_id:
            return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))
        else:
            return redirect(url_for('main.work_items'))
    
    # Get all sub jobs for the dropdown
    sub_jobs = SubJobService.get_all_sub_jobs()
    
    # Get the selected sub job if sub_job_id is provided
    selected_sub_job = None
    project_id = None
    if sub_job_id:
        selected_sub_job = SubJobService.get_sub_job_details(sub_job_id)
        if selected_sub_job:
            project_id = selected_sub_job.project_id
    
    # Get cost codes for the selected project
    cost_codes = []
    if project_id:
        cost_codes = CostCodeService.get_project_cost_codes(project_id)
    
    return render_template('add_work_item.html', 
                          sub_jobs=sub_jobs, 
                          cost_codes=cost_codes,
                          selected_sub_job=selected_sub_job)

@main_bp.route('/view_work_item/<int:work_item_id>')
def view_work_item(work_item_id):
    """View a work item"""
    try:
        # Use the work item service to get work item details
        work_item = WorkItemService.get_work_item_details(work_item_id)
        if not work_item:
            flash('Work Item not found!', 'danger')
            return redirect(url_for('main.work_items'))
            
        # Get the sub job for this work item
        sub_job = SubJobService.get_sub_job_details(work_item.sub_job_id)
        
        # Get the project for this work item
        project = ProjectService.get_project_details(work_item.project_id)
        
        # Get the cost code for this work item
        cost_code = CostCodeService.get_cost_code_details(work_item.cost_code_id)
        
        # Calculate metrics for this work item
        metrics = WorkItemService.calculate_work_item_metrics(work_item)
        
        return render_template('view_work_item.html', 
                              work_item=work_item, 
                              sub_job=sub_job,
                              project=project,
                              cost_code=cost_code,
                              metrics=metrics)
    except Exception as e:
        flash(f'Error viewing work item: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.work_items'))

@main_bp.route('/edit_work_item/<int:work_item_id>', methods=['GET', 'POST'])
def edit_work_item(work_item_id):
    """Edit a work item"""
    # Use the work item service to get work item details
    work_item = WorkItemService.get_work_item_details(work_item_id)
    if not work_item:
        flash('Work Item not found!', 'danger')
        return redirect(url_for('main.work_items'))
        
    if request.method == 'POST':
        description = request.form.get('description')
        budgeted_quantity = float(request.form.get('budgeted_quantity') or 0)
        budgeted_man_hours = float(request.form.get('budgeted_man_hours') or 0)
        earned_quantity = float(request.form.get('earned_quantity') or 0)
        earned_man_hours = float(request.form.get('earned_man_hours') or 0)
        
        # Use the work item service to update the work item
        WorkItemService.update_work_item(
            work_item_id, 
            description, 
            budgeted_quantity, 
            budgeted_man_hours, 
            earned_quantity, 
            earned_man_hours
        )
        
        flash('Work Item updated successfully!', 'success')
        return redirect(url_for('main.view_work_item', work_item_id=work_item_id))
        
    return render_template('edit_work_item.html', work_item=work_item)

@main_bp.route('/delete_work_item/<int:work_item_id>')
def delete_work_item(work_item_id):
    """Delete a work item"""
    # Get the work item to get its sub_job_id for redirection
    work_item = WorkItemService.get_work_item_details(work_item_id)
    if not work_item:
        flash('Work Item not found!', 'danger')
        return redirect(url_for('main.work_items'))
        
    sub_job_id = work_item.sub_job_id
    
    # Use the work item service to delete the work item
    success = WorkItemService.delete_work_item(work_item_id)
    
    if success:
        flash('Work Item deleted successfully!', 'success')
    else:
        flash('Error deleting work item!', 'danger')
        
    # Redirect to the sub job view if we have a sub_job_id
    if sub_job_id:
        return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))
    else:
        return redirect(url_for('main.work_items'))

# ===== RULE OF CREDIT ROUTES =====

@main_bp.route('/rules_of_credit')
def rules_of_credit():
    """List all rules of credit"""
    try:
        # Get all rules of credit using the rule of credit service
        all_rules = RuleOfCreditService.get_all_rules_of_credit()
        
        return render_template('rules_of_credit.html', rules=all_rules)
    except Exception as e:
        flash(f'Error loading rules of credit: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('rules_of_credit.html', rules=[])

@main_bp.route('/add_rule_of_credit', methods=['GET', 'POST'])
def add_rule_of_credit():
    """Add a new rule of credit"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        formula = request.form.get('formula')
        
        # Use the rule of credit service to create the rule
        rule = RuleOfCreditService.create_rule_of_credit(name, description, formula)
        
        flash('Rule of Credit added successfully!', 'success')
        return redirect(url_for('main.rules_of_credit'))
        
    return render_template('add_rule_of_credit.html')

@main_bp.route('/view_rule_of_credit/<int:rule_id>')
def view_rule_of_credit(rule_id):
    """View a rule of credit"""
    try:
        # Use the rule of credit service to get rule details
        rule = RuleOfCreditService.get_rule_of_credit_details(rule_id)
        if not rule:
            flash('Rule of Credit not found!', 'danger')
            return redirect(url_for('main.rules_of_credit'))
        
        return render_template('view_rule_of_credit.html', rule=rule)
    except Exception as e:
        flash(f'Error viewing rule of credit: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.rules_of_credit'))

@main_bp.route('/edit_rule_of_credit/<int:rule_id>', methods=['GET', 'POST'])
def edit_rule_of_credit(rule_id):
    """Edit a rule of credit"""
    # Use the rule of credit service to get rule details
    rule = RuleOfCreditService.get_rule_of_credit_details(rule_id)
    if not rule:
        flash('Rule of Credit not found!', 'danger')
        return redirect(url_for('main.rules_of_credit'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        formula = request.form.get('formula')
        
        # Use the rule of credit service to update the rule
        RuleOfCreditService.update_rule_of_credit(rule_id, name, description, formula)
        
        flash('Rule of Credit updated successfully!', 'success')
        return redirect(url_for('main.view_rule_of_credit', rule_id=rule_id))
        
    return render_template('edit_rule_of_credit.html', rule=rule)

@main_bp.route('/delete_rule_of_credit/<int:rule_id>')
def delete_rule_of_credit(rule_id):
    """Delete a rule of credit"""
    # Use the rule of credit service to delete the rule
    success = RuleOfCreditService.delete_rule_of_credit(rule_id)
    
    if success:
        flash('Rule of Credit deleted successfully!', 'success')
    else:
        flash('Error deleting rule of credit!', 'danger')
        
    return redirect(url_for('main.rules_of_credit'))

# ===== API ROUTES =====

@main_bp.route('/api/sub_jobs_by_project/<int:project_id>')
def api_sub_jobs_by_project(project_id):
    """API to get sub jobs for a project"""
    try:
        # Get sub jobs for this project using the sub job service
        sub_jobs = SubJobService.get_project_sub_jobs(project_id)
        
        # Convert to JSON-serializable format
        sub_jobs_data = [
            {
                'id': sub_job.id,
                'name': sub_job.name,
                'discipline': sub_job.discipline,
                'area': sub_job.area
            }
            for sub_job in sub_jobs
        ]
        
        return jsonify(sub_jobs_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/cost_codes_by_project/<int:project_id>')
def api_cost_codes_by_project(project_id):
    """API to get cost codes for a project"""
    try:
        # Get cost codes for this project using the cost code service
        cost_codes = CostCodeService.get_project_cost_codes(project_id)
        
        # Convert to JSON-serializable format
        cost_codes_data = [
            {
                'id': cost_code.id,
                'code': cost_code.code,
                'description': cost_code.description
            }
            for cost_code in cost_codes
        ]
        
        return jsonify(cost_codes_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/apply_rule_of_credit', methods=['POST'])
def api_apply_rule_of_credit():
    """API to apply a rule of credit to calculate earned values"""
    try:
        data = request.get_json()
        rule_id = data.get('rule_id')
        quantity = float(data.get('quantity') or 0)
        man_hours = float(data.get('man_hours') or 0)
        
        # Use the rule of credit service to apply the rule
        result = RuleOfCreditService.apply_rule_of_credit(rule_id, quantity, man_hours)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
