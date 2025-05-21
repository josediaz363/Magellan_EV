from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from models import db, Project, SubJob, RuleOfCredit, CostCode, WorkItem, DISCIPLINE_CHOICES, STATUS_CHOICES
import json
import uuid
import os
import tempfile
from datetime import datetime, date, timedelta
from weasyprint import HTML, CSS
import pandas as pd
from io import BytesIO
from collections import defaultdict
from sqlalchemy import func

# Create a blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page route"""
    # Get selected project if any
    project_id = request.args.get('project_id')
    selected_project = None
    
    # Base query for work items
    work_items_query = WorkItem.query
    
    # Apply project filter if provided
    if project_id:
        work_items_query = work_items_query.filter(WorkItem.project_id == project_id)
        selected_project = Project.query.get(project_id)
    
    # Get all projects for dropdown
    projects = Project.query.all()
    
    # Get recent work items (limit to 10)
    work_items = work_items_query.order_by(WorkItem.id.desc()).limit(10).all()
    
    # Calculate status counts
    status_counts = {
        'not_started': work_items_query.filter(WorkItem.status == 'not_started').count(),
        'in_progress': work_items_query.filter(WorkItem.status == 'in_progress').count(),
        'completed': work_items_query.filter(WorkItem.status == 'completed').count(),
        'on_hold': work_items_query.filter(WorkItem.status == 'on_hold').count()
    }
    
    # Calculate overall progress
    total_budgeted_hours = work_items_query.with_entities(func.sum(WorkItem.budgeted_man_hours)).scalar() or 0
    total_earned_hours = work_items_query.with_entities(func.sum(WorkItem.earned_man_hours)).scalar() or 0
    overall_progress = 0
    if total_budgeted_hours > 0:
        overall_progress = (total_earned_hours / total_budgeted_hours) * 100
    
    # Calculate overall planned progress
    total_planned_percent = work_items_query.with_entities(func.avg(WorkItem.planned_percent_complete)).scalar() or 0
    overall_planned_progress = total_planned_percent
    
    # Calculate variance and SPI
    overall_variance = overall_progress - overall_planned_progress
    spi = 1.0
    if overall_planned_progress > 0:
        spi = overall_progress / overall_planned_progress
    
    # Generate progress histogram data
    progress_histogram = [0] * 10  # 10 bins for 0-10%, 11-20%, etc.
    for item in work_items_query.all():
        bin_index = min(9, int(item.percent_complete_hours / 10))
        progress_histogram[bin_index] += 1
    
    # Generate quantity distribution data
    quantity_distribution = {
        'labels': [],
        'budgeted': [],
        'earned': []
    }
    
    # Group by unit of measure
    uom_groups = defaultdict(lambda: {'budgeted': 0, 'earned': 0})
    for item in work_items_query.all():
        if item.unit_of_measure:
            uom_groups[item.unit_of_measure]['budgeted'] += item.budgeted_quantity
            uom_groups[item.unit_of_measure]['earned'] += item.earned_quantity
    
    # Convert to lists for chart
    for uom, values in uom_groups.items():
        quantity_distribution['labels'].append(uom)
        quantity_distribution['budgeted'].append(values['budgeted'])
        quantity_distribution['earned'].append(values['earned'])
    
    # Generate manpower distribution data
    manpower_distribution = {
        'labels': [],
        'values': []
    }
    
    # Group by discipline
    if project_id:
        # Get cost codes for the project
        cost_codes = CostCode.query.filter_by(project_id=project_id).all()
        discipline_groups = defaultdict(int)
        
        for code in cost_codes:
            # Get work items for this cost code
            items = work_items_query.filter_by(cost_code_id=code.id).all()
            for item in items:
                discipline_name = dict(DISCIPLINE_CHOICES).get(code.discipline, 'Other')
                discipline_groups[discipline_name] += item.budgeted_man_hours
        
        # Convert to lists for chart
        for discipline, hours in discipline_groups.items():
            manpower_distribution['labels'].append(discipline)
            manpower_distribution['values'].append(hours)
    else:
        # Group by discipline across all projects
        discipline_groups = defaultdict(int)
        
        # Get all cost codes
        cost_codes = CostCode.query.all()
        for code in cost_codes:
            # Get work items for this cost code
            items = work_items_query.filter_by(cost_code_id=code.id).all()
            for item in items:
                discipline_name = dict(DISCIPLINE_CHOICES).get(code.discipline, 'Other')
                discipline_groups[discipline_name] += item.budgeted_man_hours
        
        # Convert to lists for chart
        for discipline, hours in discipline_groups.items():
            manpower_distribution['labels'].append(discipline)
            manpower_distribution['values'].append(hours)
    
    # Generate budget by phase data
    budget_by_phase = {
        'labels': [],
        'budgeted': [],
        'earned': []
    }
    
    # Group by sub job (as phases)
    if project_id:
        # Get sub jobs for the project
        sub_jobs = SubJob.query.filter_by(project_id=project_id).all()
        
        for sub_job in sub_jobs:
            budget_by_phase['labels'].append(sub_job.name)
            
            # Get work items for this sub job
            items = work_items_query.filter_by(sub_job_id=sub_job.id).all()
            
            budgeted_hours = sum(item.budgeted_man_hours for item in items)
            earned_hours = sum(item.earned_man_hours for item in items)
            
            budget_by_phase['budgeted'].append(budgeted_hours)
            budget_by_phase['earned'].append(earned_hours)
    else:
        # Group by project (as phases)
        for project in projects:
            budget_by_phase['labels'].append(project.name)
            
            # Get work items for this project
            items = WorkItem.query.filter_by(project_id=project.id).all()
            
            budgeted_hours = sum(item.budgeted_man_hours for item in items)
            earned_hours = sum(item.earned_man_hours for item in items)
            
            budget_by_phase['budgeted'].append(budgeted_hours)
            budget_by_phase['earned'].append(earned_hours)
    
    return render_template('index.html', 
                          projects=projects,
                          selected_project=selected_project,
                          work_items=work_items,
                          status_counts=status_counts,
                          overall_progress=overall_progress,
                          overall_planned_progress=overall_planned_progress,
                          overall_variance=overall_variance,
                          spi=spi,
                          progress_histogram=progress_histogram,
                          quantity_distribution=quantity_distribution,
                          manpower_distribution=manpower_distribution,
                          budget_by_phase=budget_by_phase)

