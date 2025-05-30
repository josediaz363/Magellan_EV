from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
import json
import uuid
import traceback
import os
import datetime
import io

# Import services
from services.project_service import ProjectService
from services.sub_job_service import SubJobService
from services.workitem_service import WorkItemService
from services.costcode_service import CostCodeService
from services.ruleofcredit_service import RuleOfCreditService
from models import DISCIPLINE_CHOICES

# Initialize services
project_service = ProjectService()
sub_job_service = SubJobService()
workitem_service = WorkItemService()
costcode_service = CostCodeService()
ruleofcredit_service = RuleOfCreditService()

# Create a blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page route"""
    try:
        projects = project_service.get_all_projects()
        work_items = workitem_service.get_recent_workitems(10)
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
        projects_with_data = project_service.get_projects_with_metrics()
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
        
        new_project = project_service.create_project(name, description, project_id_str)
        if new_project:
            flash('Project added successfully!', 'success')
        else:
            flash('Error adding project', 'danger')
        
        return redirect(url_for('main.projects'))
    
    return render_template('add_project.html')

@main_bp.route('/project/<int:project_id>')
def view_project(project_id):
    """View a specific project"""
    try:
        project = project_service.get_project_by_id(project_id)
        if not project:
            flash('Project not found', 'danger')
            return redirect(url_for('main.projects'))
            
        sub_jobs = sub_job_service.get_sub_jobs_by_project(project_id)
        
        # Calculate project-level totals
        total_budgeted_hours = 0
        total_earned_hours = 0
        total_budgeted_quantity = 0
        total_earned_quantity = 0
        
        # Get all work items for this project
        work_items = workitem_service.get_workitems_by_project(project_id)
        
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
    """Edit a project"""
    try:
        project = project_service.get_project_by_id(project_id)
        if not project:
            flash('Project not found', 'danger')
            return redirect(url_for('main.projects'))
        
        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description')
            
            updated_project = project_service.update_project(project_id, name, description)
            if updated_project:
                flash('Project updated successfully!', 'success')
            else:
                flash('Error updating project', 'danger')
            
            return redirect(url_for('main.view_project', project_id=project_id))
        
        return render_template('edit_project.html', project=project)
    except Exception as e:
        flash(f'Error editing project: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.projects'))

@main_bp.route('/delete_project/<int:project_id>', methods=['POST'])
def delete_project(project_id):
    """Delete a project"""
    try:
        if project_service.delete_project(project_id):
            flash('Project deleted successfully!', 'success')
        else:
            flash('Error deleting project', 'danger')
    except Exception as e:
        flash(f'Error deleting project: {str(e)}', 'danger')
        traceback.print_exc()
    
    return redirect(url_for('main.projects'))

# ===== SUB JOB ROUTES =====

@main_bp.route('/project/<int:project_id>/add_sub_job', methods=['GET', 'POST'])
def add_sub_job(project_id):
    """Add a new sub job to a project"""
    try:
        project = project_service.get_project_by_id(project_id)
        if not project:
            flash('Project not found', 'danger')
            return redirect(url_for('main.projects'))
        
        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description')
            sub_job_id_str = request.form.get('sub_job_id_str') or f"SJ-{uuid.uuid4().hex[:8].upper()}"
            area = request.form.get('area')
            
            new_sub_job = sub_job_service.create_sub_job(name, description, sub_job_id_str, project_id, area)
            if new_sub_job:
                flash('Sub job added successfully!', 'success')
            else:
                flash('Error adding sub job', 'danger')
            
            return redirect(url_for('main.view_project', project_id=project_id))
        
        return render_template('add_sub_job.html', project=project)
    except Exception as e:
        flash(f'Error adding sub job: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.view_project', project_id=project_id))

