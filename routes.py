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
    """Dashboard settings page"""
    return render_template('settings.html')

@main_bp.route('/api/project/<int:project_id>/dashboard')
def project_dashboard_data(project_id):
    """API endpoint to get dashboard data for a specific project"""
    try:
        project = Project.query.get_or_404(project_id)
        work_items = WorkItem.query.filter_by(project_id=project_id).all()
        
        # Calculate project-level totals
        total_budgeted_hours = sum(item.budgeted_man_hours or 0 for item in work_items)
        total_earned_hours = sum(item.earned_man_hours or 0 for item in work_items)
        total_budgeted_quantity = sum(item.budgeted_quantity or 0 for item in work_items)
        total_earned_quantity = sum(item.earned_quantity or 0 for item in work_items)
        
        # Calculate overall progress percentage
        overall_progress = 0
        if total_budgeted_hours > 0:
            overall_progress = (total_earned_hours / total_budgeted_hours) * 100
        
        # Get discipline distribution for quantity
        disciplines = {}
        for item in work_items:
            if item.cost_code and item.cost_code.discipline:
                discipline = item.cost_code.discipline
                if discipline not in disciplines:
                    disciplines[discipline] = {
                        'budgeted': 0,
                        'earned': 0
                    }
                disciplines[discipline]['budgeted'] += item.budgeted_quantity or 0
                disciplines[discipline]['earned'] += item.earned_quantity or 0
        
        # Format for quantity distribution chart
        quantity_distribution = {
            'labels': list(disciplines.keys()),
            'budgeted': [disciplines[d]['budgeted'] for d in disciplines],
            'earned': [disciplines[d]['earned'] for d in disciplines]
        }
        
        # Calculate progress histogram
        progress_bins = [0] * 10  # 10 bins for 0-10%, 11-20%, etc.
        for item in work_items:
            if item.budgeted_man_hours and item.budgeted_man_hours > 0:
                progress = (item.earned_man_hours or 0) / item.budgeted_man_hours * 100
                bin_index = min(9, int(progress / 10))  # Ensure it fits in our 10 bins
                progress_bins[bin_index] += 1
        
        # Mock data for SPI chart (would be calculated from actual data in production)
        spi_data = {
            'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            'values': [0.95, 0.98, 1.02, 1.05, 1.03, 1.01]
        }
        
        # Mock data for manpower distribution (would be calculated from actual data)
        manpower_distribution = {
            'labels': ['Electrical', 'Mechanical', 'Civil', 'Instrumentation'],
            'values': [30, 25, 20, 25]
        }
        
        # Mock data for budget by phase (would be calculated from actual data)
        budget_by_phase = {
            'labels': ['Engineering', 'Procurement', 'Construction', 'Commissioning'],
            'values': [15, 25, 45, 15]
        }
        
        # Return all dashboard data
        return jsonify({
            'actualProgress': overall_progress,
            'plannedProgress': 80.0,  # Mock data
            'weeklyActual': 5.0,  # Mock data
            'weeklyPlanned': 5.5,  # Mock data
            'overallProgress': overall_progress,
            'quantityDistribution': quantity_distribution,
            'progressHistogram': progress_bins,
            'spiData': spi_data,
            'manpowerDistribution': manpower_distribution,
            'budgetByPhase': budget_by_phase
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/project/<int:project_id>/planned-progress', methods=['POST'])
def update_planned_progress(project_id):
    """API endpoint to update planned progress for a project"""
    try:
        data = request.json
        percentage = data.get('percentage')
        interval_type = data.get('intervalType')
        
        # In a real implementation, this would save to the database
        # For now, we'll just return success
        
        return jsonify({'success': True})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

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
                    'name': step_names[i],
                    'weight': weight
                })
                total_weight += weight
        
        # Normalize weights if total is not 100
        if total_weight != 100 and total_weight > 0:
            for step in steps:
                step['weight'] = (step['weight'] / total_weight) * 100
        
        # Create new rule of credit
        new_rule = RuleOfCredit(
            name=name,
            description=description,
            steps=json.dumps(steps)
        )
        
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
        total_weight = 0
        
        for i in range(len(step_names)):
            if step_names[i].strip():  # Only add non-empty steps
                weight = float(step_weights[i]) if step_weights[i] else 0
                steps.append({
                    'name': step_names[i],
                    'weight': weight
                })
                total_weight += weight
        
        # Normalize weights if total is not 100
        if total_weight != 100 and total_weight > 0:
            for step in steps:
                step['weight'] = (step['weight'] / total_weight) * 100
        
        rule.steps = json.dumps(steps)
        db.session.commit()
        
        flash('Rule of Credit updated successfully!', 'success')
        return redirect(url_for('main.list_rules_of_credit'))
    
    # Parse steps for display
    steps = json.loads(rule.steps) if rule.steps else []
    
    return render_template('edit_rule_of_credit.html', rule=rule, steps=steps)

