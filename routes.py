from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from models import db, Project, SubJob, CostCode, RuleOfCredit, WorkItem, ProjectCostCode, DISCIPLINE_CHOICES
import uuid
import traceback
import json
from datetime import datetime, timedelta
import calendar
from sqlalchemy import func, and_, or_, desc, extract
import os
from reports.pdf_export import QuantitiesPDF, HoursPDF

# Define the blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Dashboard page"""
    try:
        # Get all projects for the dropdown
        projects = Project.query.all()
        
        # Get recent work items (limit to 10)
        work_items = WorkItem.query.order_by(WorkItem.id.desc()).limit(10).all()
        
        # Calculate earned values for each work item
        for item in work_items:
            item.calculate_earned_values()
        
        return render_template('index.html', projects=projects, work_items=work_items)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('index.html', projects=[], work_items=[])

@main_bp.route('/api/get_project_progress/<int:project_id>')
def get_project_progress(project_id):
    """API endpoint to get project progress data"""
    try:
        # Get the project
        project = Project.query.get_or_404(project_id)
        
        # Get all work items for this project
        work_items = WorkItem.query.filter_by(project_id=project_id).all()
        
        # Calculate total budgeted and earned hours
        total_budgeted_hours = sum(item.budgeted_man_hours or 0 for item in work_items)
        total_earned_hours = sum(item.earned_man_hours or 0 for item in work_items)
        
        # Calculate overall progress percentage
        overall_progress = 0
        if total_budgeted_hours > 0:
            overall_progress = (total_earned_hours / total_budgeted_hours) * 100
        
        return jsonify({
            'overall_progress': overall_progress,
            'total_budgeted_hours': total_budgeted_hours,
            'total_earned_hours': total_earned_hours
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@main_bp.route('/projects')
def projects():
    """Projects page"""
    try:
        projects = Project.query.all()
        return render_template('projects.html', projects=projects)
    except Exception as e:
        flash(f'Error loading projects: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('projects.html', projects=[])

@main_bp.route('/add_project', methods=['GET', 'POST'])
def add_project():
    """Add a new project"""
    try:
        if request.method == 'POST':
            try:
                # Get form data
                name = request.form.get('name')
                description = request.form.get('description')
                
                # Create new project
                new_project = Project(
                    name=name,
                    description=description,
                    project_id_str=f"PRJ-{uuid.uuid4().hex[:8].upper()}"
                )
                
                db.session.add(new_project)
                db.session.commit()
                
                flash('Project added successfully!', 'success')
                return redirect(url_for('main.projects'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error adding project: {str(e)}', 'danger')
                traceback.print_exc()
        
        return render_template('add_project.html')
    except Exception as e:
        flash(f'Error loading add project form: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.projects'))

@main_bp.route('/edit_project/<int:project_id>', methods=['GET', 'POST'])
def edit_project(project_id):
    """Edit an existing project"""
    try:
        project = Project.query.get_or_404(project_id)
        
        if request.method == 'POST':
            try:
                # Get form data
                name = request.form.get('name')
                description = request.form.get('description')
                
                # Update project
                project.name = name
                project.description = description
                
                db.session.commit()
                
                flash('Project updated successfully!', 'success')
                return redirect(url_for('main.view_project', project_id=project.id))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating project: {str(e)}', 'danger')
                traceback.print_exc()
        
        return render_template('edit_project.html', project=project)
    except Exception as e:
        flash(f'Error loading edit project form: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.projects'))

@main_bp.route('/view_project/<int:project_id>')
def view_project(project_id):
    """View a specific project"""
    try:
        project = Project.query.get_or_404(project_id)
        sub_jobs = SubJob.query.filter_by(project_id=project_id).all()
        
        # Get work items for this project
        work_items = WorkItem.query.filter_by(project_id=project_id).all()
        
        # Calculate project statistics
        total_budgeted_hours = sum(item.budgeted_man_hours or 0 for item in work_items)
        total_earned_hours = sum(item.earned_man_hours or 0 for item in work_items)
        
        percent_complete = 0
        if total_budgeted_hours > 0:
            percent_complete = (total_earned_hours / total_budgeted_hours) * 100
        
        return render_template('view_project.html', 
                              project=project, 
                              sub_jobs=sub_jobs,
                              total_budgeted_hours=total_budgeted_hours,
                              total_earned_hours=total_earned_hours,
                              percent_complete=percent_complete)
    except Exception as e:
        flash(f'Error loading project: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.projects'))

@main_bp.route('/delete_project/<int:project_id>', methods=['POST'])
def delete_project(project_id):
    """Delete a project"""
    try:
        project = Project.query.get_or_404(project_id)
        
        # Delete all sub jobs associated with this project
        sub_jobs = SubJob.query.filter_by(project_id=project_id).all()
        for sub_job in sub_jobs:
            db.session.delete(sub_job)
        
        # Delete all work items associated with this project
        work_items = WorkItem.query.filter_by(project_id=project_id).all()
        for work_item in work_items:
            db.session.delete(work_item)
        
        # Delete all project-cost code associations
        project_cost_codes = ProjectCostCode.query.filter_by(project_id=project_id).all()
        for pcc in project_cost_codes:
            db.session.delete(pcc)
        
        # Delete the project
        db.session.delete(project)
        db.session.commit()
        
        flash('Project deleted successfully!', 'success')
        return redirect(url_for('main.projects'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting project: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.view_project', project_id=project_id))

@main_bp.route('/add_sub_job/<int:project_id>', methods=['GET', 'POST'])
def add_sub_job(project_id):
    """Add a new sub job to a project"""
    try:
        project = Project.query.get_or_404(project_id)
        
        if request.method == 'POST':
            try:
                # Get form data
                name = request.form.get('name')
                description = request.form.get('description')
                
                # Create new sub job
                new_sub_job = SubJob(
                    name=name,
                    description=description,
                    project_id=project_id,
                    sub_job_id_str=f"SJ-{uuid.uuid4().hex[:8].upper()}"
                )
                
                db.session.add(new_sub_job)
                db.session.commit()
                
                flash('Sub job added successfully!', 'success')
                return redirect(url_for('main.view_project', project_id=project_id))
            except Exception as e:
                db.session.rollback()
                flash(f'Error adding sub job: {str(e)}', 'danger')
                traceback.print_exc()
        
        return render_template('add_sub_job.html', project=project)
    except Exception as e:
        flash(f'Error loading add sub job form: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.view_project', project_id=project_id))

@main_bp.route('/edit_sub_job/<int:sub_job_id>', methods=['GET', 'POST'])
def edit_sub_job(sub_job_id):
    """Edit an existing sub job"""
    try:
        sub_job = SubJob.query.get_or_404(sub_job_id)
        
        if request.method == 'POST':
            try:
                # Get form data
                name = request.form.get('name')
                description = request.form.get('description')
                
                # Update sub job
                sub_job.name = name
                sub_job.description = description
                
                db.session.commit()
                
                flash('Sub job updated successfully!', 'success')
                return redirect(url_for('main.view_sub_job', sub_job_id=sub_job.id))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating sub job: {str(e)}', 'danger')
                traceback.print_exc()
        
        return render_template('edit_sub_job.html', sub_job=sub_job)
    except Exception as e:
        flash(f'Error loading edit sub job form: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.view_project', project_id=sub_job.project_id))

@main_bp.route('/view_sub_job/<int:sub_job_id>')
def view_sub_job(sub_job_id):
    """View a specific sub job"""
    try:
        sub_job = SubJob.query.get_or_404(sub_job_id)
        
        # Get work items for this sub job
        work_items = WorkItem.query.filter_by(sub_job_id=sub_job_id).all()
        
        # Calculate sub job statistics
        total_budgeted_hours = sum(item.budgeted_man_hours or 0 for item in work_items)
        total_earned_hours = sum(item.earned_man_hours or 0 for item in work_items)
        
        percent_complete = 0
        if total_budgeted_hours > 0:
            percent_complete = (total_earned_hours / total_budgeted_hours) * 100
        
        return render_template('view_sub_job.html', 
                              sub_job=sub_job, 
                              work_items=work_items,
                              total_budgeted_hours=total_budgeted_hours,
                              total_earned_hours=total_earned_hours,
                              percent_complete=percent_complete)
    except Exception as e:
        flash(f'Error loading sub job: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.projects'))

@main_bp.route('/delete_sub_job/<int:sub_job_id>', methods=['POST'])
def delete_sub_job(sub_job_id):
    """Delete a sub job"""
    try:
        sub_job = SubJob.query.get_or_404(sub_job_id)
        project_id = sub_job.project_id
        
        # Delete all work items associated with this sub job
        work_items = WorkItem.query.filter_by(sub_job_id=sub_job_id).all()
        for work_item in work_items:
            db.session.delete(work_item)
        
        # Delete the sub job
        db.session.delete(sub_job)
        db.session.commit()
        
        flash('Sub job deleted successfully!', 'success')
        return redirect(url_for('main.view_project', project_id=project_id))
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting sub job: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))