@main_bp.route('/sub_job/<int:sub_job_id>')
def view_sub_job(sub_job_id):
    """View a specific sub job"""
    try:
        sub_job_data = sub_job_service.get_sub_job_metrics(sub_job_id)
        if not sub_job_data:
            flash('Sub job not found', 'danger')
            return redirect(url_for('main.projects'))
        
        return render_template('view_sub_job.html', 
                              sub_job=sub_job_data['sub_job'],
                              work_items=sub_job_data['work_items'],
                              overall_progress=sub_job_data['overall_progress'],
                              total_earned_hours=sub_job_data['total_earned_hours'],
                              total_budgeted_hours=sub_job_data['total_budgeted_hours'])
    except Exception as e:
        flash(f'Error loading sub job: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.projects'))

@main_bp.route('/edit_sub_job/<int:sub_job_id>', methods=['GET', 'POST'])
def edit_sub_job(sub_job_id):
    """Edit a sub job"""
    try:
        sub_job = sub_job_service.get_sub_job_by_id(sub_job_id)
        if not sub_job:
            flash('Sub job not found', 'danger')
            return redirect(url_for('main.projects'))
        
        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description')
            area = request.form.get('area')
            
            updated_sub_job = sub_job_service.update_sub_job(sub_job_id, name, description, area)
            if updated_sub_job:
                flash('Sub job updated successfully!', 'success')
            else:
                flash('Error updating sub job', 'danger')
            
            return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))
        
        return render_template('edit_sub_job.html', sub_job=sub_job)
    except Exception as e:
        flash(f'Error editing sub job: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.projects'))

@main_bp.route('/delete_sub_job/<int:sub_job_id>', methods=['POST'])
def delete_sub_job(sub_job_id):
    """Delete a sub job"""
    try:
        sub_job = sub_job_service.get_sub_job_by_id(sub_job_id)
        if not sub_job:
            flash('Sub job not found', 'danger')
            return redirect(url_for('main.projects'))
        
        project_id = sub_job.project_id
        
        if sub_job_service.delete_sub_job(sub_job_id):
            flash('Sub job deleted successfully!', 'success')
        else:
            flash('Error deleting sub job', 'danger')
        
        return redirect(url_for('main.view_project', project_id=project_id))
    except Exception as e:
        flash(f'Error deleting sub job: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.projects'))

# ===== COST CODE ROUTES =====

@main_bp.route('/cost_codes')
def list_cost_codes():
    """List all cost codes"""
    try:
        costcodes_with_projects = costcode_service.get_costcodes_with_projects()
        return render_template('list_cost_codes.html', cost_codes=costcodes_with_projects)
    except Exception as e:
        flash(f'Error loading cost codes: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('list_cost_codes.html', cost_codes=[])

@main_bp.route('/add_cost_code', methods=['GET', 'POST'])
def add_cost_code():
    """Add a new cost code"""
    try:
        if request.method == 'POST':
            cost_code_id_str = request.form.get('cost_code_id_str')
            description = request.form.get('description')
            discipline = request.form.get('discipline')
            project_id = request.form.get('project_id')
            rule_of_credit_id = request.form.get('rule_of_credit_id')
            if rule_of_credit_id == '':
                rule_of_credit_id = None
            
            new_costcode = costcode_service.create_costcode(
                cost_code_id_str, description, discipline, project_id, rule_of_credit_id)
            
            if new_costcode:
                flash('Cost code added successfully!', 'success')
                return redirect(url_for('main.list_cost_codes'))
            else:
                flash('Error adding cost code', 'danger')
        
        projects = project_service.get_all_projects()
        rules = ruleofcredit_service.get_all_rulesofcredit()
        disciplines = costcode_service.get_discipline_choices()
        
        return render_template('add_cost_code.html', 
                              projects=projects, 
                              rules=rules,
                              disciplines=disciplines)
    except Exception as e:
        flash(f'Error adding cost code: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_cost_codes'))

