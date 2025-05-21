from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import db, Project, SubJob, CostCode, RuleOfCredit, WorkItem
from sqlalchemy import or_
from flask import current_app
import json
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import math

# Create Blueprint
main = Blueprint('main', __name__)

# Home route
@main.route('/')
def index():
    # Get counts for dashboard
    project_count = Project.query.count()
    sub_job_count = SubJob.query.count()
    work_item_count = WorkItem.query.count()
    rule_count = RuleOfCredit.query.count()
    
    # Get recent work items
    recent_work_items = WorkItem.query.order_by(WorkItem.id.desc()).limit(5).all()
    
    return render_template('index.html', 
                          project_count=project_count,
                          sub_job_count=sub_job_count,
                          work_item_count=work_item_count,
                          rule_count=rule_count,
                          recent_work_items=recent_work_items)

# Projects routes
@main.route('/projects')
def projects():
    projects = Project.query.all()
    return render_template('projects.html', projects=projects)

@main.route('/project/<int:project_id>')
def view_project(project_id):
    project = Project.query.get_or_404(project_id)
    sub_jobs = SubJob.query.filter_by(project_id=project_id).all()
    return render_template('view_project.html', project=project, sub_jobs=sub_jobs)

@main.route('/project/add', methods=['GET', 'POST'])
def add_project():
    if request.method == 'POST':
        project_id_str = request.form['project_id_str']
        name = request.form['name']
        description = request.form['description']
        
        # Check if project ID already exists
        existing_project = Project.query.filter_by(project_id_str=project_id_str).first()
        if existing_project:
            flash('Project ID already exists', 'danger')
            return render_template('add_project.html')
        
        new_project = Project(
            project_id_str=project_id_str,
            name=name,
            description=description
        )
        
        db.session.add(new_project)
        db.session.commit()
        
        flash('Project added successfully', 'success')
        return redirect(url_for('main.projects'))
    
    return render_template('add_project.html')

@main.route('/project/<int:project_id>/edit', methods=['GET', 'POST'])
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    
    if request.method == 'POST':
        project.project_id_str = request.form['project_id_str']
        project.name = request.form['name']
        project.description = request.form['description']
        
        db.session.commit()
        
        flash('Project updated successfully', 'success')
        return redirect(url_for('main.view_project', project_id=project.id))
    
    return render_template('edit_project.html', project=project)

# Sub Job routes
@main.route('/project/<int:project_id>/sub_job/add', methods=['GET', 'POST'])
def add_sub_job(project_id):
    project = Project.query.get_or_404(project_id)
    
    if request.method == 'POST':
        sub_job_id_str = request.form['sub_job_id_str']
        name = request.form['name']
        description = request.form['description']
        area = request.form['area']
        
        # Check if sub job ID already exists
        existing_sub_job = SubJob.query.filter_by(sub_job_id_str=sub_job_id_str).first()
        if existing_sub_job:
            flash('Sub Job ID already exists', 'danger')
            return render_template('add_sub_job.html', project=project)
        
        new_sub_job = SubJob(
            sub_job_id_str=sub_job_id_str,
            name=name,
            description=description,
            area=area,
            project_id=project_id
        )
        
        db.session.add(new_sub_job)
        db.session.commit()
        
        flash('Sub Job added successfully', 'success')
        return redirect(url_for('main.view_project', project_id=project_id))
    
    return render_template('add_sub_job.html', project=project)

@main.route('/sub_job/<int:sub_job_id>')
def view_sub_job(sub_job_id):
    sub_job = SubJob.query.get_or_404(sub_job_id)
    project = Project.query.get(sub_job.project_id)
    work_items = WorkItem.query.filter_by(sub_job_id=sub_job_id).all()
    
    return render_template('view_sub_job.html', sub_job=sub_job, project=project, work_items=work_items)