@main_bp.route('/list_cost_codes')
def list_cost_codes():
    """List all cost codes"""
    try:
        cost_codes = CostCode.query.all()
        return render_template('list_cost_codes.html', cost_codes=cost_codes)
    except Exception as e:
        flash(f'Error loading cost codes: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('list_cost_codes.html', cost_codes=[])

@main_bp.route('/add_cost_code', methods=['GET', 'POST'])
def add_cost_code():
    """Add a new cost code"""
    try:
        if request.method == 'POST':
            try:
                # Get form data
                code = request.form.get('code')
                description = request.form.get('description')
                discipline = request.form.get('discipline')
                rule_of_credit_id = request.form.get('rule_of_credit_id') or None
                project_ids = request.form.getlist('project_ids')
                
                # Create new cost code
                new_cost_code = CostCode(
                    cost_code_id_str=code,
                    description=description,
                    discipline=discipline,
                    rule_of_credit_id=rule_of_credit_id
                )
                
                db.session.add(new_cost_code)
                db.session.flush()  # Get the ID without committing
                
                # Create project associations
                for project_id in project_ids:
                    project_cost_code = ProjectCostCode(
                        project_id=project_id,
                        cost_code_id=new_cost_code.id
                    )
                    db.session.add(project_cost_code)
                
                db.session.commit()
                
                flash('Cost code added successfully!', 'success')
                return redirect(url_for('main.list_cost_codes'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error adding cost code: {str(e)}', 'danger')
                traceback.print_exc()
        
        # Get all projects and rules of credit for the form
        projects = Project.query.all()
        rules = RuleOfCredit.query.all()
        
        return render_template('add_cost_code.html', 
                              projects=projects,
                              rules=rules,
                              disciplines=DISCIPLINE_CHOICES)
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
                # Get form data
                code = request.form.get('code')
                description = request.form.get('description')
                discipline = request.form.get('discipline')
                rule_of_credit_id = request.form.get('rule_of_credit_id') or None
                project_ids = request.form.getlist('project_ids')
                
                # Update cost code
                cost_code.cost_code_id_str = code
                cost_code.description = description
                cost_code.discipline = discipline
                cost_code.rule_of_credit_id = rule_of_credit_id
                
                # Update project associations
                # First, remove all existing associations
                ProjectCostCode.query.filter_by(cost_code_id=cost_code_id).delete()
                
                # Then, create new associations
                for project_id in project_ids:
                    project_cost_code = ProjectCostCode(
                        project_id=project_id,
                        cost_code_id=cost_code_id
                    )
                    db.session.add(project_cost_code)
                
                db.session.commit()
                
                flash('Cost code updated successfully!', 'success')
                return redirect(url_for('main.list_cost_codes'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating cost code: {str(e)}', 'danger')
                traceback.print_exc()
        
        # Get all projects and rules of credit for the form
        projects = Project.query.all()
        rules = RuleOfCredit.query.all()
        
        # Get associated project IDs
        project_cost_codes = ProjectCostCode.query.filter_by(cost_code_id=cost_code_id).all()
        associated_project_ids = [pcc.project_id for pcc in project_cost_codes]
        
        return render_template('edit_cost_code.html', 
                              cost_code=cost_code,
                              projects=projects,
                              rules=rules,
                              disciplines=DISCIPLINE_CHOICES,
                              associated_project_ids=associated_project_ids)
    except Exception as e:
        flash(f'Error loading edit cost code form: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_cost_codes'))

@main_bp.route('/delete_cost_code/<int:cost_code_id>', methods=['POST'])
def delete_cost_code(cost_code_id):
    """Delete a cost code"""
    try:
        cost_code = CostCode.query.get_or_404(cost_code_id)
        
        # Check if this cost code is used by any work items
        work_items = WorkItem.query.filter_by(cost_code_id=cost_code_id).all()
        if work_items:
            flash('Cannot delete cost code because it is used by work items.', 'danger')
            return redirect(url_for('main.list_cost_codes'))
        
        # Delete all project associations
        ProjectCostCode.query.filter_by(cost_code_id=cost_code_id).delete()
        
        # Delete the cost code
        db.session.delete(cost_code)
        db.session.commit()
        
        flash('Cost code deleted successfully!', 'success')
        return redirect(url_for('main.list_cost_codes'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting cost code: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_cost_codes'))

@main_bp.route('/list_rules_of_credit')
def list_rules_of_credit():
    """List all rules of credit"""
    try:
        rules = RuleOfCredit.query.all()
        return render_template('list_rules_of_credit.html', rules=rules)
    except Exception as e:
        flash(f'Error loading rules of credit: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('list_rules_of_credit.html', rules=[])

@main_bp.route('/add_rule_of_credit', methods=['GET', 'POST'])
def add_rule_of_credit():
    """Add a new rule of credit"""
    try:
        if request.method == 'POST':
            try:
                # Get form data
                name = request.form.get('name')
                description = request.form.get('description')
                
                # Get steps data
                steps = []
                step_names = request.form.getlist('step_name[]')
                step_weights = request.form.getlist('step_weight[]')
                
                for i in range(len(step_names)):
                    if step_names[i] and step_weights[i]:
                        steps.append({
                            'name': step_names[i],
                            'weight': float(step_weights[i])
                        })
                
                # Create new rule of credit
                new_rule = RuleOfCredit(
                    name=name,
                    description=description,
                    steps_json=json.dumps(steps)
                )
                
                db.session.add(new_rule)
                db.session.commit()
                
                flash('Rule of credit added successfully!', 'success')
                return redirect(url_for('main.list_rules_of_credit'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error adding rule of credit: {str(e)}', 'danger')
                traceback.print_exc()
        
        return render_template('add_rule_of_credit.html')
    except Exception as e:
        flash(f'Error loading add rule of credit form: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_rules_of_credit'))

@main_bp.route('/edit_rule_of_credit/<int:rule_id>', methods=['GET', 'POST'])
def edit_rule_of_credit(rule_id):
    """Edit an existing rule of credit"""
    try:
        rule = RuleOfCredit.query.get_or_404(rule_id)
        
        if request.method == 'POST':
            try:
                # Get form data
                name = request.form.get('name')
                description = request.form.get('description')
                
                # Get steps data
                steps = []
                step_names = request.form.getlist('step_name[]')
                step_weights = request.form.getlist('step_weight[]')
                
                for i in range(len(step_names)):
                    if step_names[i] and step_weights[i]:
                        steps.append({
                            'name': step_names[i],
                            'weight': float(step_weights[i])
                        })
                
                # Update rule of credit
                rule.name = name
                rule.description = description
                rule.steps_json = json.dumps(steps)
                
                db.session.commit()
                
                flash('Rule of credit updated successfully!', 'success')
                return redirect(url_for('main.list_rules_of_credit'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating rule of credit: {str(e)}', 'danger')
                traceback.print_exc()
        
        # Get steps for the form
        steps = rule.get_steps()
        
        return render_template('edit_rule_of_credit.html', rule=rule, steps=steps)
    except Exception as e:
        flash(f'Error loading edit rule of credit form: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_rules_of_credit'))

@main_bp.route('/delete_rule_of_credit/<int:rule_id>', methods=['POST'])
def delete_rule_of_credit(rule_id):
    """Delete a rule of credit"""
    try:
        rule = RuleOfCredit.query.get_or_404(rule_id)
        
        # Check if this rule is used by any cost codes
        cost_codes = CostCode.query.filter_by(rule_of_credit_id=rule_id).all()
        if cost_codes:
            flash('Cannot delete rule of credit because it is used by cost codes.', 'danger')
            return redirect(url_for('main.list_rules_of_credit'))
        
        # Delete the rule
        db.session.delete(rule)
        db.session.commit()
        
        flash('Rule of credit deleted successfully!', 'success')
        return redirect(url_for('main.list_rules_of_credit'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting rule of credit: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_rules_of_credit'))

@main_bp.route('/work_items')
def work_items():
    """Work items page"""
    try:
        # Get all work items
        work_items = WorkItem.query.order_by(WorkItem.id.desc()).all()
        
        # Calculate earned values for each work item
        for item in work_items:
            item.calculate_earned_values()
        
        # Get all projects and sub jobs for filtering
        projects = Project.query.all()
        
        # Get sub jobs for the selected project
        project_id = request.args.get('project_id', type=int)
        if project_id:
            sub_jobs = SubJob.query.filter_by(project_id=project_id).all()
        else:
            sub_jobs = []
        
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
                if cost_code and cost_code.rule_of_credit_id:
                    rule = RuleOfCredit.query.get(cost_code.rule_of_credit_id)
                    if rule:
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
        
        # Get projects, sub jobs for the form
        projects = Project.query.all()
        
        # Check if sub_job_id is provided in the URL
        pre_selected_sub_job_id = request.args.get('sub_job_id', type=int)
        pre_selected_project_id = None
        
        if pre_selected_sub_job_id:
            sub_job = SubJob.query.get(pre_selected_sub_job_id)
            if sub_job:
                pre_selected_project_id = sub_job.project_id
                sub_jobs = SubJob.query.filter_by(project_id=pre_selected_project_id).all()
                # Get cost codes associated with this project
                project_cost_codes = ProjectCostCode.query.filter_by(project_id=pre_selected_project_id).all()
                cost_code_ids = [pcc.cost_code_id for pcc in project_cost_codes]
                cost_codes = CostCode.query.filter(CostCode.id.in_(cost_code_ids)).all() if cost_code_ids else []
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
        
        # Get projects, sub jobs for the form
        projects = Project.query.all()
        sub_jobs = SubJob.query.filter_by(project_id=work_item.project_id).all()
        
        # Get cost codes associated with this project
        project_cost_codes = ProjectCostCode.query.filter_by(project_id=work_item.project_id).all()
        cost_code_ids = [pcc.cost_code_id for pcc in project_cost_codes]
        cost_codes = CostCode.query.filter(CostCode.id.in_(cost_code_ids)).all() if cost_code_ids else []
        
        # Make sure the current cost code is included even if it's not associated with the project anymore
        if work_item.cost_code_id and work_item.cost_code_id not in cost_code_ids:
            current_cost_code = CostCode.query.get(work_item.cost_code_id)
            if current_cost_code and current_cost_code not in cost_codes:
                cost_codes.append(current_cost_code)
        
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
        
        if work_item.cost_code and work_item.cost_code.rule_of_credit_id:
            rule = RuleOfCredit.query.get(work_item.cost_code.rule_of_credit_id)
            if rule:
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

@main_bp.route('/delete_work_item/<int:work_item_id>', methods=['POST'])
def delete_work_item(work_item_id):
    """Delete a work item"""
    try:
        work_item = WorkItem.query.get_or_404(work_item_id)
        sub_job_id = work_item.sub_job_id
        
        # Delete the work item
        db.session.delete(work_item)
        db.session.commit()
        
        flash('Work item deleted successfully!', 'success')
        
        # Redirect based on where the user came from
        if sub_job_id:
            return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))
        else:
            return redirect(url_for('main.work_items'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting work item: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.view_work_item', work_item_id=work_item_id))

@main_bp.route('/update_work_item_progress/<int:work_item_id>', methods=['GET', 'POST'])
def update_work_item_progress(work_item_id):
    """Update progress for a work item"""
    try:
        work_item = WorkItem.query.get_or_404(work_item_id)
        
        # Get rule of credit steps and progress
        steps = []
        progress_data = work_item.get_steps_progress()
        
        if work_item.cost_code and work_item.cost_code.rule_of_credit_id:
            rule = RuleOfCredit.query.get(work_item.cost_code.rule_of_credit_id)
            if rule:
                steps = rule.get_steps()
                
                # Add progress to steps
                for step in steps:
                    step_name = step['name']
                    step['progress'] = progress_data.get(step_name, 0)
        
        if request.method == 'POST':
            try:
                # Get progress data from form
                new_progress_data = {}
                for step in steps:
                    step_name = step['name']
                    progress_value = request.form.get(f'progress_{step_name}')
                    if progress_value is not None:
                        new_progress_data[step_name] = float(progress_value)
                
                # Update progress data
                work_item.set_progress_data(new_progress_data)
                
                # Recalculate earned values
                work_item.calculate_earned_values()
                
                db.session.commit()
                flash('Progress updated successfully!', 'success')
                return redirect(url_for('main.view_work_item', work_item_id=work_item.id))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating progress: {str(e)}', 'danger')
                traceback.print_exc()
        
        return render_template('update_work_item_progress.html', 
                              work_item=work_item,
                              steps=steps)
    except Exception as e:
        flash(f'Error loading update progress form: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.view_work_item', work_item_id=work_item_id))

@main_bp.route('/reports')
def reports_index():
    """Reports index page"""
    try:
        projects = Project.query.all()
        return render_template('reports_index.html', projects=projects)
    except Exception as e:
        flash(f'Error loading reports: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('reports_index.html', projects=[])

@main_bp.route('/api/get_cost_codes/<int:project_id>')
def get_cost_codes(project_id):
    """API endpoint to get cost codes for a project"""
    try:
        # Get cost codes associated with this project through the join table
        project_cost_codes = ProjectCostCode.query.filter_by(project_id=project_id).all()
        cost_code_ids = [pcc.cost_code_id for pcc in project_cost_codes]
        cost_codes = CostCode.query.filter(CostCode.id.in_(cost_code_ids)).all() if cost_code_ids else []
        
        # Format cost codes for JSON response
        cost_codes_data = [{
            'id': cc.id,
            'code': cc.cost_code_id_str,
            'description': cc.description
        } for cc in cost_codes]
        
        return jsonify({'cost_codes': cost_codes_data})
    except Exception as e:
        return jsonify({'error': str(e)})

@main_bp.route('/api/get_sub_jobs/<int:project_id>')
def get_sub_jobs(project_id):
    """API endpoint to get sub jobs for a project"""
    try:
        sub_jobs = SubJob.query.filter_by(project_id=project_id).all()
        
        # Format sub jobs for JSON response
        sub_jobs_data = [{
            'id': sj.id,
            'name': sj.name
        } for sj in sub_jobs]
        
        return jsonify({'sub_jobs': sub_jobs_data})
    except Exception as e:
        return jsonify({'error': str(e)})

@main_bp.route('/generate_quantities_pdf/<int:project_id>')
def generate_quantities_pdf(project_id):
    """Generate a quantities PDF report for a project"""
    try:
        project = Project.query.get_or_404(project_id)
        
        # Get all work items for this project
        work_items = WorkItem.query.filter_by(project_id=project_id).all()
        
        # Calculate earned values for each work item
        for item in work_items:
            item.calculate_earned_values()
        
        # Generate PDF
        pdf = QuantitiesPDF(project, work_items)
        pdf_path = pdf.generate()
        
        # Send the file
        return send_file(pdf_path, as_attachment=True, download_name=f"{project.name}_quantities.pdf")
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.reports_index'))

@main_bp.route('/generate_hours_pdf/<int:project_id>')
def generate_hours_pdf(project_id):
    """Generate a hours PDF report for a project"""
    try:
        project = Project.query.get_or_404(project_id)
        
        # Get all work items for this project
        work_items = WorkItem.query.filter_by(project_id=project_id).all()
        
        # Calculate earned values for each work item
        for item in work_items:
            item.calculate_earned_values()
        
        # Generate PDF
        pdf = HoursPDF(project, work_items)
        pdf_path = pdf.generate()
        
        # Send the file
        return send_file(pdf_path, as_attachment=True, download_name=f"{project.name}_hours.pdf")
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.reports_index'))