@main_bp.route('/edit_cost_code/<int:costcode_id>', methods=['GET', 'POST'])
def edit_cost_code(costcode_id):
    """Edit a cost code"""
    try:
        costcode = costcode_service.get_costcode_by_id(costcode_id)
        if not costcode:
            flash('Cost code not found', 'danger')
            return redirect(url_for('main.list_cost_codes'))
        
        if request.method == 'POST':
            description = request.form.get('description')
            discipline = request.form.get('discipline')
            rule_of_credit_id = request.form.get('rule_of_credit_id')
            if rule_of_credit_id == '':
                rule_of_credit_id = None
            
            updated_costcode = costcode_service.update_costcode(
                costcode_id, description, discipline, rule_of_credit_id)
            
            if updated_costcode:
                flash('Cost code updated successfully!', 'success')
                return redirect(url_for('main.list_cost_codes'))
            else:
                flash('Error updating cost code', 'danger')
        
        rules_of_credit = ruleofcredit_service.get_all_rulesofcredit()
        disciplines = costcode_service.get_discipline_choices()
        
        return render_template('edit_cost_code.html', 
                              costcode=costcode, 
                              rules=rules_of_credit,
                              disciplines=disciplines)
    except Exception as e:
        flash(f'Error editing cost code: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_cost_codes'))

@main_bp.route('/delete_cost_code/<int:costcode_id>', methods=['POST'])
def delete_cost_code(costcode_id):
    """Delete a cost code"""
    try:
        if costcode_service.delete_costcode(costcode_id):
            flash('Cost code deleted successfully!', 'success')
        else:
            flash('Error deleting cost code', 'danger')
    except Exception as e:
        flash(f'Error deleting cost code: {str(e)}', 'danger')
        traceback.print_exc()
    
    return redirect(url_for('main.list_cost_codes'))

# ===== RULE OF CREDIT ROUTES =====

@main_bp.route('/rules_of_credit')
def list_rules_of_credit():
    """List all rules of credit"""
    try:
        rules = ruleofcredit_service.get_all_rulesofcredit()
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
            name = request.form.get('name')
            description = request.form.get('description')
            
            new_rule = ruleofcredit_service.create_ruleofcredit(name, description)
            if new_rule:
                flash('Rule of credit added successfully!', 'success')
                return redirect(url_for('main.edit_rule_of_credit', ruleofcredit_id=new_rule.id))
            else:
                flash('Error adding rule of credit', 'danger')
        
        return render_template('add_rule_of_credit.html')
    except Exception as e:
        flash(f'Error adding rule of credit: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_rules_of_credit'))

@main_bp.route('/edit_rule_of_credit/<int:ruleofcredit_id>', methods=['GET', 'POST'])
def edit_rule_of_credit(ruleofcredit_id):
    """Edit a rule of credit"""
    try:
        rule = ruleofcredit_service.get_ruleofcredit_by_id(ruleofcredit_id)
        if not rule:
            flash('Rule of credit not found', 'danger')
            return redirect(url_for('main.list_rules_of_credit'))
        
        steps = ruleofcredit_service.get_steps(ruleofcredit_id)
        
        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description')
            
            updated_rule = ruleofcredit_service.update_ruleofcredit(ruleofcredit_id, name, description)
            if updated_rule:
                flash('Rule of credit updated successfully!', 'success')
            else:
                flash('Error updating rule of credit', 'danger')
            
            return redirect(url_for('main.edit_rule_of_credit', ruleofcredit_id=ruleofcredit_id))
        
        return render_template('edit_rule_of_credit.html', rule=rule, steps=steps)
    except Exception as e:
        flash(f'Error editing rule of credit: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_rules_of_credit'))

@main_bp.route('/delete_rule_of_credit/<int:ruleofcredit_id>', methods=['POST'])
def delete_rule_of_credit(ruleofcredit_id):
    """Delete a rule of credit"""
    try:
        if ruleofcredit_service.delete_ruleofcredit(ruleofcredit_id):
            flash('Rule of credit deleted successfully!', 'success')
        else:
            flash('Error deleting rule of credit', 'danger')
    except Exception as e:
        flash(f'Error deleting rule of credit: {str(e)}', 'danger')
        traceback.print_exc()
    
    return redirect(url_for('main.list_rules_of_credit'))