@main.route('/sub_job/<int:sub_job_id>/edit', methods=['GET', 'POST'])
def edit_sub_job(sub_job_id):
    sub_job = SubJob.query.get_or_404(sub_job_id)
    project = Project.query.get(sub_job.project_id)
    
    if request.method == 'POST':
        sub_job.sub_job_id_str = request.form['sub_job_id_str']
        sub_job.name = request.form['name']
        sub_job.description = request.form['description']
        sub_job.area = request.form['area']
        
        db.session.commit()
        
        flash('Sub Job updated successfully', 'success')
        return redirect(url_for('main.view_sub_job', sub_job_id=sub_job.id))
    
    return render_template('edit_sub_job.html', sub_job=sub_job, project=project)

# Rules of Credit routes
@main.route('/rules-of-credit')
def list_rules_of_credit():
    rules = RuleOfCredit.query.all()
    return render_template('list_rules_of_credit.html', rules=rules)

@main.route('/rule-of-credit/add', methods=['GET', 'POST'])
def add_rule_of_credit():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        
        # Process steps
        steps = []
        step_names = request.form.getlist('step_name[]')
        step_weights = request.form.getlist('step_weight[]')
        
        total_weight = 0
        for i in range(len(step_names)):
            if step_names[i].strip():  # Only add non-empty steps
                weight = float(step_weights[i]) if step_weights[i] else 0
                steps.append({
                    "name": step_names[i].strip(),
                    "weight": weight
                })
                total_weight += weight
        
        # Validate total weight is 100%
        if not math.isclose(total_weight, 100, abs_tol=0.01):
            flash('Total weight must equal 100%', 'danger')
            return render_template('add_rule_of_credit.html', 
                                  name=name, 
                                  description=description, 
                                  steps=steps)
        
        new_rule = RuleOfCredit(
            name=name,
            description=description
        )
        new_rule.set_steps(steps)
        
        db.session.add(new_rule)
        db.session.commit()
        
        flash('Rule of Credit added successfully', 'success')
        return redirect(url_for('main.list_rules_of_credit'))
    
    return render_template('add_rule_of_credit.html')

@main.route('/rule-of-credit/<int:rule_id>/edit', methods=['GET', 'POST'])
def edit_rule_of_credit(rule_id):
    rule = RuleOfCredit.query.get_or_404(rule_id)
    
    if request.method == 'POST':
        rule.name = request.form['name']
        rule.description = request.form['description']
        
        # Process steps
        steps = []
        step_names = request.form.getlist('step_name[]')
        step_weights = request.form.getlist('step_weight[]')
        
        total_weight = 0
        for i in range(len(step_names)):
            if step_names[i].strip():  # Only add non-empty steps
                weight = float(step_weights[i]) if step_weights[i] else 0
                steps.append({
                    "name": step_names[i].strip(),
                    "weight": weight
                })
                total_weight += weight
        
        # Validate total weight is 100%
        if not math.isclose(total_weight, 100, abs_tol=0.01):
            flash('Total weight must equal 100%', 'danger')
            return render_template('edit_rule_of_credit.html', 
                                  rule=rule, 
                                  steps=rule.get_steps())
        
        rule.set_steps(steps)
        db.session.commit()
        
        flash('Rule of Credit updated successfully', 'success')
        return redirect(url_for('main.list_rules_of_credit'))
    
    return render_template('edit_rule_of_credit.html', rule=rule, steps=rule.get_steps())

# Cost Code routes
@main.route('/cost-codes')
def list_cost_codes():
    project_id = request.args.get('project_id', type=int)
    discipline = request.args.get('discipline')
    
    query = CostCode.query
    
    if project_id:
        query = query.filter_by(project_id=project_id)
    
    if discipline:
        query = query.filter_by(discipline=discipline)
    
    cost_codes = query.all()
    projects = Project.query.all()
    
    return render_template('list_cost_codes.html', 
                          cost_codes=cost_codes, 
                          projects=projects,
                          disciplines=DISCIPLINE_CHOICES,
                          selected_project_id=project_id,
                          selected_discipline=discipline)