# ===== PROJECT ROUTES =====

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
    project = Project.query.get_or_404(project_id)
    sub_jobs = SubJob.query.filter_by(project_id=project_id).all()
    return render_template('view_project.html', project=project, sub_jobs=sub_jobs)

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
    sub_job = SubJob.query.get_or_404(sub_job_id)
    work_items = WorkItem.query.filter_by(sub_job_id=sub_job_id).all()
    return render_template('view_sub_job.html', sub_job=sub_job, work_items=work_items)

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

# ===== WORK ITEMS ROUTES =====

@main_bp.route('/work_items')
def work_items():
    """List all work items with filtering options"""
    # Get filter parameters
    project_id = request.args.get('project', 'all')
    sub_job_id = request.args.get('sub_job', 'all')
    
    # Base query
    query = WorkItem.query
    
    # Apply filters
    if project_id != 'all':
        query = query.filter(WorkItem.project_id == project_id)
    
    if sub_job_id != 'all':
        query = query.filter(WorkItem.sub_job_id == sub_job_id)
    
    # Get all work items based on filters
    work_items = query.all()
    
    # Get all projects and cost codes for dropdowns
    projects = Project.query.all()
    cost_codes = CostCode.query.all()
    
    # Get sub jobs for selected project
    sub_jobs = []
    if project_id != 'all':
        sub_jobs = SubJob.query.filter_by(project_id=project_id).all()
    
    # Calculate status counts
    status_counts = {
        'not_started': sum(1 for item in work_items if item.status == 'not_started'),
        'in_progress': sum(1 for item in work_items if item.status == 'in_progress'),
        'completed': sum(1 for item in work_items if item.status == 'completed'),
        'on_hold': sum(1 for item in work_items if item.status == 'on_hold')
    }
    
    return render_template('work_items.html', 
                          work_items=work_items, 
                          projects=projects,
                          sub_jobs=sub_jobs,
                          cost_codes=cost_codes,
                          selected_project_id=int(project_id) if project_id != 'all' else 'all',
                          selected_sub_job_id=int(sub_job_id) if sub_job_id != 'all' else 'all',
                          status_counts=status_counts)

@main_bp.route('/batch_update_work_items', methods=['GET', 'POST'])
def batch_update_work_items():
    """Batch update work items"""
    if request.method == 'POST':
        # Get selected work items
        selected_items = request.form.getlist('selected_items')
        update_type = request.form.get('update_type')
        
        if not selected_items:
            flash('No work items selected', 'warning')
            return redirect(url_for('main.batch_update_work_items'))
        
        if update_type == 'status':
            # Update status
            status_value = request.form.get('status_value')
            for item_id in selected_items:
                work_item = WorkItem.query.get(item_id)
                if work_item:
                    work_item.status = status_value
                    
                    # Update actual dates if needed
                    if status_value == 'in_progress' and not work_item.actual_start_date:
                        work_item.actual_start_date = datetime.utcnow().date()
                    elif status_value == 'completed' and not work_item.actual_end_date:
                        work_item.actual_end_date = datetime.utcnow().date()
            
            db.session.commit()
            flash(f'Updated status for {len(selected_items)} work items', 'success')
            
        elif update_type == 'progress':
            # Update actual progress
            for item_id in selected_items:
                work_item = WorkItem.query.get(item_id)
                if work_item:
                    actual_percent = request.form.get(f'actual_percent_{item_id}')
                    if actual_percent is not None:
                        actual_percent = float(actual_percent)
                        # Calculate earned values based on percentage
                        work_item.earned_man_hours = work_item.budgeted_man_hours * (actual_percent / 100)
                        work_item.earned_quantity = work_item.budgeted_quantity * (actual_percent / 100)
                        
                        # Update status if needed
                        if actual_percent >= 100 and work_item.status != 'completed':
                            work_item.status = 'completed'
                            work_item.actual_end_date = datetime.utcnow().date()
                        elif actual_percent > 0 and work_item.status == 'not_started':
                            work_item.status = 'in_progress'
                            if not work_item.actual_start_date:
                                work_item.actual_start_date = datetime.utcnow().date()
            
            db.session.commit()
            flash(f'Updated progress for {len(selected_items)} work items', 'success')
            
        elif update_type == 'planned':
            # Update planned % complete
            planned_interval = request.form.get('planned_interval')
            for item_id in selected_items:
                work_item = WorkItem.query.get(item_id)
                if work_item:
                    planned_percent = request.form.get(f'planned_percent_{item_id}')
                    if planned_percent is not None:
                        work_item.planned_percent_complete = float(planned_percent)
                        work_item.interval_type = planned_interval
            
            db.session.commit()
            flash(f'Updated planned % complete for {len(selected_items)} work items', 'success')
        
        return redirect(url_for('main.work_items'))
    
    # GET request - show batch update form
    # Get filter parameters
    project_id = request.args.get('project', 'all')
    sub_job_id = request.args.get('sub_job', 'all')
    
    # Base query
    query = WorkItem.query
    
    # Apply filters
    if project_id != 'all':
        query = query.filter(WorkItem.project_id == project_id)
    
    if sub_job_id != 'all':
        query = query.filter(WorkItem.sub_job_id == sub_job_id)
    
    # Get all work items based on filters
    work_items = query.all()
    
    # Get all projects and cost codes for dropdowns
    projects = Project.query.all()
    cost_codes = CostCode.query.all()
    
    # Get sub jobs for selected project
    sub_jobs = []
    if project_id != 'all':
        sub_jobs = SubJob.query.filter_by(project_id=project_id).all()
    
    return render_template('batch_update_work_items.html', 
                          work_items=work_items, 
                          projects=projects,
                          sub_jobs=sub_jobs,
                          cost_codes=cost_codes,
                          selected_project_id=int(project_id) if project_id != 'all' else 'all',
                          selected_sub_job_id=int(sub_job_id) if sub_job_id != 'all' else 'all')