@main_bp.route('/add_step/<int:ruleofcredit_id>', methods=['POST'])
def add_step(ruleofcredit_id):
    """Add a step to a rule of credit"""
    try:
        step_name = request.form.get('step_name')
        weight = request.form.get('weight')
        
        if ruleofcredit_service.add_step(ruleofcredit_id, step_name, weight):
            flash('Step added successfully!', 'success')
        else:
            flash('Error adding step', 'danger')
    except Exception as e:
        flash(f'Error adding step: {str(e)}', 'danger')
        traceback.print_exc()
    
    return redirect(url_for('main.edit_rule_of_credit', ruleofcredit_id=ruleofcredit_id))

@main_bp.route('/update_step/<int:ruleofcredit_id>/<int:step_index>', methods=['POST'])
def update_step(ruleofcredit_id, step_index):
    """Update a step in a rule of credit"""
    try:
        step_name = request.form.get('step_name')
        weight = request.form.get('weight')
        
        if ruleofcredit_service.update_step(ruleofcredit_id, step_index, step_name, weight):
            flash('Step updated successfully!', 'success')
        else:
            flash('Error updating step', 'danger')
    except Exception as e:
        flash(f'Error updating step: {str(e)}', 'danger')
        traceback.print_exc()
    
    return redirect(url_for('main.edit_rule_of_credit', ruleofcredit_id=ruleofcredit_id))

@main_bp.route('/delete_step/<int:ruleofcredit_id>/<int:step_index>', methods=['POST'])
def delete_step(ruleofcredit_id, step_index):
    """Delete a step from a rule of credit"""
    try:
        if ruleofcredit_service.delete_step(ruleofcredit_id, step_index):
            flash('Step deleted successfully!', 'success')
        else:
            flash('Error deleting step', 'danger')
    except Exception as e:
        flash(f'Error deleting step: {str(e)}', 'danger')
        traceback.print_exc()
    
    return redirect(url_for('main.edit_rule_of_credit', ruleofcredit_id=ruleofcredit_id))

# ===== WORK ITEM ROUTES =====

@main_bp.route('/work_items')
def list_work_items():
    """List all work items"""
    try:
        work_items_with_data = workitem_service.get_workitems_with_related()
        return render_template('list_work_items.html', work_items_with_data=work_items_with_data)
    except Exception as e:
        flash(f'Error loading work items: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('list_work_items.html', work_items_with_data=[])

# Alias for list_work_items to maintain compatibility with existing templates
@main_bp.route('/work_items_alias')
def work_items():
    """Alias for list_work_items to maintain compatibility"""
    return list_work_items()

@main_bp.route('/add_work_item', methods=['GET', 'POST'])
def add_work_item():
    """Add a new work item"""
    try:
        if request.method == 'POST':
            work_item_id_str = request.form.get('work_item_id_str') or f"WI-{uuid.uuid4().hex[:8].upper()}"
            description = request.form.get('description')
            project_id = request.form.get('project_id')
            sub_job_id = request.form.get('sub_job_id')
            cost_code_id = request.form.get('cost_code_id')
            budgeted_quantity = request.form.get('budgeted_quantity')
            unit_of_measure = request.form.get('unit_of_measure')
            budgeted_man_hours = request.form.get('budgeted_man_hours')
            
            new_workitem = workitem_service.create_workitem(
                work_item_id_str, description, project_id, sub_job_id, cost_code_id,
                budgeted_quantity, unit_of_measure, budgeted_man_hours
            )
            
            if new_workitem:
                flash('Work item added successfully!', 'success')
                return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))
            else:
                flash('Error adding work item', 'danger')
        
        # Get pre-selected project and sub job if provided
        pre_selected_project_id = request.args.get('project_id')
        pre_selected_sub_job_id = request.args.get('sub_job_id')
        
        pre_selected_project = None
        pre_selected_sub_job = None
        
        if pre_selected_project_id:
            pre_selected_project = project_service.get_project_by_id(pre_selected_project_id)
        
        if pre_selected_sub_job_id:
            pre_selected_sub_job = sub_job_service.get_sub_job_by_id(pre_selected_sub_job_id)
            if pre_selected_sub_job and not pre_selected_project:
                pre_selected_project = project_service.get_project_by_id(pre_selected_sub_job.project_id)
        
        projects = project_service.get_all_projects()
        sub_jobs = sub_job_service.get_all(SubJob)
        cost_codes = costcode_service.get_all_costcodes()
        
        return render_template('add_work_item.html', 
                              projects=projects, 
                              sub_jobs=sub_jobs,
                              cost_codes=cost_codes,
                              pre_selected_project=pre_selected_project,
                              pre_selected_sub_job=pre_selected_sub_job)
    except Exception as e:
        flash(f'Error adding work item: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_work_items'))