@main.route('/cost-code/add', methods=['GET', 'POST'])
def add_cost_code():
    if request.method == 'POST':
        cost_code_id_str = request.form['cost_code_id_str']
        description = request.form['description']
        discipline = request.form['discipline']
        project_id = request.form['project_id']
        rule_of_credit_id = request.form['rule_of_credit_id'] if request.form['rule_of_credit_id'] else None
        
        # Check if cost code ID already exists
        existing_cost_code = CostCode.query.filter_by(cost_code_id_str=cost_code_id_str).first()
        if existing_cost_code:
            flash('Cost Code ID already exists', 'danger')
            projects = Project.query.all()
            rules = RuleOfCredit.query.all()
            return render_template('add_cost_code.html', 
                                  projects=projects, 
                                  rules=rules, 
                                  disciplines=DISCIPLINE_CHOICES)
        
        new_cost_code = CostCode(
            cost_code_id_str=cost_code_id_str,
            description=description,
            discipline=discipline,
            project_id=project_id,
            rule_of_credit_id=rule_of_credit_id
        )
        
        db.session.add(new_cost_code)
        db.session.commit()
        
        flash('Cost Code added successfully', 'success')
        return redirect(url_for('main.list_cost_codes'))
    
    projects = Project.query.all()
    rules = RuleOfCredit.query.all()
    
    return render_template('add_cost_code.html', 
                          projects=projects, 
                          rules=rules, 
                          disciplines=DISCIPLINE_CHOICES)

@main.route('/cost-code/<int:cost_code_id>/edit', methods=['GET', 'POST'])
def edit_cost_code(cost_code_id):
    cost_code = CostCode.query.get_or_404(cost_code_id)
    
    if request.method == 'POST':
        cost_code.cost_code_id_str = request.form['cost_code_id_str']
        cost_code.description = request.form['description']
        cost_code.discipline = request.form['discipline']
        cost_code.project_id = request.form['project_id']
        cost_code.rule_of_credit_id = request.form['rule_of_credit_id'] if request.form['rule_of_credit_id'] else None
        
        db.session.commit()
        
        flash('Cost Code updated successfully', 'success')
        return redirect(url_for('main.list_cost_codes'))
    
    projects = Project.query.all()
    rules = RuleOfCredit.query.all()
    
    return render_template('edit_cost_code.html', 
                          cost_code=cost_code, 
                          projects=projects, 
                          rules=rules, 
                          disciplines=DISCIPLINE_CHOICES)

# Work Items routes
@main.route('/work-items')
def work_items():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get filter parameters
    project_id = request.args.get('project_id', type=int)
    sub_job_id = request.args.get('sub_job_id', type=int)
    cost_code_id = request.args.get('cost_code_id', type=int)
    search_query = request.args.get('search', '')
    status = request.args.get('status', '')
    sort_by = request.args.get('sort_by', 'id')
    
    # Build query
    query = WorkItem.query
    
    if project_id:
        query = query.filter_by(project_id=project_id)
    
    if sub_job_id:
        query = query.filter_by(sub_job_id=sub_job_id)
    
    if cost_code_id:
        query = query.filter_by(cost_code_id=cost_code_id)
    
    if search_query:
        query = query.filter(
            or_(
                WorkItem.work_item_id_str.ilike(f'%{search_query}%'),
                WorkItem.description.ilike(f'%{search_query}%')
            )
        )
    
    if status:
        if status == 'not_started':
            query = query.filter(WorkItem.percent_complete_hours == 0)
        elif status == 'in_progress':
            query = query.filter(WorkItem.percent_complete_hours > 0, WorkItem.percent_complete_hours < 100)
        elif status == 'completed':
            query = query.filter(WorkItem.percent_complete_hours == 100)
        elif status == 'on_hold':
            # Assuming on_hold is a special case where percent_complete_hours is negative or null
            query = query.filter(or_(WorkItem.percent_complete_hours < 0, WorkItem.percent_complete_hours == None))
    
    # Apply sorting
    if sort_by == 'id':
        query = query.order_by(WorkItem.work_item_id_str)
    elif sort_by == 'description':
        query = query.order_by(WorkItem.description)
    elif sort_by == 'progress':
        query = query.order_by(WorkItem.percent_complete_hours)
    elif sort_by == 'cost_code':
        query = query.join(CostCode).order_by(CostCode.cost_code_id_str)
    
    # Paginate results
    pagination = query.paginate(page=page, per_page=per_page)
    work_items = pagination.items
    
    # Get projects and sub jobs for filters
    projects = Project.query.all()
    
    if project_id:
        sub_jobs = SubJob.query.filter_by(project_id=project_id).all()
        cost_codes = CostCode.query.filter_by(project_id=project_id).all()
    else:
        sub_jobs = []
        cost_codes = []
    
    return render_template('work_items.html',
                          work_items=work_items,
                          pagination=pagination,
                          projects=projects,
                          sub_jobs=sub_jobs,
                          cost_codes=cost_codes,
                          selected_project_id=project_id,
                          selected_sub_job_id=sub_job_id,
                          selected_cost_code_id=cost_code_id,
                          search_query=search_query,
                          status=status,
                          sort_by=sort_by)