@main_bp.route('/delete_rule_of_credit/<int:rule_id>', methods=['POST'])
def delete_rule_of_credit(rule_id):
    """Delete a rule of credit"""
    rule = RuleOfCredit.query.get_or_404(rule_id)
    
    # Check if rule is used by any work items
    work_items = WorkItem.query.filter_by(rule_of_credit_id=rule_id).all()
    if work_items:
        flash('Cannot delete rule of credit as it is used by work items.', 'danger')
        return redirect(url_for('main.list_rules_of_credit'))
    
    db.session.delete(rule)
    db.session.commit()
    
    flash('Rule of Credit deleted successfully!', 'success')
    return redirect(url_for('main.list_rules_of_credit'))

# ===== COST CODE ROUTES =====

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
        discipline = request.form.get('discipline')
        cost_code_id_str = request.form.get('cost_code_id_str') or f"CC-{uuid.uuid4().hex[:8].upper()}"
        
        new_cost_code = CostCode(
            code=code,
            description=description,
            discipline=discipline,
            cost_code_id_str=cost_code_id_str
        )
        db.session.add(new_cost_code)
        db.session.commit()
        
        flash('Cost Code added successfully!', 'success')
        return redirect(url_for('main.list_cost_codes'))
    
    return render_template('add_cost_code.html', disciplines=DISCIPLINE_CHOICES)

@main_bp.route('/edit_cost_code/<int:cost_code_id>', methods=['GET', 'POST'])
def edit_cost_code(cost_code_id):
    """Edit an existing cost code"""
    cost_code = CostCode.query.get_or_404(cost_code_id)
    
    if request.method == 'POST':
        cost_code.code = request.form.get('code')
        cost_code.description = request.form.get('description')
        cost_code.discipline = request.form.get('discipline')
        cost_code.cost_code_id_str = request.form.get('cost_code_id_str')
        
        db.session.commit()
        flash('Cost Code updated successfully!', 'success')
        return redirect(url_for('main.list_cost_codes'))
    
    return render_template('edit_cost_code.html', cost_code=cost_code, disciplines=DISCIPLINE_CHOICES)

@main_bp.route('/delete_cost_code/<int:cost_code_id>', methods=['POST'])
def delete_cost_code(cost_code_id):
    """Delete a cost code"""
    cost_code = CostCode.query.get_or_404(cost_code_id)
    
    # Check if cost code is used by any work items
    work_items = WorkItem.query.filter_by(cost_code_id=cost_code_id).all()
    if work_items:
        flash('Cannot delete cost code as it is used by work items.', 'danger')
        return redirect(url_for('main.list_cost_codes'))
    
    db.session.delete(cost_code)
    db.session.commit()
    
    flash('Cost Code deleted successfully!', 'success')
    return redirect(url_for('main.list_cost_codes'))

# ===== WORK ITEM ROUTES =====