@main_bp.route('/work_item/<int:workitem_id>')
def view_work_item(workitem_id):
    """View a specific work item"""
    try:
        workitem = workitem_service.get_workitem_by_id(workitem_id)
        if not workitem:
            flash('Work item not found', 'danger')
            return redirect(url_for('main.list_work_items'))
        
        # Get related objects
        project = project_service.get_project_by_id(workitem.project_id)
        sub_job = sub_job_service.get_sub_job_by_id(workitem.sub_job_id)
        cost_code = costcode_service.get_costcode_by_id(workitem.cost_code_id)
        
        # Get rule of credit steps if available
        steps = []
        steps_progress = workitem.get_steps_progress()
        
        if cost_code and cost_code.rule_of_credit_id:
            rule_steps = ruleofcredit_service.get_steps(cost_code.rule_of_credit_id)
            for step in rule_steps:
                step_name = step.get('name')
                step_progress = steps_progress.get(step_name, 0)
                steps.append({
                    'name': step_name,
                    'weight': step.get('weight', 0),
                    'progress': step_progress
                })
        
        return render_template('view_work_item.html', 
                              workitem=workitem,
                              project=project,
                              sub_job=sub_job,
                              cost_code=cost_code,
                              steps=steps)
    except Exception as e:
        flash(f'Error loading work item: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_work_items'))

@main_bp.route('/edit_work_item/<int:workitem_id>', methods=['GET', 'POST'])
def edit_work_item(workitem_id):
    """Edit a work item"""
    try:
        workitem = workitem_service.get_workitem_by_id(workitem_id)
        if not workitem:
            flash('Work item not found', 'danger')
            return redirect(url_for('main.list_work_items'))
        
        if request.method == 'POST':
            description = request.form.get('description')
            budgeted_quantity = request.form.get('budgeted_quantity')
            unit_of_measure = request.form.get('unit_of_measure')
            budgeted_man_hours = request.form.get('budgeted_man_hours')
            
            updated_workitem = workitem_service.update_workitem(
                workitem_id, description, budgeted_quantity, unit_of_measure, budgeted_man_hours
            )
            
            if updated_workitem:
                flash('Work item updated successfully!', 'success')
                return redirect(url_for('main.view_work_item', workitem_id=workitem_id))
            else:
                flash('Error updating work item', 'danger')
        
        return render_template('edit_work_item.html', workitem=workitem)
    except Exception as e:
        flash(f'Error editing work item: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_work_items'))