@main.route('/work-item/add', methods=['GET', 'POST'])
def add_work_item():
    if request.method == 'POST':
        work_item_id_str = request.form['work_item_id_str']
        description = request.form['description']
        project_id = request.form['project_id']
        sub_job_id = request.form['sub_job_id']
        cost_code_id = request.form['cost_code_id']
        budgeted_quantity = float(request.form['budgeted_quantity'])
        unit_of_measure = request.form['unit_of_measure']
        budgeted_man_hours = float(request.form['budgeted_man_hours'])
        
        # Check if work item ID already exists
        existing_work_item = WorkItem.query.filter_by(work_item_id_str=work_item_id_str).first()
        if existing_work_item:
            flash('Work Item ID already exists', 'danger')
            projects = Project.query.all()
            return render_template('add_work_item.html', projects=projects)
        
        new_work_item = WorkItem(
            work_item_id_str=work_item_id_str,
            description=description,
            project_id=project_id,
            sub_job_id=sub_job_id,
            cost_code_id=cost_code_id,
            budgeted_quantity=budgeted_quantity,
            unit_of_measure=unit_of_measure,
            budgeted_man_hours=budgeted_man_hours,
            earned_man_hours=0,
            earned_quantity=0,
            percent_complete_hours=0,
            percent_complete_quantity=0
        )
        
        db.session.add(new_work_item)
        db.session.commit()
        
        flash('Work Item added successfully', 'success')
        return redirect(url_for('main.work_items'))
    
    projects = Project.query.all()
    return render_template('add_work_item.html', projects=projects)

@main.route('/work-item/<int:work_item_id>')
def view_work_item(work_item_id):
    work_item = WorkItem.query.get_or_404(work_item_id)
    project = Project.query.get(work_item.project_id)
    sub_job = SubJob.query.get(work_item.sub_job_id)
    cost_code = CostCode.query.get(work_item.cost_code_id)
    
    rule_of_credit = None
    rule_steps = []
    step_progress = {}
    
    if cost_code and cost_code.rule_of_credit_id:
        rule_of_credit = RuleOfCredit.query.get(cost_code.rule_of_credit_id)
        if rule_of_credit:
            rule_steps = rule_of_credit.get_steps()
            step_progress = work_item.get_steps_progress()
    
    return render_template('view_work_item.html',
                          work_item=work_item,
                          project=project,
                          sub_job=sub_job,
                          cost_code=cost_code,
                          rule_of_credit=rule_of_credit,
                          rule_steps=rule_steps,
                          step_progress=step_progress)

