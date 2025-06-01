"""
Complete routes.py for Magellan EV Tracker v3.0
- Includes all routes for Projects, Work Items, Cost Codes, and Rules of Credit
- Adds dashboard route as the default landing page
- Ensures all navigation links work properly
- Fixes URL service import and endpoint references
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from models import db, Project, SubJob, WorkItem, RuleOfCredit
from services.project_service import ProjectService
from services.sub_job_service import SubJobService
from services.cost_code_service import CostCodeService
from services.work_item_service import WorkItemService
from services.rule_of_credit_service import RuleOfCreditService
from services.url_service import UrlService
import json
import traceback
from datetime import datetime

# Define blueprint
main_bp = Blueprint('main', __name__)

# Dashboard route
@main_bp.route('/dashboard')
def dashboard():
    try:
        # Get counts for dashboard statistics
        projects_count = len(ProjectService.get_all_projects())
        sub_jobs_count = len(SubJobService.get_all_sub_jobs())
        work_items_count = len(WorkItemService.get_all_work_items())
        rules_count = len(RuleOfCreditService.get_all_rules_of_credit())
        
        # Calculate overall progress (simplified for now)
        overall_progress = 0
        
        return render_template('dashboard.html', 
                              projects_count=projects_count,
                              sub_jobs_count=sub_jobs_count,
                              work_items_count=work_items_count,
                              rules_count=rules_count,
                              overall_progress=overall_progress)
    except Exception as e:
        flash(f"Error loading dashboard: {str(e)}", "error")
        return render_template('dashboard.html')

# Projects routes
@main_bp.route('/projects')
def projects():
    try:
        projects = ProjectService.get_all_projects()
        
        # Create projects_with_data structure expected by the template
        projects_with_data = []
        for project in projects:
            # Get metrics for this project
            metrics = ProjectService.get_project_metrics(project.id)
            
            # Get related data counts
            sub_jobs = SubJobService.get_sub_jobs_by_project(project.id)
            
            # Create the project data structure
            project_data = {
                'project': project,
                'overall_progress': metrics['percent_complete'],
                'total_budgeted_hours': metrics['budgeted_hours'],
                'total_earned_hours': metrics['earned_hours'],
                'sub_jobs': sub_jobs
            }
            
            projects_with_data.append(project_data)
        
        return render_template('projects.html', projects_with_data=projects_with_data)
    except Exception as e:
        flash(f"Error loading projects: {str(e)}", "error")
        return render_template('projects.html', projects_with_data=[])

@main_bp.route('/add_project', methods=['GET', 'POST'])
def add_project():
    if request.method == 'POST':
        try:
            project_id_str = request.form.get('project_id_str', '')
            name = request.form.get('name', '')
            description = request.form.get('description', '')
            
            # Create project
            project = ProjectService.create_project(
                project_id_str=project_id_str,
                name=name,
                description=description
            )
            
            flash(f"Project {name} created successfully!", "success")
            return redirect(url_for('main.projects'))
        except Exception as e:
            flash(f"Error creating project: {str(e)}", "error")
            return render_template('add_project.html')
    
    return render_template('add_project.html')

@main_bp.route('/view_project/<int:project_id>')
def view_project(project_id):
    try:
        project = ProjectService.get_project_by_id(project_id)
        if not project:
            flash("Project not found", "error")
            return redirect(url_for('main.projects'))
        
        sub_jobs = SubJobService.get_sub_jobs_by_project(project_id)
        return render_template('view_project.html', project=project, sub_jobs=sub_jobs)
    except Exception as e:
        flash(f"Error viewing project: {str(e)}", "error")
        return redirect(url_for('main.projects'))

@main_bp.route('/edit_project/<int:project_id>', methods=['GET', 'POST'])
def edit_project(project_id):
    try:
        project = ProjectService.get_project_by_id(project_id)
        if not project:
            flash("Project not found", "error")
            return redirect(url_for('main.projects'))
        
        if request.method == 'POST':
            try:
                name = request.form.get('name', '')
                description = request.form.get('description', '')
                
                # Update project
                ProjectService.update_project(
                    project_id=project_id,
                    name=name,
                    description=description
                )
                
                flash(f"Project {name} updated successfully!", "success")
                return redirect(url_for('main.view_project', project_id=project_id))
            except Exception as e:
                flash(f"Error updating project: {str(e)}", "error")
                return render_template('edit_project.html', project=project)
        
        return render_template('edit_project.html', project=project)
    except Exception as e:
        flash(f"Error editing project: {str(e)}", "error")
        return redirect(url_for('main.projects'))

@main_bp.route('/delete_project/<int:project_id>', methods=['POST'])
def delete_project(project_id):
    try:
        ProjectService.delete_project(project_id)
        flash("Project deleted successfully!", "success")
    except Exception as e:
        flash(f"Error deleting project: {str(e)}", "error")
    
    return redirect(url_for('main.projects'))

# Work Items routes
@main_bp.route('/work_items')
def work_items():
    try:
        sub_job_id = request.args.get('sub_job_id', type=int)
        if sub_job_id:
            sub_job = SubJobService.get_sub_job_by_id(sub_job_id)
            work_items = WorkItemService.get_work_items_by_sub_job(sub_job_id)
            return render_template('work_items.html', work_items=work_items, sub_job=sub_job)
        else:
            work_items = WorkItemService.get_all_work_items()
            return render_template('work_items.html', work_items=work_items, sub_job=None)
    except Exception as e:
        flash(f"Error loading work items: {str(e)}", "error")
        return render_template('work_items.html', work_items=[], sub_job=None)

@main_bp.route('/add_work_item', methods=['GET', 'POST'])
def add_work_item():
    try:
        sub_job_id = request.args.get('sub_job_id', type=int)
        
        if request.method == 'POST':
            try:
                sub_job_id = request.form.get('sub_job_id', type=int)
                work_item_id_str = request.form.get('work_item_id_str', '')
                description = request.form.get('description', '')
                quantity = request.form.get('quantity', type=float, default=0.0)
                unit = request.form.get('unit', '')
                
                # Create work item
                work_item = WorkItemService.create_work_item(
                    sub_job_id=sub_job_id,
                    work_item_id_str=work_item_id_str,
                    description=description,
                    quantity=quantity,
                    unit=unit
                )
                
                flash(f"Work Item {work_item_id_str} created successfully!", "success")
                return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))
            except Exception as e:
                flash(f"Error creating work item: {str(e)}", "error")
                sub_jobs = SubJobService.get_all_sub_jobs()
                return render_template('add_work_item.html', sub_jobs=sub_jobs, selected_sub_job_id=sub_job_id)
        
        sub_jobs = SubJobService.get_all_sub_jobs()
        return render_template('add_work_item.html', sub_jobs=sub_jobs, selected_sub_job_id=sub_job_id)
    except Exception as e:
        flash(f"Error loading add work item form: {str(e)}", "error")
        return redirect(url_for('main.work_items'))

# Sub Job routes
@main_bp.route('/sub_jobs')
def sub_jobs():
    try:
        project_id = request.args.get('project_id', type=int)
        if project_id:
            project = ProjectService.get_project_by_id(project_id)
            sub_jobs = SubJobService.get_sub_jobs_by_project(project_id)
            return render_template('sub_jobs.html', sub_jobs=sub_jobs, project=project)
        else:
            sub_jobs = SubJobService.get_all_sub_jobs()
            return render_template('sub_jobs.html', sub_jobs=sub_jobs, project=None)
    except Exception as e:
        flash(f"Error loading sub jobs: {str(e)}", "error")
        return render_template('sub_jobs.html', sub_jobs=[], project=None)

@main_bp.route('/add_sub_job', methods=['GET', 'POST'])
def add_sub_job():
    try:
        project_id = request.args.get('project_id', type=int)
        
        if request.method == 'POST':
            try:
                project_id = request.form.get('project_id', type=int)
                sub_job_id_str = request.form.get('sub_job_id_str', '')
                name = request.form.get('name', '')
                description = request.form.get('description', '')
                area = request.form.get('area', '')
                budgeted_hours = request.form.get('budgeted_hours', type=float, default=0.0)
                
                # Create sub job
                sub_job = SubJobService.create_sub_job(
                    project_id=project_id,
                    sub_job_id_str=sub_job_id_str,
                    name=name,
                    description=description,
                    area=area,
                    budgeted_hours=budgeted_hours
                )
                
                flash(f"Sub Job {name} created successfully!", "success")
                return redirect(url_for('main.view_project', project_id=project_id))
            except Exception as e:
                flash(f"Error creating sub job: {str(e)}", "error")
                projects = ProjectService.get_all_projects()
                return render_template('add_sub_job.html', projects=projects, selected_project_id=project_id)
        
        projects = ProjectService.get_all_projects()
        return render_template('add_sub_job.html', projects=projects, selected_project_id=project_id)
    except Exception as e:
        flash(f"Error loading add sub job form: {str(e)}", "error")
        return redirect(url_for('main.projects'))

@main_bp.route('/view_sub_job/<int:sub_job_id>')
def view_sub_job(sub_job_id):
    try:
        sub_job = SubJobService.get_sub_job_by_id(sub_job_id)
        if not sub_job:
            flash("Sub Job not found", "error")
            return redirect(url_for('main.projects'))
        
        project = ProjectService.get_project_by_id(sub_job.project_id)
        work_items = WorkItemService.get_work_items_by_sub_job(sub_job_id)
        
        return render_template('view_sub_job.html', sub_job=sub_job, project=project, work_items=work_items)
    except Exception as e:
        flash(f"Error viewing sub job: {str(e)}", "error")
        return redirect(url_for('main.projects'))

@main_bp.route('/edit_sub_job/<int:sub_job_id>', methods=['GET', 'POST'])
def edit_sub_job(sub_job_id):
    try:
        sub_job = SubJobService.get_sub_job_by_id(sub_job_id)
        if not sub_job:
            flash("Sub Job not found", "error")
            return redirect(url_for('main.projects'))
        
        if request.method == 'POST':
            try:
                name = request.form.get('name', '')
                description = request.form.get('description', '')
                area = request.form.get('area', '')
                budgeted_hours = request.form.get('budgeted_hours', type=float, default=0.0)
                
                # Update sub job
                SubJobService.update_sub_job(
                    sub_job_id=sub_job_id,
                    name=name,
                    description=description,
                    area=area,
                    budgeted_hours=budgeted_hours
                )
                
                flash(f"Sub Job {name} updated successfully!", "success")
                return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))
            except Exception as e:
                flash(f"Error updating sub job: {str(e)}", "error")
                return render_template('edit_sub_job.html', sub_job=sub_job)
        
        return render_template('edit_sub_job.html', sub_job=sub_job)
    except Exception as e:
        flash(f"Error editing sub job: {str(e)}", "error")
        return redirect(url_for('main.projects'))

@main_bp.route('/delete_sub_job/<int:sub_job_id>', methods=['POST'])
def delete_sub_job(sub_job_id):
    try:
        sub_job = SubJobService.get_sub_job_by_id(sub_job_id)
        if not sub_job:
            flash("Sub Job not found", "error")
            return redirect(url_for('main.projects'))
        
        project_id = sub_job.project_id
        SubJobService.delete_sub_job(sub_job_id)
        flash("Sub Job deleted successfully!", "success")
        return redirect(url_for('main.view_project', project_id=project_id))
    except Exception as e:
        flash(f"Error deleting sub job: {str(e)}", "error")
        return redirect(url_for('main.projects'))

# Cost Code routes
@main_bp.route('/cost_codes')
def cost_codes():
    try:
        project_id = request.args.get('project_id', type=int)
        if project_id:
            project = ProjectService.get_project_by_id(project_id)
            cost_codes = CostCodeService.get_cost_codes_by_project(project_id)
            return render_template('cost_codes.html', cost_codes=cost_codes, project=project)
        else:
            cost_codes = CostCodeService.get_all_cost_codes()
            return render_template('cost_codes.html', cost_codes=cost_codes, project=None)
    except Exception as e:
        flash(f"Error loading cost codes: {str(e)}", "error")
        return render_template('cost_codes.html', cost_codes=[], project=None)

@main_bp.route('/add_cost_code', methods=['GET', 'POST'])
def add_cost_code():
    try:
        project_id = request.args.get('project_id', type=int)
        rules = RuleOfCreditService.get_all_rules_of_credit()
        
        if request.method == 'POST':
            try:
                project_id = request.form.get('project_id', type=int)
                cost_code_id_str = request.form.get('cost_code_id_str', '')
                description = request.form.get('description', '')
                discipline = request.form.get('discipline', '')
                rule_of_credit_id = request.form.get('rule_of_credit_id', type=int)
                
                # Create cost code
                cost_code = CostCodeService.create_cost_code(
                    project_id=project_id,
                    cost_code_id_str=cost_code_id_str,
                    description=description,
                    discipline=discipline,
                    rule_of_credit_id=rule_of_credit_id
                )
                
                flash(f"Cost Code {cost_code_id_str} created successfully!", "success")
                return redirect(url_for('main.cost_codes', project_id=project_id))
            except Exception as e:
                flash(f"Error creating cost code: {str(e)}", "error")
                projects = ProjectService.get_all_projects()
                return render_template('add_cost_code.html', projects=projects, rules=rules, selected_project_id=project_id)
        
        projects = ProjectService.get_all_projects()
        return render_template('add_cost_code.html', projects=projects, rules=rules, selected_project_id=project_id)
    except Exception as e:
        flash(f"Error loading add cost code form: {str(e)}", "error")
        return redirect(url_for('main.projects'))

@main_bp.route('/edit_cost_code/<int:cost_code_id>', methods=['GET', 'POST'])
def edit_cost_code(cost_code_id):
    try:
        cost_code = CostCodeService.get_cost_code_by_id(cost_code_id)
        if not cost_code:
            flash("Cost Code not found", "error")
            return redirect(url_for('main.cost_codes'))
        
        rules = RuleOfCreditService.get_all_rules_of_credit()
        
        if request.method == 'POST':
            try:
                description = request.form.get('description', '')
                discipline = request.form.get('discipline', '')
                rule_of_credit_id = request.form.get('rule_of_credit_id', type=int)
                
                # Update cost code
                CostCodeService.update_cost_code(
                    cost_code_id=cost_code_id,
                    description=description,
                    discipline=discipline,
                    rule_of_credit_id=rule_of_credit_id
                )
                
                flash(f"Cost Code updated successfully!", "success")
                return redirect(url_for('main.cost_codes', project_id=cost_code.project_id))
            except Exception as e:
                flash(f"Error updating cost code: {str(e)}", "error")
                return render_template('edit_cost_code.html', cost_code=cost_code, rules=rules)
        
        return render_template('edit_cost_code.html', cost_code=cost_code, rules=rules)
    except Exception as e:
        flash(f"Error editing cost code: {str(e)}", "error")
        return redirect(url_for('main.cost_codes'))

@main_bp.route('/delete_cost_code/<int:cost_code_id>', methods=['POST'])
def delete_cost_code(cost_code_id):
    try:
        cost_code = CostCodeService.get_cost_code_by_id(cost_code_id)
        if not cost_code:
            flash("Cost Code not found", "error")
            return redirect(url_for('main.cost_codes'))
        
        project_id = cost_code.project_id
        CostCodeService.delete_cost_code(cost_code_id)
        flash("Cost Code deleted successfully!", "success")
        return redirect(url_for('main.cost_codes', project_id=project_id))
    except Exception as e:
        flash(f"Error deleting cost code: {str(e)}", "error")
        return redirect(url_for('main.cost_codes'))

# Rules of Credit routes
@main_bp.route('/rules_of_credit')
def rules_of_credit():
    try:
        # Get action from query parameters
        action = request.args.get('action')
        view_id = request.args.get('view')
        edit_id = request.args.get('edit')
        delete_id = request.args.get('delete')
        
        # Handle different actions based on query parameters
        if action == 'add':
            return render_template('add_rule_of_credit.html')
        elif view_id:
            rule = RuleOfCreditService.get_rule_of_credit_by_id(view_id)
            if rule:
                return render_template('view_rule_of_credit.html', rule=rule)
            else:
                flash('Rule of Credit not found', 'danger')
        elif edit_id:
            rule = RuleOfCreditService.get_rule_of_credit_by_id(edit_id)
            if rule:
                return render_template('edit_rule_of_credit.html', rule=rule)
            else:
                flash('Rule of Credit not found', 'danger')
        elif delete_id:
            rule = RuleOfCreditService.get_rule_of_credit_by_id(delete_id)
            if rule:
                RuleOfCreditService.delete_rule_of_credit(rule)
                flash(f'Rule of Credit {rule.name} deleted successfully', 'success')
            else:
                flash('Rule of Credit not found', 'danger')
        
        # Default: list all rules of credit
        rules = RuleOfCreditService.get_all_rules_of_credit()
        return render_template('rules_of_credit.html', rules=rules)
    except Exception as e:
        flash(f'Error loading rules of credit: {str(e)}', 'danger')
        return render_template('rules_of_credit.html', rules=[])

@main_bp.route('/add_rule_of_credit', methods=['GET', 'POST'])
def add_rule_of_credit():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '')
            description = request.form.get('description', '')
            steps_json = request.form.get('steps_json', '')
            
            # Create rule of credit
            rule = RuleOfCreditService.create_rule_of_credit(
                name=name,
                description=description,
                steps_json=steps_json
            )
            
            flash(f"Rule of Credit {name} created successfully!", "success")
            return redirect(url_for('main.rules_of_credit'))
        except Exception as e:
            flash(f"Error creating rule of credit: {str(e)}", "error")
            return render_template('add_rule_of_credit.html')
    
    return render_template('add_rule_of_credit.html')

# Reports route
@main_bp.route('/reports')
def reports():
    try:
        return render_template('reports.html')
    except Exception as e:
        flash(f"Error loading reports: {str(e)}", "error")
        return render_template('reports.html')