@main_bp.route('/delete_work_item/<int:workitem_id>', methods=['POST'])
def delete_work_item(workitem_id):
    """Delete a work item"""
    try:
        workitem = workitem_service.get_workitem_by_id(workitem_id)
        if not workitem:
            flash('Work item not found', 'danger')
            return redirect(url_for('main.list_work_items'))
        
        sub_job_id = workitem.sub_job_id
        
        if workitem_service.delete_workitem(workitem_id):
            flash('Work item deleted successfully!', 'success')
        else:
            flash('Error deleting work item', 'danger')
        
        return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))
    except Exception as e:
        flash(f'Error deleting work item: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_work_items'))

@main_bp.route('/update_progress/<int:workitem_id>', methods=['GET', 'POST'])
def update_progress(workitem_id):
    """Update progress for a work item"""
    try:
        workitem = workitem_service.get_workitem_by_id(workitem_id)
        if not workitem:
            flash('Work item not found', 'danger')
            return redirect(url_for('main.list_work_items'))
        
        # Get cost code and rule of credit
        cost_code = costcode_service.get_costcode_by_id(workitem.cost_code_id)
        if not cost_code or not cost_code.rule_of_credit_id:
            flash('No rule of credit associated with this work item', 'warning')
            return redirect(url_for('main.view_work_item', workitem_id=workitem_id))
        
        rule_steps = ruleofcredit_service.get_steps(cost_code.rule_of_credit_id)
        if not rule_steps:
            flash('No steps defined for the associated rule of credit', 'warning')
            return redirect(url_for('main.view_work_item', workitem_id=workitem_id))
        
        if request.method == 'POST':
            progress_updates = {}
            for step in rule_steps:
                step_name = step.get('name')
                progress_value = request.form.get(f'progress_{step_name}', 0)
                progress_updates[step_name] = float(progress_value)
            
            if workitem_service.update_progress(workitem_id, progress_updates):
                flash('Progress updated successfully!', 'success')
            else:
                flash('Error updating progress', 'danger')
            
            return redirect(url_for('main.view_work_item', workitem_id=workitem_id))
        
        # Get current progress
        steps_progress = workitem.get_steps_progress()
        
        steps_with_progress = []
        for step in rule_steps:
            step_name = step.get('name')
            step_progress = steps_progress.get(step_name, 0)
            steps_with_progress.append({
                'name': step_name,
                'weight': step.get('weight', 0),
                'progress': step_progress
            })
        
        return render_template('update_progress.html', 
                              workitem=workitem,
                              steps=steps_with_progress)
    except Exception as e:
        flash(f'Error updating progress: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.view_work_item', workitem_id=workitem_id))

# ===== API ROUTES =====

@main_bp.route('/api/projects')
def api_projects():
    """API endpoint to get all projects"""
    try:
        projects = project_service.get_all_projects()
        return jsonify([p.serialize() for p in projects])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/project/<int:project_id>')