@main.route('/work-item/<int:work_item_id>/edit', methods=['GET', 'POST'])
def edit_work_item(work_item_id):
    work_item = WorkItem.query.get_or_404(work_item_id)
    
    if request.method == 'POST':
        work_item.work_item_id_str = request.form['work_item_id_str']
        work_item.description = request.form['description']
        work_item.project_id = request.form['project_id']
        work_item.sub_job_id = request.form['sub_job_id']
        work_item.cost_code_id = request.form['cost_code_id']
        work_item.budgeted_quantity = float(request.form['budgeted_quantity'])
        work_item.unit_of_measure = request.form['unit_of_measure']
        work_item.budgeted_man_hours = float(request.form['budgeted_man_hours'])
        
        db.session.commit()
        
        # Recalculate earned values based on new budgeted values
        work_item.calculate_earned_values()
        db.session.commit()
        
        flash('Work Item updated successfully', 'success')
        return redirect(url_for('main.view_work_item', work_item_id=work_item.id))
    
    projects = Project.query.all()
    sub_jobs = SubJob.query.filter_by(project_id=work_item.project_id).all()
    cost_codes = CostCode.query.filter_by(project_id=work_item.project_id).all()
    
    return render_template('edit_work_item.html',
                          work_item=work_item,
                          projects=projects,
                          sub_jobs=sub_jobs,
                          cost_codes=cost_codes)

@main.route('/work-item/<int:work_item_id>/update-progress', methods=['GET', 'POST'])
def update_work_item_progress(work_item_id):
    work_item = WorkItem.query.get_or_404(work_item_id)
    project = Project.query.get(work_item.project_id)
    sub_job = SubJob.query.get(work_item.sub_job_id)
    cost_code = CostCode.query.get(work_item.cost_code_id)
    
    rule_of_credit = None
    rule_steps = []
    step_progress = {}
    
    if cost_code and cost_code.rule_of_credit_id:
        rule_of_credit = RuleOfCredit.query.get(cost_code.rule_of_credit_id)
        if rule_of_credit:
            rule_steps = rule_of_credit.get_steps()
            step_progress = work_item.get_steps_progress()
    
    if request.method == 'POST':
        if rule_of_credit:
            # Update progress for each step
            for step in rule_steps:
                step_name = step['name']
                step_progress_key = f"step_{step_name}"
                if step_progress_key in request.form:
                    progress_value = float(request.form[step_progress_key])
                    work_item.update_progress_step(step_name, progress_value)
            
            db.session.commit()
            flash('Progress updated successfully', 'success')
            return redirect(url_for('main.view_work_item', work_item_id=work_item.id))
    
    return render_template('update_work_item_progress.html',
                          work_item=work_item,
                          project=project,
                          sub_job=sub_job,
                          cost_code=cost_code,
                          rule_of_credit=rule_of_credit,
                          rule_steps=rule_steps,
                          step_progress=step_progress)

# API routes for AJAX
@main.route('/api/project/<int:project_id>/sub_jobs')
def api_get_project_sub_jobs(project_id):
    sub_jobs = SubJob.query.filter_by(project_id=project_id).all()
    return jsonify([sub_job.serialize() for sub_job in sub_jobs])

@main.route('/api/project/<int:project_id>/cost_codes')
def api_get_project_cost_codes(project_id):
    cost_codes = CostCode.query.filter_by(project_id=project_id).all()
    return jsonify([cost_code.serialize() for cost_code in cost_codes])

# Reports routes
@main.route('/reports')
def reports_index():
    projects = Project.query.all()
    return render_template('reports.html', projects=projects)

