"""
Fixed routes.py for Magellan EV Tracker v3.0
- Corrects the import statement for UrlService (case-sensitive fix)
- Removes all 'discipline' references from SubJob workflows
- Ensures all required template variables are defined
- Fixes variable naming consistency between routes and templates
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
import traceback
from models import db
from services.project_service import ProjectService
from services.sub_job_service import SubJobService
from services.cost_code_service import CostCodeService
from services.work_item_service import WorkItemService
from services.rule_of_credit_service import RuleOfCreditService
from utils.url_service import UrlService  # Fixed import - changed URLService to UrlService

# Define blueprint
main_bp = Blueprint('main', __name__)

# Routes
@main_bp.route('/')
def index():
    """Home page route"""
    try:
        projects = ProjectService.get_all_projects()
        return render_template('index.html', projects=projects)
    except Exception as e:
        flash(f'Error loading projects: {str(e)}', 'danger')
        return render_template('index.html', projects=[])

@main_bp.route('/projects')
def projects():
    """Projects listing page"""
    try:
        projects = ProjectService.get_all_projects()
        return render_template('projects.html', projects=projects)
    except Exception as e:
        flash(f'Error loading projects: {str(e)}', 'danger')
        return render_template('projects.html', projects=[])

@main_bp.route('/add_project', methods=['GET', 'POST'])
def add_project():
    """Add project route"""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            project_id_str = request.form.get('project_id_str', '')
            description = request.form.get('description', '')
            
            # Create project
            project = ProjectService.create_project(name, project_id_str, description)
            
            flash(f'Project {name} created successfully!', 'success')
            return redirect(url_for('main.view_project', project_id=project.id))
        except Exception as e:
            flash(f'Error creating project: {str(e)}', 'danger')
    
    return render_template('add_project.html')

@main_bp.route('/edit_project', methods=['GET', 'POST'])
def edit_project():
    """Edit project route"""
    project_id = request.args.get('project_id', type=int)
    
    if not project_id:
        flash('Project ID is required', 'danger')
        return redirect(url_for('main.projects'))
    
    try:
        project = ProjectService.get_project_by_id(project_id)
        
        if not project:
            flash('Project not found', 'danger')
            return redirect(url_for('main.projects'))
        
        if request.method == 'POST':
            try:
                name = request.form.get('name')
                project_id_str = request.form.get('project_id_str')
                description = request.form.get('description', '')
                
                # Update project
                ProjectService.update_project(project_id, name, project_id_str, description)
                
                flash(f'Project {name} updated successfully!', 'success')
                return redirect(url_for('main.view_project', project_id=project_id))
            except Exception as e:
                flash(f'Error updating project: {str(e)}', 'danger')
        
        return render_template('edit_project.html', project=project)
    except Exception as e:
        flash(f'Error loading project: {str(e)}', 'danger')
        return redirect(url_for('main.projects'))

@main_bp.route('/view_project/<int:project_id>')
def view_project(project_id):
    """View project details"""
    try:
        project = ProjectService.get_project_by_id(project_id)
        
        if not project:
            flash('Project not found', 'danger')
            return redirect(url_for('main.projects'))
        
        # Get sub jobs for this project
        sub_jobs = SubJobService.get_project_sub_jobs(project_id)
        
        # Get metrics
        total_budget = sum(sj.budgeted_hours for sj in sub_jobs if sj.budgeted_hours)
        total_earned = sum(sj.earned_hours for sj in sub_jobs if sj.earned_hours)
        
        if total_budget > 0:
            overall_progress = (total_earned / total_budget) * 100
        else:
            overall_progress = 0
            
        return render_template('view_project.html', 
                              project=project, 
                              sub_jobs=sub_jobs,
                              total_budget=total_budget,
                              total_earned=total_earned,
                              overall_progress=overall_progress)
    except Exception as e:
        flash(f'Error viewing project: {str(e)}', 'danger')
        return redirect(url_for('main.projects'))

@main_bp.route('/delete_project', methods=['POST'])
def delete_project():
    """Delete project route"""
    project_id = request.form.get('project_id', type=int)
    
    if not project_id:
        flash('Project ID is required', 'danger')
        return redirect(url_for('main.projects'))
    
    try:
        # Delete project
        ProjectService.delete_project(project_id)
        
        flash('Project deleted successfully!', 'success')
        return redirect(url_for('main.projects'))
    except Exception as e:
        flash(f'Error deleting project: {str(e)}', 'danger')
        return redirect(url_for('main.projects'))

@main_bp.route('/sub_jobs')
def sub_jobs():
    """Sub jobs listing page"""
    try:
        project_id = request.args.get('project_id', type=int)
        
        if project_id:
            # Get sub jobs for specific project
            sub_jobs = SubJobService.get_project_sub_jobs(project_id)
            project = ProjectService.get_project_by_id(project_id)
            
            # Get areas for filtering
            areas = sorted(set(sj.area for sj in sub_jobs if sj.area))
            
            return render_template('sub_jobs.html', 
                                  sub_jobs=sub_jobs, 
                                  project=project,
                                  areas=areas,
                                  selected_project_id=project_id)
        else:
            # Get all sub jobs
            sub_jobs = SubJobService.get_all_sub_jobs()
            
            # Get areas for filtering
            areas = sorted(set(sj.area for sj in sub_jobs if sj.area))
            
            # Get all projects for dropdown
            projects = ProjectService.get_all_projects()
            
            return render_template('sub_jobs.html', 
                                  sub_jobs=sub_jobs, 
                                  projects=projects,
                                  areas=areas)
    except Exception as e:
        flash(f'Error loading sub jobs: {str(e)}', 'danger')
        return render_template('sub_jobs.html', sub_jobs=[], areas=[])

@main_bp.route('/add_sub_job', methods=['GET', 'POST'])
def add_sub_job():
    """Add sub job route"""
    project_id = request.args.get('project_id', type=int)
    
    if request.method == 'POST':
        try:
            project_id = request.form.get('project_id', type=int)
            name = request.form.get('name')
            sub_job_id_str = request.form.get('sub_job_id_str', '')
            description = request.form.get('description', '')
            area = request.form.get('area', '')
            budgeted_hours = request.form.get('budgeted_hours', type=float, default=0)
            
            # Create sub job
            sub_job = SubJobService.create_sub_job(
                project_id=project_id,
                name=name,
                sub_job_id_str=sub_job_id_str,
                description=description,
                area=area,
                budgeted_hours=budgeted_hours
            )
            
            flash(f'Sub Job {name} created successfully!', 'success')
            return redirect(url_for('main.view_sub_job', sub_job_id=sub_job.id))
        except Exception as e:
            flash(f'Error creating sub job: {str(e)}', 'danger')
            traceback.print_exc()
    
    try:
        # Get project for context
        if project_id:
            selected_project = ProjectService.get_project_by_id(project_id)
        else:
            selected_project = None
            
        # Get all projects for dropdown
        projects = ProjectService.get_all_projects()
        
        return render_template('add_sub_job.html', 
                              projects=projects, 
                              selected_project=selected_project,
                              project=selected_project)  # Added for compatibility
    except Exception as e:
        flash(f'Error loading form: {str(e)}', 'danger')
        return redirect(url_for('main.sub_jobs'))

@main_bp.route('/edit_sub_job', methods=['GET', 'POST'])
def edit_sub_job():
    """Edit sub job route"""
    sub_job_id = request.args.get('sub_job_id', type=int)
    
    if not sub_job_id:
        flash('Sub Job ID is required', 'danger')
        return redirect(url_for('main.sub_jobs'))
    
    try:
        sub_job = SubJobService.get_sub_job_by_id(sub_job_id)
        
        if not sub_job:
            flash('Sub Job not found', 'danger')
            return redirect(url_for('main.sub_jobs'))
        
        if request.method == 'POST':
            try:
                name = request.form.get('name')
                sub_job_id_str = request.form.get('sub_job_id_str')
                description = request.form.get('description', '')
                area = request.form.get('area', '')
                budgeted_hours = request.form.get('budgeted_hours', type=float, default=0)
                
                # Update sub job
                SubJobService.update_sub_job(
                    sub_job_id=sub_job_id,
                    name=name,
                    sub_job_id_str=sub_job_id_str,
                    description=description,
                    area=area,
                    budgeted_hours=budgeted_hours
                )
                
                flash(f'Sub Job {name} updated successfully!', 'success')
                return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))
            except Exception as e:
                flash(f'Error updating sub job: {str(e)}', 'danger')
        
        # Get project for context
        project = ProjectService.get_project_by_id(sub_job.project_id)
        
        return render_template('edit_sub_job.html', sub_job=sub_job, project=project)
    except Exception as e:
        flash(f'Error loading sub job: {str(e)}', 'danger')
        return redirect(url_for('main.sub_jobs'))

@main_bp.route('/view_sub_job/<int:sub_job_id>')
def view_sub_job(sub_job_id):
    """View sub job details"""
    try:
        sub_job = SubJobService.get_sub_job_by_id(sub_job_id)
        
        if not sub_job:
            flash('Sub Job not found', 'danger')
            return redirect(url_for('main.sub_jobs'))
        
        # Get project for context
        project = ProjectService.get_project_by_id(sub_job.project_id)
        
        # Get work items for this sub job
        work_items = WorkItemService.get_sub_job_work_items(sub_job_id)
        
        # Calculate metrics with default values to prevent errors
        total_budget = sum(wi.budgeted_hours for wi in work_items if wi.budgeted_hours) or 0
        total_earned = sum(wi.earned_hours for wi in work_items if wi.earned_hours) or 0
        
        if total_budget > 0:
            overall_progress = (total_earned / total_budget) * 100
        else:
            overall_progress = 0
            
        return render_template('view_sub_job.html', 
                              sub_job=sub_job, 
                              project=project,
                              work_items=work_items,
                              total_budget=total_budget,
                              total_earned=total_earned,
                              overall_progress=overall_progress)
    except Exception as e:
        flash(f'Error viewing sub job: {str(e)}', 'danger')
        return redirect(url_for('main.sub_jobs'))

@main_bp.route('/delete_sub_job', methods=['POST'])
def delete_sub_job():
    """Delete sub job route"""
    sub_job_id = request.form.get('sub_job_id', type=int)
    
    if not sub_job_id:
        flash('Sub Job ID is required', 'danger')
        return redirect(url_for('main.sub_jobs'))
    
    try:
        # Get project ID for redirect
        sub_job = SubJobService.get_sub_job_by_id(sub_job_id)
        project_id = sub_job.project_id if sub_job else None
        
        # Delete sub job
        SubJobService.delete_sub_job(sub_job_id)
        
        flash('Sub Job deleted successfully!', 'success')
        
        if project_id:
            return redirect(url_for('main.view_project', project_id=project_id))
        else:
            return redirect(url_for('main.sub_jobs'))
    except Exception as e:
        flash(f'Error deleting sub job: {str(e)}', 'danger')
        return redirect(url_for('main.sub_jobs'))

# Additional routes for cost codes, work items, and rules of credit would follow...
# These have been omitted for brevity in this fix, as they are not related to the current issue.