@main_bp.route('/work_items')
def work_items():
    """List all work items with filtering"""
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
            query = query.filter_by(project_id=project_id)
        if sub_job_id:
            query = query.filter_by(sub_job_id=sub_job_id)
        if search:
            query = query.filter(WorkItem.description.ilike(f'%{search}%'))
        if discipline:
            query = query.join(CostCode).filter(CostCode.discipline == discipline)
        if status:
            if status == 'not_started':
                query = query.filter(WorkItem.percent_complete_hours == 0)
            elif status == 'in_progress':
                query = query.filter(WorkItem.percent_complete_hours > 0, WorkItem.percent_complete_hours < 100)
            elif status == 'completed':
                query = query.filter(WorkItem.percent_complete_hours == 100)
        
        # Apply sorting
        if sort_by:
            if sort_by == 'id':
                query = query.order_by(WorkItem.work_item_id_str)
            elif sort_by == 'description':
                query = query.order_by(WorkItem.description)
            elif sort_by == 'progress':
                query = query.order_by(WorkItem.percent_complete_hours)
            elif sort_by == 'cost_code':
                query = query.join(CostCode).order_by(CostCode.code)
        
        # Execute query
        work_items = query.all()
        
        # Get all projects and sub jobs for filters
        projects = Project.query.all()
        sub_jobs = []
        if project_id:
            sub_jobs = SubJob.query.filter_by(project_id=project_id).all()
        
        # Get all disciplines for filter
        disciplines = DISCIPLINE_CHOICES
        
        return render_template('work_items.html', 
                              work_items=work_items, 
                              projects=projects, 
                              sub_jobs=sub_jobs,
                              disciplines=disciplines)
    except Exception as e:
        flash(f'Error loading work items: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('work_items.html', work_items=[], projects=[], sub_jobs=[])

@main_bp.route('/add_work_item', methods=['GET', 'POST'])
def add_work_item():
    """Add a new work item"""
    # Get project_id and sub_job_id from query parameters if provided
    project_id = request.args.get('project_id', type=int)
    sub_job_id = request.args.get('sub_job_id', type=int)
    
    # Get all projects for dropdown
    projects = Project.query.all()
    
    # Get sub jobs based on project_id if provided
    sub_jobs = []
    if project_id:
        sub_jobs = SubJob.query.filter_by(project_id=project_id).all()
    elif sub_job_id:
        sub_job = SubJob.query.get(sub_job_id)
        if sub_job:
            project_id = sub_job.project_id
            sub_jobs = SubJob.query.filter_by(project_id=project_id).all()
    
    # Get all cost codes and rules of credit for dropdowns
    cost_codes = CostCode.query.all()
    rules_of_credit = RuleOfCredit.query.all()
    
    if request.method == 'POST':
        # Get form data
        project_id = request.form.get('project_id', type=int)
        sub_job_id = request.form.get('sub_job_id', type=int)
        work_item_id_str = request.form.get('work_item_id_str') or f"WI-{uuid.uuid4().hex[:8].upper()}"
        description = request.form.get('description')
        cost_code_id = request.form.get('cost_code_id', type=int)
        rule_of_credit_id = request.form.get('rule_of_credit_id', type=int)
        unit_of_measure = request.form.get('unit_of_measure')
        budgeted_quantity = request.form.get('budgeted_quantity', type=float)
        budgeted_man_hours = request.form.get('budgeted_man_hours', type=float)
        
        # Create new work item
        new_work_item = WorkItem(
            project_id=project_id,
            sub_job_id=sub_job_id,
            work_item_id_str=work_item_id_str,
            description=description,
            cost_code_id=cost_code_id,
            rule_of_credit_id=rule_of_credit_id,
            unit_of_measure=unit_of_measure,
            budgeted_quantity=budgeted_quantity,
            budgeted_man_hours=budgeted_man_hours,
            percent_complete_hours=0,
            percent_complete_quantity=0,
            earned_man_hours=0,
            earned_quantity=0,
            current_step=0
        )
        
        db.session.add(new_work_item)
        db.session.commit()
        
        flash('Work Item added successfully!', 'success')
        
        # Redirect based on context
        if sub_job_id:
            return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))
        elif project_id:
            return redirect(url_for('main.view_project', project_id=project_id))
        else:
            return redirect(url_for('main.work_items'))
    
    return render_template('add_work_item.html', 
                          projects=projects, 
                          sub_jobs=sub_jobs, 
                          cost_codes=cost_codes,
                          rules_of_credit=rules_of_credit,
                          project_id=project_id,
                          sub_job_id=sub_job_id)