@main.route('/reports/hours', methods=['GET', 'POST'])
def report_hours():
    if request.method == 'POST':
        project_id = request.form.get('project_id')
        sub_job_id = request.form.get('sub_job_id')
        
        if not project_id:
            flash('Please select a project', 'danger')
            projects = Project.query.all()
            return render_template('reports.html', projects=projects)
        
        project = Project.query.get(project_id)
        
        if sub_job_id:
            sub_job = SubJob.query.get(sub_job_id)
            work_items = WorkItem.query.filter_by(sub_job_id=sub_job_id).all()
            report_title = f"Sub Job: {sub_job.sub_job_id_str} - {sub_job.name}"
        else:
            sub_job = None
            work_items = WorkItem.query.filter_by(project_id=project_id).all()
            report_title = f"Project: {project.project_id_str} - {project.name}"
        
        # Group work items by cost code
        work_items_by_cost_code = {}
        for work_item in work_items:
            cost_code = CostCode.query.get(work_item.cost_code_id)
            if cost_code.id not in work_items_by_cost_code:
                work_items_by_cost_code[cost_code.id] = {
                    'cost_code': cost_code,
                    'work_items': []
                }
            work_items_by_cost_code[cost_code.id]['work_items'].append(work_item)
        
        # Calculate totals
        total_budgeted_hours = sum(wi.budgeted_man_hours for wi in work_items)
        total_earned_hours = sum(wi.earned_man_hours for wi in work_items)
        total_percent_complete = (total_earned_hours / total_budgeted_hours * 100) if total_budgeted_hours > 0 else 0
        
        return render_template('report_template_hours.html',
                              project=project,
                              sub_job=sub_job,
                              report_title=report_title,
                              work_items_by_cost_code=work_items_by_cost_code,
                              total_budgeted_hours=total_budgeted_hours,
                              total_earned_hours=total_earned_hours,
                              total_percent_complete=total_percent_complete,
                              report_date=datetime.now().strftime('%Y-%m-%d'))
    
    return redirect(url_for('main.reports_index'))

@main.route('/reports/quantities', methods=['GET', 'POST'])
def report_quantities():
    if request.method == 'POST':
        project_id = request.form.get('project_id')
        sub_job_id = request.form.get('sub_job_id')
        
        if not project_id:
            flash('Please select a project', 'danger')
            projects = Project.query.all()
            return render_template('reports.html', projects=projects)
        
        project = Project.query.get(project_id)
        
        if sub_job_id:
            sub_job = SubJob.query.get(sub_job_id)
            work_items = WorkItem.query.filter_by(sub_job_id=sub_job_id).all()
            report_title = f"Sub Job: {sub_job.sub_job_id_str} - {sub_job.name}"
        else:
            sub_job = None
            work_items = WorkItem.query.filter_by(project_id=project_id).all()
            report_title = f"Project: {project.project_id_str} - {project.name}"
        
        # Group work items by cost code
        work_items_by_cost_code = {}
        for work_item in work_items:
            cost_code = CostCode.query.get(work_item.cost_code_id)
            if cost_code.id not in work_items_by_cost_code:
                work_items_by_cost_code[cost_code.id] = {
                    'cost_code': cost_code,
                    'work_items': []
                }
            work_items_by_cost_code[cost_code.id]['work_items'].append(work_item)
        
        # Calculate totals (only for work items with same unit of measure)
        units_of_measure = {}
        for wi in work_items:
            if wi.unit_of_measure not in units_of_measure:
                units_of_measure[wi.unit_of_measure] = {
                    'budgeted': 0,
                    'earned': 0
                }
            units_of_measure[wi.unit_of_measure]['budgeted'] += wi.budgeted_quantity
            units_of_measure[wi.unit_of_measure]['earned'] += wi.earned_quantity
        
        return render_template('report_template_quantities.html',
                              project=project,
                              sub_job=sub_job,
                              report_title=report_title,
                              work_items_by_cost_code=work_items_by_cost_code,
                              units_of_measure=units_of_measure,
                              report_date=datetime.now().strftime('%Y-%m-%d'))
    
    return redirect(url_for('main.reports_index'))

# Define discipline choices for templates
@main.context_processor
def inject_discipline_choices():
    from models import DISCIPLINE_CHOICES
    return dict(DISCIPLINE_CHOICES=DISCIPLINE_CHOICES)