def api_project(project_id):
    """API endpoint to get a specific project"""
    try:
        project = project_service.get_project_by_id(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        return jsonify(project.serialize_with_subjobs_and_workitems())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/sub_jobs/<int:project_id>')
def api_sub_jobs(project_id):
    """API endpoint to get all sub jobs for a project"""
    try:
        sub_jobs = sub_job_service.get_sub_jobs_by_project(project_id)
        return jsonify([sj.serialize() for sj in sub_jobs])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/work_items/<int:sub_job_id>')
def api_work_items(sub_job_id):
    """API endpoint to get all work items for a sub job"""
    try:
        work_items = workitem_service.get_workitems_by_subjob(sub_job_id)
        return jsonify([wi.serialize() for wi in work_items])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/cost_codes/<int:project_id>')
def api_cost_codes(project_id):
    """API endpoint to get all cost codes for a project"""
    try:
        cost_codes = costcode_service.get_costcodes_by_project(project_id)
        return jsonify([cc.serialize() for cc in cost_codes])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/rules_of_credit')
def api_rules_of_credit():
    """API endpoint to get all rules of credit"""
    try:
        rules = ruleofcredit_service.get_all_rulesofcredit()
        return jsonify([r.serialize() for r in rules])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/project_progress/<int:project_id>')
def api_project_progress(project_id):
    """API endpoint to get progress data for a project"""
    try:
        project = project_service.get_project_by_id(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Get all work items for this project
        work_items = workitem_service.get_workitems_by_project(project_id)
        
        # Calculate totals
        total_budgeted_hours = sum(item.budgeted_man_hours or 0 for item in work_items)
        total_earned_hours = sum(item.earned_man_hours or 0 for item in work_items)
        
        # Calculate overall progress percentage
        overall_progress = 0
        if total_budgeted_hours > 0:
            overall_progress = (total_earned_hours / total_budgeted_hours) * 100
        
        # Get sub jobs with their progress
        sub_jobs_data = []
        sub_jobs = sub_job_service.get_sub_jobs_by_project(project_id)
        
        for sub_job in sub_jobs:
            sub_job_items = [item for item in work_items if item.sub_job_id == sub_job.id]
            
            sub_job_budgeted_hours = sum(item.budgeted_man_hours or 0 for item in sub_job_items)
            sub_job_earned_hours = sum(item.earned_man_hours or 0 for item in sub_job_items)
            
            sub_job_progress = 0
            if sub_job_budgeted_hours > 0:
                sub_job_progress = (sub_job_earned_hours / sub_job_budgeted_hours) * 100
            
            sub_jobs_data.append({
                'id': sub_job.id,
                'name': sub_job.name,
                'budgeted_hours': sub_job_budgeted_hours,
                'earned_hours': sub_job_earned_hours,
                'progress': sub_job_progress
            })
        
        return jsonify({
            'project': {
                'id': project.id,
                'name': project.name,
                'description': project.description
            },
            'overall_progress': overall_progress,
            'total_budgeted_hours': total_budgeted_hours,
            'total_earned_hours': total_earned_hours,
            'sub_jobs': sub_jobs_data
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ===== REPORT ROUTES =====

@main_bp.route('/reports')
def reports():
    """Reports dashboard"""
    try:
        projects = project_service.get_all_projects()
        return render_template('reports.html', projects=projects)
    except Exception as e:
        flash(f'Error loading reports: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('reports.html', projects=[])

@main_bp.route('/generate_project_report/<int:project_id>')
def generate_project_report(project_id):
    """Generate a project report"""
    try:
        project = project_service.get_project_by_id(project_id)
        if not project:
            flash('Project not found', 'danger')
            return redirect(url_for('main.reports'))
        
        # Get all sub jobs for this project
        sub_jobs = sub_job_service.get_sub_jobs_by_project(project_id)
        
        # Get all work items for this project
        work_items = workitem_service.get_workitems_by_project(project_id)
        
        # Calculate project-level totals
        total_budgeted_hours = sum(item.budgeted_man_hours or 0 for item in work_items)
        total_earned_hours = sum(item.earned_man_hours or 0 for item in work_items)
        
        # Calculate overall progress percentage
        overall_progress = 0
        if total_budgeted_hours > 0:
            overall_progress = (total_earned_hours / total_budgeted_hours) * 100
        
        # Create report data
        report_data = {
            'project': project,
            'sub_jobs': sub_jobs,
            'work_items': work_items,
            'total_budgeted_hours': total_budgeted_hours,
            'total_earned_hours': total_earned_hours,
            'overall_progress': overall_progress,
            'generated_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Render report template
        report_html = render_template('report_template.html', **report_data)
        
        # Generate unique filename
        filename = f"project_report_{project.project_id_str}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = os.path.join('reports', filename)
        
        # Ensure reports directory exists
        os.makedirs('reports', exist_ok=True)
        
        # Write report to file
        with open(filepath, 'w') as f:
            f.write(report_html)
        
        # Return file as attachment
        return send_file(filepath, as_attachment=True)
    except Exception as e:
        flash(f'Error generating report: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.reports'))