@main_bp.route('/add_work_item', methods=['GET', 'POST'])
def add_work_item():
    """Add a new work item"""
    if request.method == 'POST':
        # Get form data
        project_id = request.form.get('project_id')
        sub_job_id = request.form.get('sub_job_id')
        cost_code_id = request.form.get('cost_code_id')
        description = request.form.get('description')
        budgeted_quantity = request.form.get('budgeted_quantity')
        unit_of_measure = request.form.get('unit_of_measure')
        budgeted_man_hours = request.form.get('budgeted_man_hours')
        work_item_id_str = request.form.get('work_item_id_str') or f"WI-{uuid.uuid4().hex[:8].upper()}"
        
        # Get planned dates and percent complete
        planned_start_date_str = request.form.get('planned_start_date')
        planned_end_date_str = request.form.get('planned_end_date')
        planned_percent_complete = request.form.get('planned_percent_complete', 0)
        interval_type = request.form.get('interval_type', 'weeks')
        
        # Parse dates if provided
        planned_start_date = None
        if planned_start_date_str:
            try:
                planned_start_date = datetime.strptime(planned_start_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
                
        planned_end_date = None
        if planned_end_date_str:
            try:
                planned_end_date = datetime.strptime(planned_end_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # Create new work item
        new_work_item = WorkItem(
            work_item_id_str=work_item_id_str,
            description=description,
            project_id=project_id,
            sub_job_id=sub_job_id,
            cost_code_id=cost_code_id,
            budgeted_quantity=float(budgeted_quantity) if budgeted_quantity else 0,
            unit_of_measure=unit_of_measure,
            budgeted_man_hours=float(budgeted_man_hours) if budgeted_man_hours else 0,
            status='not_started',  # Default status
            planned_percent_complete=float(planned_percent_complete) if planned_percent_complete else 0,
            interval_type=interval_type,
            planned_start_date=planned_start_date,
            planned_end_date=planned_end_date
        )
        
        db.session.add(new_work_item)
        db.session.commit()
        
        flash('Work item added successfully!', 'success')
        return redirect(url_for('main.work_items'))
    
    # Get all projects, sub jobs, and cost codes for dropdowns
    projects = Project.query.all()
    sub_jobs = []  # Will be populated via AJAX
    cost_codes = CostCode.query.all()
    
    return render_template('add_work_item.html', 
                          projects=projects, 
                          sub_jobs=sub_jobs, 
                          cost_codes=cost_codes)

@main_bp.route('/edit_work_item/<int:work_item_id>', methods=['GET', 'POST'])
def edit_work_item(work_item_id):
    """Edit an existing work item"""
    work_item = WorkItem.query.get_or_404(work_item_id)
    
    if request.method == 'POST':
        # Update work item data
        work_item.work_item_id_str = request.form.get('work_item_id_str')
        work_item.description = request.form.get('description')
        work_item.project_id = request.form.get('project_id')
        work_item.sub_job_id = request.form.get('sub_job_id')
        work_item.cost_code_id = request.form.get('cost_code_id')
        work_item.budgeted_quantity = float(request.form.get('budgeted_quantity')) if request.form.get('budgeted_quantity') else 0
        work_item.unit_of_measure = request.form.get('unit_of_measure')
        work_item.budgeted_man_hours = float(request.form.get('budgeted_man_hours')) if request.form.get('budgeted_man_hours') else 0
        work_item.status = request.form.get('status')
        
        # Update planned data
        planned_percent_complete = request.form.get('planned_percent_complete')
        if planned_percent_complete is not None:
            work_item.planned_percent_complete = float(planned_percent_complete)
        
        work_item.interval_type = request.form.get('interval_type', 'weeks')
        
        # Parse dates if provided
        planned_start_date_str = request.form.get('planned_start_date')
        if planned_start_date_str:
            try:
                work_item.planned_start_date = datetime.strptime(planned_start_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
                
        planned_end_date_str = request.form.get('planned_end_date')
        if planned_end_date_str:
            try:
                work_item.planned_end_date = datetime.strptime(planned_end_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        db.session.commit()
        
        # Recalculate earned values
        work_item.calculate_earned_values()
        db.session.commit()
        
        flash('Work item updated successfully!', 'success')
        return redirect(url_for('main.work_items'))
    
    # Get all projects, sub jobs, and cost codes for dropdowns
    projects = Project.query.all()
    sub_jobs = SubJob.query.filter_by(project_id=work_item.project_id).all()
    cost_codes = CostCode.query.all()
    
    return render_template('edit_work_item.html', 
                          work_item=work_item,
                          projects=projects, 
                          sub_jobs=sub_jobs, 
                          cost_codes=cost_codes)

@main_bp.route('/view_work_item/<int:work_item_id>')
def view_work_item(work_item_id):
    """View a specific work item"""
    work_item = WorkItem.query.get_or_404(work_item_id)
    
    # Get the cost code and rule of credit
    cost_code = CostCode.query.get(work_item.cost_code_id)
    rule = None
    if cost_code and cost_code.rule_of_credit_id:
        rule = RuleOfCredit.query.get(cost_code.rule_of_credit_id)
    
    return render_template('view_work_item.html', 
                          work_item=work_item,
                          cost_code=cost_code,
                          rule=rule)

@main_bp.route('/update_work_item_progress/<int:work_item_id>', methods=['GET', 'POST'])
def update_work_item_progress(work_item_id):
    """Update progress for a specific work item"""
    work_item = WorkItem.query.get_or_404(work_item_id)
    
    # Get the cost code and rule of credit
    cost_code = CostCode.query.get(work_item.cost_code_id)
    rule = None
    steps = []
    
    if cost_code and cost_code.rule_of_credit_id:
        rule = RuleOfCredit.query.get(cost_code.rule_of_credit_id)
        if rule:
            steps = rule.get_steps()
    
    if request.method == 'POST':
        # Update status
        work_item.status = request.form.get('status')
        
        # Update progress for each step
        progress_data = {}
        for step in steps:
            step_name = step.get('name')
            step_progress = request.form.get(f"step_{step_name}")
            if step_progress is not None:
                work_item.update_progress_step(step_name, float(step_progress))
        
        db.session.commit()
        
        flash('Work item progress updated successfully!', 'success')
        return redirect(url_for('main.work_items'))
    
    # Get current progress data
    progress_data = work_item.get_steps_progress()
    
    return render_template('update_work_item_progress.html', 
                          work_item=work_item,
                          cost_code=cost_code,
                          rule=rule,
                          steps=steps,
                          progress_data=progress_data)

@main_bp.route('/update_planned_progress/<int:work_item_id>', methods=['POST'])
def update_planned_progress(work_item_id):
    """Update planned progress for a specific work item"""
    work_item = WorkItem.query.get_or_404(work_item_id)
    
    # Update planned progress data
    planned_percent_complete = request.form.get('planned_percent_complete')
    if planned_percent_complete is not None:
        work_item.planned_percent_complete = float(planned_percent_complete)
    
    work_item.interval_type = request.form.get('interval_type', 'weeks')
    
    # Parse dates if provided
    planned_start_date_str = request.form.get('planned_start_date')
    if planned_start_date_str:
        try:
            work_item.planned_start_date = datetime.strptime(planned_start_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
            
    planned_end_date_str = request.form.get('planned_end_date')
    if planned_end_date_str:
        try:
            work_item.planned_end_date = datetime.strptime(planned_end_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # Calculate variance
    work_item.calculate_variance()
    
    db.session.commit()
    
    flash('Planned progress updated successfully!', 'success')
    return redirect(url_for('main.update_work_item_progress', work_item_id=work_item_id))

@main_bp.route('/delete_work_item/<int:work_item_id>', methods=['POST'])
def delete_work_item(work_item_id):
    """Delete a work item"""
    work_item = WorkItem.query.get_or_404(work_item_id)
    
    db.session.delete(work_item)
    db.session.commit()
    
    flash('Work item deleted successfully!', 'success')
    return redirect(url_for('main.work_items'))

# ===== REPORTS ROUTES =====

@main_bp.route('/reports')
def reports():
    """Reports dashboard"""
    projects = Project.query.all()
    return render_template('reports.html', projects=projects)

@main_bp.route('/generate_hours_report')
def generate_hours_report():
    """Generate a report showing earned hours vs. budgeted hours"""
    project_id = request.args.get('project_id')
    sub_job_id = request.args.get('sub_job_id')
    level = request.args.get('level', 'project')
    report_format = request.args.get('format', 'pdf')
    
    if not project_id:
        flash('Project is required', 'danger')
        return redirect(url_for('main.reports'))
    
    project = Project.query.get_or_404(project_id)
    
    # Base query
    query = WorkItem.query.filter(WorkItem.project_id == project_id)
    
    # Apply sub job filter if provided
    if sub_job_id:
        query = query.filter(WorkItem.sub_job_id == sub_job_id)
    
    # Get all work items based on filters
    work_items = query.all()
    
    # Group data based on level
    grouped_data = {}
    if level == 'project':
        grouped_data = {project.id: work_items}
    elif level == 'sub_job':
        # Group by sub job
        sub_job_groups = defaultdict(list)
        for item in work_items:
            sub_job_groups[item.sub_job_id].append(item)
        grouped_data = dict(sub_job_groups)
    elif level == 'work_item':
        # No grouping, each work item is its own group
        grouped_data = {item.id: [item] for item in work_items}
    
    # Get all unique Rules of Credit steps
    all_steps = []
    for item in work_items:
        if item.cost_code and item.cost_code.rule_of_credit:
            steps = item.cost_code.rule_of_credit.get_steps()
            for step in steps:
                step_name = step.get('name')
                if step_name not in all_steps:
                    all_steps.append(step_name)
    
    # Limit to 7 steps as per requirements
    max_steps = min(len(all_steps), 7)
    roc_step_headers = all_steps[:max_steps]
    
    # Generate report based on format
    if report_format == 'pdf':
        # Generate PDF report
        report_title = "Hours Report"
        report_subtitle = "Progress Detail Sub Job by Hours"
        generation_date = datetime.now().strftime("%Y-%m-%d")
        
        # Render HTML template
        html_content = render_template('report_template_hours.html',
                                      report_title=report_title,
                                      report_subtitle=report_subtitle,
                                      project=project,
                                      grouped_data=grouped_data,
                                      group_by=level,
                                      max_steps=max_steps,
                                      roc_step_headers=roc_step_headers,
                                      generation_date=generation_date)
        
        # Convert HTML to PDF
        pdf = HTML(string=html_content).write_pdf()
        
        # Create response
        response = BytesIO(pdf)
        
        # Return PDF file
        return send_file(
            response,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{project.project_id_str}_hours_report_{datetime.now().strftime('%Y%m%d')}.pdf"
        )
    
    elif report_format == 'excel':
        # Generate Excel report
        # Create a pandas DataFrame
        data = []
        for group_key, items in grouped_data.items():
            for item in items:
                row = {
                    'Work Item': item.work_item_id_str,
                    'Description': item.description,
                    'UoM': item.unit_of_measure,
                    'Budgeted Hours': item.budgeted_man_hours,
                    'Earned Hours': item.earned_man_hours,
                    '% Complete': item.percent_complete_hours,
                    'Planned % Complete': item.planned_percent_complete,
                    'Variance': item.variance_percent
                }
                
                # Add Rules of Credit steps
                if item.cost_code and item.cost_code.rule_of_credit:
                    progress_data = item.get_steps_progress()
                    steps = item.cost_code.rule_of_credit.get_steps()
                    step_map = {step["name"]: step for step in steps}
                    
                    for step_name in roc_step_headers:
                        if step_name in step_map:
                            row[step_name] = progress_data.get(step_name, 0)
                        else:
                            row[step_name] = None
                
                data.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Create Excel file
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Hours Report', index=False)
        
        output.seek(0)
        
        # Return Excel file
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f"{project.project_id_str}_hours_report_{datetime.now().strftime('%Y%m%d')}.xlsx"
        )
    
    # Default fallback
    flash('Invalid report format', 'danger')
    return redirect(url_for('main.reports'))

@main_bp.route('/generate_quantities_report')
def generate_quantities_report():
    """Generate a report showing earned quantities vs. budgeted quantities"""
    project_id = request.args.get('project_id')
    sub_job_id = request.args.get('sub_job_id')
    level = request.args.get('level', 'project')
    report_format = request.args.get('format', 'pdf')
    
    if not project_id:
        flash('Project is required', 'danger')
        return redirect(url_for('main.reports'))
    
    project = Project.query.get_or_404(project_id)
    
    # Base query
    query = WorkItem.query.filter(WorkItem.project_id == project_id)
    
    # Apply sub job filter if provided
    if sub_job_id:
        query = query.filter(WorkItem.sub_job_id == sub_job_id)
    
    # Get all work items based on filters
    work_items = query.all()
    
    # Group data based on level
    grouped_data = {}
    if level == 'project':
        grouped_data = {project.id: work_items}
    elif level == 'sub_job':
        # Group by sub job
        sub_job_groups = defaultdict(list)
        for item in work_items:
            sub_job_groups[item.sub_job_id].append(item)
        grouped_data = dict(sub_job_groups)
    elif level == 'work_item':
        # No grouping, each work item is its own group
        grouped_data = {item.id: [item] for item in work_items}
    
    # Get all unique Rules of Credit steps
    all_steps = []
    for item in work_items:
        if item.cost_code and item.cost_code.rule_of_credit:
            steps = item.cost_code.rule_of_credit.get_steps()
            for step in steps:
                step_name = step.get('name')
                if step_name not in all_steps:
                    all_steps.append(step_name)
    
    # Limit to 7 steps as per requirements
    max_steps = min(len(all_steps), 7)
    roc_step_headers = all_steps[:max_steps]
    
    # Generate report based on format
    if report_format == 'pdf':
        # Generate PDF report
        report_title = "Quantities Report"
        report_subtitle = "Progress Detail Sub Job by Quantities"
        generation_date = datetime.now().strftime("%Y-%m-%d")
        
        # Render HTML template
        html_content = render_template('report_template_quantities.html',
                                      report_title=report_title,
                                      report_subtitle=report_subtitle,
                                      project=project,
                                      grouped_data=grouped_data,
                                      group_by=level,
                                      max_steps=max_steps,
                                      roc_step_headers=roc_step_headers,
                                      generation_date=generation_date)
        
        # Convert HTML to PDF
        pdf = HTML(string=html_content).write_pdf()
        
        # Create response
        response = BytesIO(pdf)
        
        # Return PDF file
        return send_file(
            response,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{project.project_id_str}_quantities_report_{datetime.now().strftime('%Y%m%d')}.pdf"
        )
    
    elif report_format == 'excel':
        # Generate Excel report
        # Create a pandas DataFrame
        data = []
        for group_key, items in grouped_data.items():
            for item in items:
                row = {
                    'Work Item': item.work_item_id_str,
                    'Description': item.description,
                    'UoM': item.unit_of_measure,
                    'Budgeted Quantity': item.budgeted_quantity,
                    'Earned Quantity': item.earned_quantity,
                    '% Complete': item.percent_complete_quantity,
                    'Planned % Complete': item.planned_percent_complete,
                    'Variance': item.variance_percent
                }
                
                # Add Rules of Credit steps
                if item.cost_code and item.cost_code.rule_of_credit:
                    progress_data = item.get_steps_progress()
                    steps = item.cost_code.rule_of_credit.get_steps()
                    step_map = {step["name"]: step for step in steps}
                    
                    for step_name in roc_step_headers:
                        if step_name in step_map:
                            row[step_name] = progress_data.get(step_name, 0)
                        else:
                            row[step_name] = None
                
                data.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Create Excel file
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Quantities Report', index=False)
        
        output.seek(0)
        
        # Return Excel file
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f"{project.project_id_str}_quantities_report_{datetime.now().strftime('%Y%m%d')}.xlsx"
        )
    
    # Default fallback
    flash('Invalid report format', 'danger')
    return redirect(url_for('main.reports'))

@main_bp.route('/generate_progress_report')
def generate_progress_report():
    """Generate a report showing progress percentages"""
    project_id = request.args.get('project_id')
    sub_job_id = request.args.get('sub_job_id')
    level = request.args.get('level', 'project')
    report_format = request.args.get('format', 'pdf')
    
    if not project_id:
        flash('Project is required', 'danger')
        return redirect(url_for('main.reports'))
    
    project = Project.query.get_or_404(project_id)
    
    # Base query
    query = WorkItem.query.filter(WorkItem.project_id == project_id)
    
    # Apply sub job filter if provided
    if sub_job_id:
        query = query.filter(WorkItem.sub_job_id == sub_job_id)
    
    # Get all work items based on filters
    work_items = query.all()
    
    # Group data based on level
    grouped_data = {}
    if level == 'project':
        grouped_data = {project.id: work_items}
    elif level == 'sub_job':
        # Group by sub job
        sub_job_groups = defaultdict(list)
        for item in work_items:
            sub_job_groups[item.sub_job_id].append(item)
        grouped_data = dict(sub_job_groups)
    elif level == 'work_item':
        # No grouping, each work item is its own group
        grouped_data = {item.id: [item] for item in work_items}
    
    # Generate report based on format
    if report_format == 'pdf':
        # Generate PDF report
        report_title = "Progress Report"
        report_subtitle = "Progress Detail by Percentage"
        generation_date = datetime.now().strftime("%Y-%m-%d")
        
        # Create a custom template for progress report
        # For now, we'll use the hours template as a base
        html_content = render_template('report_template_hours.html',
                                      report_title=report_title,
                                      report_subtitle=report_subtitle,
                                      project=project,
                                      grouped_data=grouped_data,
                                      group_by=level,
                                      max_steps=0,  # No steps for progress report
                                      roc_step_headers=[],
                                      generation_date=generation_date)
        
        # Convert HTML to PDF
        pdf = HTML(string=html_content).write_pdf()
        
        # Create response
        response = BytesIO(pdf)
        
        # Return PDF file
        return send_file(
            response,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{project.project_id_str}_progress_report_{datetime.now().strftime('%Y%m%d')}.pdf"
        )
    
    elif report_format == 'excel':
        # Generate Excel report
        # Create a pandas DataFrame
        data = []
        for group_key, items in grouped_data.items():
            for item in items:
                row = {
                    'Work Item': item.work_item_id_str,
                    'Description': item.description,
                    'UoM': item.unit_of_measure,
                    'Budgeted Hours': item.budgeted_man_hours,
                    'Earned Hours': item.earned_man_hours,
                    'Actual % Complete': item.percent_complete_hours,
                    'Planned % Complete': item.planned_percent_complete,
                    'Variance': item.variance_percent,
                    'Status': dict(STATUS_CHOICES).get(item.status, 'Unknown')
                }
                
                # Add planned dates if available
                if item.planned_start_date:
                    row['Planned Start'] = item.planned_start_date.strftime('%Y-%m-%d')
                else:
                    row['Planned Start'] = 'Not Set'
                    
                if item.planned_end_date:
                    row['Planned End'] = item.planned_end_date.strftime('%Y-%m-%d')
                else:
                    row['Planned End'] = 'Not Set'
                    
                # Add actual dates if available
                if item.actual_start_date:
                    row['Actual Start'] = item.actual_start_date.strftime('%Y-%m-%d')
                else:
                    row['Actual Start'] = 'Not Started'
                    
                if item.actual_end_date:
                    row['Actual End'] = item.actual_end_date.strftime('%Y-%m-%d')
                else:
                    row['Actual End'] = 'Not Completed'
                
                data.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Create Excel file
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Progress Report', index=False)
        
        output.seek(0)
        
        # Return Excel file
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f"{project.project_id_str}_progress_report_{datetime.now().strftime('%Y%m%d')}.xlsx"
        )
    
    # Default fallback
    flash('Invalid report format', 'danger')
    return redirect(url_for('main.reports'))

@main_bp.route('/generate_rules_report')
def generate_rules_report():
    """Generate a report showing Rules of Credit steps and progress"""
    project_id = request.args.get('project_id')
    sub_job_id = request.args.get('sub_job_id')
    report_format = request.args.get('format', 'pdf')
    
    if not project_id:
        flash('Project is required', 'danger')
        return redirect(url_for('main.reports'))
    
    project = Project.query.get_or_404(project_id)
    
    # Base query
    query = WorkItem.query.filter(WorkItem.project_id == project_id)
    
    # Apply sub job filter if provided
    if sub_job_id:
        query = query.filter(WorkItem.sub_job_id == sub_job_id)
    
    # Get all work items based on filters
    work_items = query.all()
    
    # Group by cost code
    cost_code_groups = defaultdict(list)
    for item in work_items:
        cost_code_groups[item.cost_code_id].append(item)
    grouped_data = dict(cost_code_groups)
    
    # Get all unique Rules of Credit steps
    all_steps = []
    for item in work_items:
        if item.cost_code and item.cost_code.rule_of_credit:
            steps = item.cost_code.rule_of_credit.get_steps()
            for step in steps:
                step_name = step.get('name')
                if step_name not in all_steps:
                    all_steps.append(step_name)
    
    # Limit to 7 steps as per requirements
    max_steps = min(len(all_steps), 7)
    roc_step_headers = all_steps[:max_steps]
    
    # Generate report based on format
    if report_format == 'pdf':
        # Generate PDF report
        report_title = "Rules of Credit Report"
        report_subtitle = "Progress Detail by Rules of Credit"
        generation_date = datetime.now().strftime("%Y-%m-%d")
        
        # Render HTML template
        html_content = render_template('report_template_hours.html',
                                      report_title=report_title,
                                      report_subtitle=report_subtitle,
                                      project=project,
                                      grouped_data=grouped_data,
                                      group_by="cost_code",
                                      max_steps=max_steps,
                                      roc_step_headers=roc_step_headers,
                                      generation_date=generation_date)
        
        # Convert HTML to PDF
        pdf = HTML(string=html_content).write_pdf()
        
        # Create response
        response = BytesIO(pdf)
        
        # Return PDF file
        return send_file(
            response,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{project.project_id_str}_rules_report_{datetime.now().strftime('%Y%m%d')}.pdf"
        )
    
    elif report_format == 'excel':
        # Generate Excel report
        # Create a pandas DataFrame
        data = []
        for cost_code_id, items in grouped_data.items():
            cost_code = CostCode.query.get(cost_code_id)
            rule = None
            if cost_code and cost_code.rule_of_credit_id:
                rule = RuleOfCredit.query.get(cost_code.rule_of_credit_id)
            
            for item in items:
                row = {
                    'Cost Code': cost_code.cost_code_id_str if cost_code else '',
                    'Rule of Credit': rule.name if rule else '',
                    'Work Item': item.work_item_id_str,
                    'Description': item.description,
                    'UoM': item.unit_of_measure,
                    'Budgeted Hours': item.budgeted_man_hours,
                    'Earned Hours': item.earned_man_hours,
                    '% Complete': item.percent_complete_hours,
                    'Planned % Complete': item.planned_percent_complete,
                    'Variance': item.variance_percent
                }
                
                # Add Rules of Credit steps
                if rule:
                    progress_data = item.get_steps_progress()
                    steps = rule.get_steps()
                    step_map = {step["name"]: step for step in steps}
                    
                    for step_name in roc_step_headers:
                        if step_name in step_map:
                            row[step_name] = progress_data.get(step_name, 0)
                        else:
                            row[step_name] = None
                
                data.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Create Excel file
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Rules of Credit Report', index=False)
        
        output.seek(0)
        
        # Return Excel file
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f"{project.project_id_str}_rules_report_{datetime.now().strftime('%Y%m%d')}.xlsx"
        )
    
    # Default fallback
    flash('Invalid report format', 'danger')
    return redirect(url_for('main.reports'))

# ===== API ROUTES =====

@main_bp.route('/api/project/<int:project_id>/sub_jobs')
def api_get_project_sub_jobs(project_id):
    """API endpoint to get sub jobs for a project"""
    sub_jobs = SubJob.query.filter_by(project_id=project_id).all()
    return jsonify([{
        'id': sub_job.id,
        'sub_job_id_str': sub_job.sub_job_id_str,
        'name': sub_job.name
    } for sub_job in sub_jobs])

@main_bp.route('/api/cost_code/<int:cost_code_id>/rule_of_credit')
def api_get_cost_code_rule(cost_code_id):
    """API endpoint to get rule of credit for a cost code"""
    cost_code = CostCode.query.get_or_404(cost_code_id)
    
    if not cost_code.rule_of_credit_id:
        return jsonify({'error': 'No rule of credit associated with this cost code'})
    
    rule = RuleOfCredit.query.get(cost_code.rule_of_credit_id)
    if not rule:
        return jsonify({'error': 'Rule of credit not found'})
    
    return jsonify({
        'id': rule.id,
        'name': rule.name,
        'steps': rule.get_steps()
    })

@main_bp.route('/api/work_item/<int:work_item_id>/progress')
def api_get_work_item_progress(work_item_id):
    """API endpoint to get progress data for a work item"""
    work_item = WorkItem.query.get_or_404(work_item_id)
    
    # Calculate variance if needed
    if work_item.planned_percent_complete is not None:
        work_item.calculate_variance()
    
    return jsonify({
        'id': work_item.id,
        'work_item_id_str': work_item.work_item_id_str,
        'description': work_item.description,
        'status': work_item.status,
        'percent_complete_hours': work_item.percent_complete_hours,
        'percent_complete_quantity': work_item.percent_complete_quantity,
        'planned_percent_complete': work_item.planned_percent_complete,
        'variance_percent': work_item.variance_percent,
        'is_behind_schedule': work_item.is_behind_schedule(),
        'is_ahead_schedule': work_item.is_ahead_schedule(),
        'planned_start_date': work_item.planned_start_date.strftime('%Y-%m-%d') if work_item.planned_start_date else None,
        'planned_end_date': work_item.planned_end_date.strftime('%Y-%m-%d') if work_item.planned_end_date else None,
        'actual_start_date': work_item.actual_start_date.strftime('%Y-%m-%d') if work_item.actual_start_date else None,
        'actual_end_date': work_item.actual_end_date.strftime('%Y-%m-%d') if work_item.actual_end_date else None,
        'interval_type': work_item.interval_type
    })

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
        for i in range(len(step_names)):
            if step_names[i]:  # Only add if name is not empty
                steps.append({
                    'name': step_names[i],
                    'weight': float(step_weights[i]) if step_weights[i] else 0
                })
        
        # Create new rule of credit
        new_rule = RuleOfCredit(
            name=name,
            description=description
        )
        new_rule.set_steps(steps)
        
        db.session.add(new_rule)
        db.session.commit()
        
        flash('Rule of Credit added successfully!', 'success')
        return redirect(url_for('main.list_rules_of_credit'))
    
    return render_template('add_rule_of_credit.html')

@main_bp.route('/edit_rule_of_credit/<int:rule_id>', methods=['GET', 'POST'])
def edit_rule_of_credit(rule_id):
    """Edit an existing rule of credit"""
    rule = RuleOfCredit.query.get_or_404(rule_id)
    
    if request.method == 'POST':
        rule.name = request.form.get('name')
        rule.description = request.form.get('description')
        
        # Get step data
        step_names = request.form.getlist('step_name[]')
        step_weights = request.form.getlist('step_weight[]')
        
        # Create steps list
        steps = []
        for i in range(len(step_names)):
            if step_names[i]:  # Only add if name is not empty
                steps.append({
                    'name': step_names[i],
                    'weight': float(step_weights[i]) if step_weights[i] else 0
                })
        
        rule.set_steps(steps)
        db.session.commit()
        
        flash('Rule of Credit updated successfully!', 'success')
        return redirect(url_for('main.list_rules_of_credit'))
    
    steps = rule.get_steps()
    return render_template('edit_rule_of_credit.html', rule=rule, steps=steps)

@main_bp.route('/delete_rule_of_credit/<int:rule_id>', methods=['POST'])
def delete_rule_of_credit(rule_id):
    """Delete a rule of credit"""
    rule = RuleOfCredit.query.get_or_404(rule_id)
    
    # Check if rule is used by any cost codes
    cost_codes = CostCode.query.filter_by(rule_of_credit_id=rule_id).all()
    if cost_codes:
        flash('Cannot delete rule as it is used by cost codes. Remove the association first.', 'danger')
        return redirect(url_for('main.list_rules_of_credit'))
    
    db.session.delete(rule)
    db.session.commit()
    
    flash('Rule of Credit deleted successfully!', 'success')
    return redirect(url_for('main.list_rules_of_credit'))

# ===== COST CODES ROUTES =====

@main_bp.route('/cost_codes')
def cost_codes():
    """List all cost codes with filtering options"""
    # Get filter parameters
    project_id = request.args.get('project', 'all')
    discipline = request.args.get('discipline', 'all')
    
    # Base query
    query = CostCode.query
    
    # Apply filters
    if project_id != 'all':
        query = query.filter(CostCode.project_id == project_id)
    
    if discipline != 'all':
        query = query.filter(CostCode.discipline == discipline)
    
    # Get all cost codes based on filters
    cost_codes = query.all()
    
    # Get all projects for dropdown
    projects = Project.query.all()
    
    # Get all disciplines for dropdown
    disciplines = DISCIPLINE_CHOICES
    
    return render_template('cost_codes.html', 
                          cost_codes=cost_codes, 
                          projects=projects,
                          disciplines=disciplines,
                          selected_project_id=int(project_id) if project_id != 'all' else 'all',
                          selected_discipline=discipline)

@main_bp.route('/add_cost_code', methods=['GET', 'POST'])
def add_cost_code():
    """Add a new cost code"""
    if request.method == 'POST':
        cost_code_id_str = request.form.get('cost_code_id_str')
        description = request.form.get('description')
        discipline = request.form.get('discipline')
        project_id = request.form.get('project_id')
        rule_of_credit_id = request.form.get('rule_of_credit_id') or None
        
        new_cost_code = CostCode(
            cost_code_id_str=cost_code_id_str,
            description=description,
            discipline=discipline,
            project_id=project_id,
            rule_of_credit_id=rule_of_credit_id
        )
        
        db.session.add(new_cost_code)
        db.session.commit()
        
        flash('Cost Code added successfully!', 'success')
        return redirect(url_for('main.cost_codes'))
    
    projects = Project.query.all()
    rules = RuleOfCredit.query.all()
    disciplines = DISCIPLINE_CHOICES
    
    return render_template('add_cost_code.html', 
                          projects=projects, 
                          rules=rules, 
                          disciplines=disciplines)

@main_bp.route('/edit_cost_code/<int:cost_code_id>', methods=['GET', 'POST'])
def edit_cost_code(cost_code_id):
    """Edit an existing cost code"""
    cost_code = CostCode.query.get_or_404(cost_code_id)
    
    if request.method == 'POST':
        cost_code.cost_code_id_str = request.form.get('cost_code_id_str')
        cost_code.description = request.form.get('description')
        cost_code.discipline = request.form.get('discipline')
        cost_code.project_id = request.form.get('project_id')
        cost_code.rule_of_credit_id = request.form.get('rule_of_credit_id') or None
        
        db.session.commit()
        
        flash('Cost Code updated successfully!', 'success')
        return redirect(url_for('main.cost_codes'))
    
    projects = Project.query.all()
    rules = RuleOfCredit.query.all()
    disciplines = DISCIPLINE_CHOICES
    
    return render_template('edit_cost_code.html', 
                          cost_code=cost_code,
                          projects=projects, 
                          rules=rules, 
                          disciplines=disciplines)

@main_bp.route('/delete_cost_code/<int:cost_code_id>', methods=['POST'])
def delete_cost_code(cost_code_id):
    """Delete a cost code"""
    cost_code = CostCode.query.get_or_404(cost_code_id)
    
    # Check if cost code is used by any work items
    work_items = WorkItem.query.filter_by(cost_code_id=cost_code_id).all()
    if work_items:
        flash('Cannot delete cost code as it is used by work items. Delete the work items first.', 'danger')
        return redirect(url_for('main.cost_codes'))
    
    db.session.delete(cost_code)
    db.session.commit()
    
    flash('Cost Code deleted successfully!', 'success')
    return redirect(url_for('main.cost_codes'))

# ===== EXPORT ROUTES =====

@main_bp.route('/export/work_items')
def export_work_items():
    """Export work items to Excel"""
    # Get filter parameters
    project_id = request.args.get('project', 'all')
    sub_job_id = request.args.get('sub_job', 'all')
    search = request.args.get('search', '')
    cost_code_id = request.args.get('cost_code', 'all')
    status = request.args.get('status', 'all')
    
    # Base query
    query = WorkItem.query
    
    # Apply filters
    if project_id != 'all':
        query = query.filter(WorkItem.project_id == project_id)
    
    if sub_job_id != 'all':
        query = query.filter(WorkItem.sub_job_id == sub_job_id)
    
    if cost_code_id != 'all':
        query = query.filter(WorkItem.cost_code_id == cost_code_id)
    
    if status != 'all':
        query = query.filter(WorkItem.status == status)
    
    # Get all work items based on filters
    work_items = query.all()
    
    # Apply search filter (this is done in Python since it's more complex)
    if search:
        search = search.lower()
        work_items = [item for item in work_items if 
                     search in item.work_item_id_str.lower() or 
                     search in item.description.lower()]
    
    # Create a pandas DataFrame
    data = []
    for item in work_items:
        data.append({
            'Work Item ID': item.work_item_id_str,
            'Description': item.description,
            'Project': item.project.name if item.project else '',
            'Sub Job': item.sub_job.name if item.sub_job else '',
            'Cost Code': item.cost_code.cost_code_id_str if item.cost_code else '',
            'UoM': item.unit_of_measure,
            'Budgeted Quantity': item.budgeted_quantity,
            'Earned Quantity': item.earned_quantity,
            'Quantity % Complete': item.percent_complete_quantity,
            'Budgeted Hours': item.budgeted_man_hours,
            'Earned Hours': item.earned_man_hours,
            'Hours % Complete': item.percent_complete_hours,
            'Status': item.status,
            'Planned % Complete': item.planned_percent_complete,
            'Variance': item.variance_percent,
            'Planned Start Date': item.planned_start_date.strftime('%Y-%m-%d') if item.planned_start_date else 'Not Set',
            'Planned End Date': item.planned_end_date.strftime('%Y-%m-%d') if item.planned_end_date else 'Not Set',
            'Actual Start Date': item.actual_start_date.strftime('%Y-%m-%d') if item.actual_start_date else 'Not Started',
            'Actual End Date': item.actual_end_date.strftime('%Y-%m-%d') if item.actual_end_date else 'Not Completed',
            'Interval Type': item.interval_type if item.interval_type else 'weeks'
        })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Create Excel file
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Work Items', index=False)
    
    output.seek(0)
    
    # Return Excel file
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f"work_items_export_{datetime.now().strftime('%Y%m%d')}.xlsx"
    )
