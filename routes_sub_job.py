"""
Updated routes.py for Magellan EV Tracker v3.0
- Removes 'discipline' references from SubJob workflows
- Maintains 'area' field for SubJob
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
import traceback
from models import db
from services.project_service import ProjectService
from services.sub_job_service import SubJobService
from services.cost_code_service import CostCodeService
from services.work_item_service import WorkItemService
from services.rule_of_credit_service import RuleOfCreditService
from utils.url_service import URLService

# Define blueprint
main_bp = Blueprint('main', __name__)

# Constants
DISCIPLINE_CHOICES = ['Civil', 'Mechanical', 'Electrical', 'Instrumentation', 'Piping', 'Structural', 'Other']

# ===== SUB JOB ROUTES =====

@main_bp.route('/sub_jobs')
def sub_jobs():
    """List all sub jobs"""
    try:
        # Get filter parameters
        area = request.args.get('area')
        
        # Get all sub jobs using the sub job service
        all_sub_jobs = SubJobService.get_all_sub_jobs()
        
        # Apply filters if provided
        if area:
            all_sub_jobs = [sj for sj in all_sub_jobs if sj.area == area]
        
        # Get unique areas for filtering
        areas = sorted(set(sj.area for sj in SubJobService.get_all_sub_jobs() if sj.area))
        
        return render_template('sub_jobs.html', 
                              sub_jobs=all_sub_jobs, 
                              areas=areas,
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
        area = request.form.get('area')
        description = request.form.get('description')
        
        # Use the sub job service to create the sub job
        sub_job = SubJobService.create_sub_job(project_id, name, area, description)
        
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
                          selected_project=selected_project)

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
        area = request.form.get('area')
        description = request.form.get('description')
        
        # Use the sub job service to update the sub job
        SubJobService.update_sub_job(sub_job_id, name, area, description)
        
        flash('Sub Job updated successfully!', 'success')
        return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))
        
    return render_template('edit_sub_job.html', 
                          sub_job=sub_job)