@main_bp.route('/view_work_item/<int:work_item_id>')
def view_work_item(work_item_id):
    """View a specific work item"""
    work_item = WorkItem.query.get_or_404(work_item_id)
    
    # Get rule of credit steps if available
    steps = []
    if work_item.rule_of_credit and work_item.rule_of_credit.steps:
        steps = json.loads(work_item.rule_of_credit.steps)
    
    return render_template('view_work_item.html', work_item=work_item, steps=steps)

@main_bp.route('/edit_work_item/<int:work_item_id>', methods=['GET', 'POST'])
def edit_work_item(work_item_id):
    """Edit an existing work item"""
    work_item = WorkItem.query.get_or_404(work_item_id)
    
    # Get all projects, sub jobs, cost codes, and rules of credit for dropdowns
    projects = Project.query.all()
    sub_jobs = SubJob.query.filter_by(project_id=work_item.project_id).all()
    cost_codes = CostCode.query.all()
    rules_of_credit = RuleOfCredit.query.all()
    
    if request.method == 'POST':
        # Update work item data
        work_item.project_id = request.form.get('project_id', type=int)
        work_item.sub_job_id = request.form.get('sub_job_id', type=int)
        work_item.work_item_id_str = request.form.get('work_item_id_str')
        work_item.description = request.form.get('description')
        work_item.cost_code_id = request.form.get('cost_code_id', type=int)
        work_item.rule_of_credit_id = request.form.get('rule_of_credit_id', type=int)
        work_item.unit_of_measure = request.form.get('unit_of_measure')
        work_item.budgeted_quantity = request.form.get('budgeted_quantity', type=float)
        work_item.budgeted_man_hours = request.form.get('budgeted_man_hours', type=float)
        
        db.session.commit()
        flash('Work Item updated successfully!', 'success')
        return redirect(url_for('main.view_work_item', work_item_id=work_item.id))
    
    return render_template('edit_work_item.html', 
                          work_item=work_item,
                          projects=projects, 
                          sub_jobs=sub_jobs, 
                          cost_codes=cost_codes,
                          rules_of_credit=rules_of_credit)

@main_bp.route('/update_work_item_progress/<int:work_item_id>', methods=['GET', 'POST'])
def update_work_item_progress(work_item_id):
    """Update progress of a work item"""
    work_item = WorkItem.query.get_or_404(work_item_id)
    
    # Get rule of credit steps if available
    steps = []
    if work_item.rule_of_credit and work_item.rule_of_credit.steps:
        steps = json.loads(work_item.rule_of_credit.steps)
    
    if request.method == 'POST':
        # Get progress data
        percent_complete = request.form.get('percent_complete', type=float)
        current_step = request.form.get('current_step', type=int)
        
        # Update work item progress
        work_item.percent_complete_hours = percent_complete
        work_item.percent_complete_quantity = percent_complete
        work_item.current_step = current_step
        
        # Calculate earned values
        work_item.earned_man_hours = (work_item.budgeted_man_hours or 0) * (percent_complete / 100)
        work_item.earned_quantity = (work_item.budgeted_quantity or 0) * (percent_complete / 100)
        
        db.session.commit()
        flash('Work Item progress updated successfully!', 'success')
        
        # Redirect based on context
        if work_item.sub_job_id:
            return redirect(url_for('main.view_sub_job', sub_job_id=work_item.sub_job_id))
        else:
            return redirect(url_for('main.view_work_item', work_item_id=work_item.id))
    
    return render_template('update_work_item_progress.html', work_item=work_item, steps=steps)

@main_bp.route('/delete_work_item/<int:work_item_id>', methods=['POST'])
def delete_work_item(work_item_id):
    """Delete a work item"""
    work_item = WorkItem.query.get_or_404(work_item_id)
    sub_job_id = work_item.sub_job_id
    
    db.session.delete(work_item)
    db.session.commit()
    
    flash('Work Item deleted successfully!', 'success')
    
    # Redirect based on context
    if sub_job_id:
        return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))
    else:
        return redirect(url_for('main.work_items'))

# ===== REPORTS ROUTES =====

@main_bp.route('/reports')
def reports_index():
    """Reports landing page"""
    projects = Project.query.all()
    return render_template('reports_index.html', projects=projects)
