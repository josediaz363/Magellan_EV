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
        cost_codes = costcode_service.get_all_costcodes()
        projects = project_service.get_all_projects()
        disciplines = costcode_service.get_discipline_choices()
        return render_template('list_cost_codes.html', 
                              cost_codes=cost_codes, 
                              projects=projects, 
                              disciplines=disciplines)
    except Exception as e:
        flash(f'Error loading cost codes: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('list_cost_codes.html', 
                              cost_codes=[], 
                              projects=[], 
                              disciplines=[])

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
        rules = ruleofcredit_service.get_all_rulesofcredit()  # Changed variable name to match template
        disciplines = costcode_service.get_discipline_choices()
        
        return render_template('add_cost_code.html', 
                              projects=projects, 
                              rules=rules,  # Changed variable name to match template
                              disciplines=disciplines)
    except Exception as e:
        flash(f'Error adding cost code: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_cost_codes'))

@main_bp.route('/edit_cost_code/<int:cost_code_id>', methods=['GET', 'POST'])
def edit_cost_code(cost_code_id):
    """Edit a cost code"""
    try:
        costcode = costcode_service.get_costcode_by_id(cost_code_id)
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
                cost_code_id, description, discipline, rule_of_credit_id)
            
            if updated_costcode:
                flash('Cost code updated successfully!', 'success')
                return redirect(url_for('main.list_cost_codes'))
            else:
                flash('Error updating cost code', 'danger')
        
        rules_of_credit = ruleofcredit_service.get_all_rulesofcredit()
        disciplines = costcode_service.get_discipline_choices()
        
        return render_template('edit_cost_code.html', 
                              costcode=costcode, 
                              rules=rules_of_credit,  # Changed variable name to match template
                              disciplines=disciplines)
    except Exception as e:
        flash(f'Error editing cost code: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_cost_codes'))

@main_bp.route('/delete_cost_code/<int:cost_code_id>', methods=['POST'])
def delete_cost_code(cost_code_id):
    """Delete a cost code"""
    try:
        if costcode_service.delete_costcode(cost_code_id):
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
            
            # Parse steps from form
            steps = []
            i = 0
            while f'step_name_{i}' in request.form:
                step_name = request.form.get(f'step_name_{i}')
                step_percentage = float(request.form.get(f'step_percentage_{i}'))
                steps.append((step_name, step_percentage))
                i += 1
            
            new_rule = ruleofcredit_service.create_ruleofcredit(name, description, steps)
            
            if new_rule:
                flash('Rule of credit added successfully!', 'success')
                return redirect(url_for('main.list_rules_of_credit'))
            else:
                flash('Error adding rule of credit', 'danger')
        
        return render_template('add_rule_of_credit.html')
    except Exception as e:
        flash(f'Error adding rule of credit: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_rules_of_credit'))

@main_bp.route('/edit_rule_of_credit/<int:rule_id>', methods=['GET', 'POST'])
def edit_rule_of_credit(rule_id):
    """Edit a rule of credit"""
    try:
        rule = ruleofcredit_service.get_ruleofcredit_by_id(rule_id)
        if not rule:
            flash('Rule of credit not found', 'danger')
            return redirect(url_for('main.list_rules_of_credit'))
        
        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description')
            
            # Parse steps from form
            steps = []
            i = 0
            while f'step_name_{i}' in request.form:
                step_name = request.form.get(f'step_name_{i}')
                step_percentage = float(request.form.get(f'step_percentage_{i}'))
                steps.append((step_name, step_percentage))
                i += 1
            
            updated_rule = ruleofcredit_service.update_ruleofcredit(rule_id, name, description, steps)
            
            if updated_rule:
                flash('Rule of credit updated successfully!', 'success')
                return redirect(url_for('main.list_rules_of_credit'))
            else:
                flash('Error updating rule of credit', 'danger')
        
        # Parse steps from JSON
        steps = ruleofcredit_service.get_steps_for_rule(rule_id)
        
        return render_template('edit_rule_of_credit.html', rule=rule, steps=steps)
    except Exception as e:
        flash(f'Error editing rule of credit: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_rules_of_credit'))

@main_bp.route('/delete_rule_of_credit/<int:rule_id>', methods=['POST'])
def delete_rule_of_credit(rule_id):
    """Delete a rule of credit"""
    try:
        success = ruleofcredit_service.delete_ruleofcredit(rule_id)
        
        if success:
            flash('Rule of credit deleted successfully!', 'success')
        else:
            flash('Error deleting rule of credit', 'danger')
        
        return redirect(url_for('main.list_rules_of_credit'))
    except Exception as e:
        flash(f'Error deleting rule of credit: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_rules_of_credit'))

# ===== WORK ITEM ROUTES =====

@main_bp.route('/work_items')
def list_work_items():
    """List all work items"""
    try:
        work_items = workitem_service.get_workitems_with_related_data()
        return render_template('work_items.html', work_items=work_items)
    except Exception as e:
        flash(f'Error loading work items: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('work_items.html', work_items=[])

# Add an alias route for work_items to fix template reference
@main_bp.route('/work_items_alias')
def work_items():
    """Alias for list_work_items to maintain compatibility with templates"""
    return list_work_items()

@main_bp.route('/add_work_item/<int:sub_job_id>', methods=['GET', 'POST'])
def add_work_item(sub_job_id):
    """Add a new work item"""
    try:
        sub_job = sub_job_service.get_sub_job_by_id(sub_job_id)
        if not sub_job:
            flash('Sub job not found', 'danger')
            return redirect(url_for('main.projects'))
        
        if request.method == 'POST':
            work_item_id_str = request.form.get('work_item_id_str') or f"WI-{uuid.uuid4().hex[:8].upper()}"
            description = request.form.get('description')
            project_id = request.form.get('project_id')
            cost_code_id = request.form.get('cost_code_id')
            
            # Parse numeric values
            try:
                budgeted_quantity = float(request.form.get('budgeted_quantity') or 0)
            except ValueError:
                budgeted_quantity = 0
                
            try:
                budgeted_man_hours = float(request.form.get('budgeted_man_hours') or 0)
            except ValueError:
                budgeted_man_hours = 0
                
            unit_of_measure = request.form.get('unit_of_measure')
            
            new_workitem = workitem_service.create_workitem(
                work_item_id_str, description, project_id, sub_job_id, cost_code_id,
                budgeted_quantity, unit_of_measure, budgeted_man_hours)
            
            if new_workitem:
                flash('Work item added successfully!', 'success')
                return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))
            else:
                flash('Error adding work item', 'danger')
        
        # Get all projects for dropdown
        projects = project_service.get_all_projects()
        
        # Get all sub jobs for dropdown
        sub_jobs = sub_job_service.get_sub_jobs_by_project(sub_job.project_id)
        
        # Get all cost codes for dropdown
        cost_codes = costcode_service.get_costcodes_by_project(sub_job.project_id)
        
        return render_template('add_work_item.html', 
                              sub_job=sub_job,
                              pre_selected_sub_job=sub_job,
                              pre_selected_project=project_service.get_project_by_id(sub_job.project_id),
                              projects=projects,
                              sub_jobs=sub_jobs,
                              cost_codes=cost_codes)
    except Exception as e:
        flash(f'Error adding work item: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))

@main_bp.route('/work_item/<int:work_item_id>')
def view_work_item(work_item_id):
    """View a specific work item"""
    try:
        work_item = workitem_service.get_workitem_by_id(work_item_id)
        if not work_item:
            flash('Work item not found', 'danger')
            return redirect(url_for('main.list_work_items'))
        
        # Get related entities
        project = project_service.get_project_by_id(work_item.project_id)
        sub_job = sub_job_service.get_sub_job_by_id(work_item.sub_job_id)
        cost_code = costcode_service.get_costcode_by_id(work_item.cost_code_id) if work_item.cost_code_id else None
        
        # Get progress steps
        progress_steps = []
        if work_item.progress_json:
            try:
                progress_steps = json.loads(work_item.progress_json)
            except:
                progress_steps = []
        
        # Get progress history
        progress_history = workitem_service.get_workitem_progress_history(work_item_id)
        
        return render_template('view_work_item.html', 
                              work_item=work_item,
                              project=project,
                              sub_job=sub_job,
                              cost_code=cost_code,
                              progress_steps=progress_steps,
                              progress_history=progress_history)
    except Exception as e:
        flash(f'Error loading work item: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_work_items'))

@main_bp.route('/edit_work_item/<int:work_item_id>', methods=['GET', 'POST'])
def edit_work_item(work_item_id):
    """Edit a work item"""
    try:
        work_item = workitem_service.get_workitem_by_id(work_item_id)
        if not work_item:
            flash('Work item not found', 'danger')
            return redirect(url_for('main.list_work_items'))
        
        if request.method == 'POST':
            description = request.form.get('description')
            
            # Parse numeric values
            try:
                budgeted_quantity = float(request.form.get('budgeted_quantity') or 0)
            except ValueError:
                budgeted_quantity = 0
                
            try:
                budgeted_man_hours = float(request.form.get('budgeted_man_hours') or 0)
            except ValueError:
                budgeted_man_hours = 0
                
            unit_of_measure = request.form.get('unit_of_measure')
            
            updated_workitem = workitem_service.update_workitem(
                work_item_id, description, budgeted_quantity, unit_of_measure, budgeted_man_hours)
            
            if updated_workitem:
                flash('Work item updated successfully!', 'success')
                return redirect(url_for('main.view_work_item', work_item_id=work_item_id))
            else:
                flash('Error updating work item', 'danger')
        
        # Get related entities
        project = project_service.get_project_by_id(work_item.project_id)
        sub_job = sub_job_service.get_sub_job_by_id(work_item.sub_job_id)
        cost_code = costcode_service.get_costcode_by_id(work_item.cost_code_id) if work_item.cost_code_id else None
        
        return render_template('edit_work_item.html', 
                              work_item=work_item,
                              project=project,
                              sub_job=sub_job,
                              cost_code=cost_code)
    except Exception as e:
        flash(f'Error editing work item: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_work_items'))

@main_bp.route('/delete_work_item/<int:work_item_id>', methods=['POST'])
def delete_work_item(work_item_id):
    """Delete a work item"""
    try:
        work_item = workitem_service.get_workitem_by_id(work_item_id)
        if not work_item:
            flash('Work item not found', 'danger')
            return redirect(url_for('main.list_work_items'))
        
        sub_job_id = work_item.sub_job_id
        
        if workitem_service.delete_workitem(work_item_id):
            flash('Work item deleted successfully!', 'success')
        else:
            flash('Error deleting work item', 'danger')
        
        return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))
    except Exception as e:
        flash(f'Error deleting work item: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_work_items'))

@main_bp.route('/update_work_item_progress/<int:work_item_id>', methods=['GET', 'POST'])
def update_work_item_progress(work_item_id):
    """Update progress for a work item"""
    try:
        work_item = workitem_service.get_workitem_by_id(work_item_id)
        if not work_item:
            flash('Work item not found', 'danger')
            return redirect(url_for('main.list_work_items'))
        
        # Get cost code and rule of credit
        cost_code = None
        rule = None
        steps = []
        
        if work_item.cost_code_id:
            cost_code = costcode_service.get_costcode_by_id(work_item.cost_code_id)
            if cost_code and cost_code.rule_of_credit_id:
                rule = ruleofcredit_service.get_ruleofcredit_by_id(cost_code.rule_of_credit_id)
                steps = ruleofcredit_service.get_steps_for_rule(rule.id)
        
        if request.method == 'POST':
            # Update progress for each step
            for i, step in enumerate(steps):
                step_name = step['name']
                completion_percentage = float(request.form.get(f'step_{i}_completion') or 0)
                
                workitem_service.update_progress_step(work_item_id, step_name, completion_percentage)
            
            flash('Progress updated successfully!', 'success')
            return redirect(url_for('main.view_work_item', work_item_id=work_item_id))
        
        # Get current progress
        current_progress = {}
        if work_item.progress_json:
            try:
                progress_data = json.loads(work_item.progress_json)
                for step in progress_data:
                    current_progress[step['name']] = step['completion_percentage']
            except:
                pass
        
        # Get related entities
        project = project_service.get_project_by_id(work_item.project_id)
        sub_job = sub_job_service.get_sub_job_by_id(work_item.sub_job_id)
        
        return render_template('update_work_item_progress.html', 
                              work_item=work_item,
                              project=project,
                              sub_job=sub_job,
                              cost_code=cost_code,
                              rule=rule,
                              steps=steps,
                              current_progress=current_progress)
    except Exception as e:
        flash(f'Error updating work item progress: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.view_work_item', work_item_id=work_item_id))

# ===== REPORTS ROUTES =====

@main_bp.route('/reports')
def reports_index():
    """Reports index page"""
    try:
        projects = project_service.get_all_projects()
        return render_template('reports_index.html', projects=projects)
    except Exception as e:
        flash(f'Error loading reports: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('reports_index.html', projects=[])

@main_bp.route('/generate_project_report/<int:project_id>')
def generate_project_report(project_id):
    """Generate a project report"""
    try:
        # Get project data
        project = project_service.get_project_by_id(project_id)
        if not project:
            flash('Project not found', 'danger')
            return redirect(url_for('main.reports_index'))
        
        # Get sub jobs
        sub_jobs = sub_job_service.get_sub_jobs_by_project(project_id)
        
        # Get work items
        work_items = workitem_service.get_workitems_by_project(project_id)
        
        # Calculate project-level totals
        total_budgeted_hours = sum(item.budgeted_man_hours or 0 for item in work_items)
        total_earned_hours = sum(item.earned_man_hours or 0 for item in work_items)
        
        # Calculate overall progress percentage
        overall_progress = 0
        if total_budgeted_hours > 0:
            overall_progress = (total_earned_hours / total_budgeted_hours) * 100
        
        # Generate report HTML
        report_html = render_template('reports/project_report.html',
                                     project=project,
                                     sub_jobs=sub_jobs,
                                     work_items=work_items,
                                     total_budgeted_hours=total_budgeted_hours,
                                     total_earned_hours=total_earned_hours,
                                     overall_progress=overall_progress,
                                     generation_date=datetime.datetime.now())
        
        # Create a PDF from the HTML
        from weasyprint import HTML
        pdf = HTML(string=report_html).write_pdf()
        
        # Create a response with the PDF
        buffer = io.BytesIO(pdf)
        buffer.seek(0)
        
        return send_file(
            buffer,
            download_name=f"project_report_{project.project_id_str}_{datetime.datetime.now().strftime('%Y%m%d')}.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        flash(f'Error generating project report: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.reports_index'))

# ===== API ROUTES =====

@main_bp.route('/api/projects')
def api_projects():
    """API endpoint for projects"""
    try:
        projects = project_service.get_all_projects()
        return jsonify([{
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'project_id_str': p.project_id_str
        } for p in projects])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/project/<int:project_id>/sub_jobs')
def api_project_sub_jobs(project_id):
    """API endpoint for sub jobs in a project"""
    try:
        sub_jobs = sub_job_service.get_sub_jobs_by_project(project_id)
        return jsonify([{
            'id': sj.id,
            'name': sj.name,
            'description': sj.description,
            'sub_job_id_str': sj.sub_job_id_str,
            'area': sj.area
        } for sj in sub_jobs])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/sub_job/<int:sub_job_id>/work_items')
def api_sub_job_work_items(sub_job_id):
    """API endpoint for work items in a sub job"""
    try:
        work_items = workitem_service.get_workitems_by_subjob(sub_job_id)
        return jsonify([{
            'id': wi.id,
            'description': wi.description,
            'work_item_id_str': wi.work_item_id_str,
            'budgeted_quantity': wi.budgeted_quantity,
            'earned_quantity': wi.earned_quantity,
            'budgeted_man_hours': wi.budgeted_man_hours,
            'earned_man_hours': wi.earned_man_hours,
            'percent_complete_hours': wi.percent_complete_hours
        } for wi in work_items])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/project/<int:project_id>/progress')
def api_project_progress(project_id):
    """API endpoint for project progress data"""
    try:
        # Get all work items for this project
        work_items = workitem_service.get_workitems_by_project(project_id)
        
        # Calculate totals
        total_budgeted_hours = sum(item.budgeted_man_hours or 0 for item in work_items)
        total_earned_hours = sum(item.earned_man_hours or 0 for item in work_items)
        
        # Calculate overall progress percentage
        overall_progress = 0
        if total_budgeted_hours > 0:
            overall_progress = (total_earned_hours / total_budgeted_hours) * 100
        
        # Get sub jobs
        sub_jobs = sub_job_service.get_sub_jobs_by_project(project_id)
        
        # Calculate progress for each sub job
        sub_job_progress = []
        for sub_job in sub_jobs:
            sub_job_data = sub_job_service.get_sub_job_metrics(sub_job.id)
            if sub_job_data:
                sub_job_progress.append({
                    'id': sub_job.id,
                    'name': sub_job.name,
                    'progress': sub_job_data['overall_progress']
                })
        
        return jsonify({
            'overall_progress': overall_progress,
            'total_budgeted_hours': total_budgeted_hours,
            'total_earned_hours': total_earned_hours,
            'sub_job_progress': sub_job_progress
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/donut_chart_data/<int:project_id>')
def api_donut_chart_data(project_id):
    """API endpoint for donut chart data"""
    try:
        # Get all sub jobs for this project
        sub_jobs = sub_job_service.get_sub_jobs_by_project(project_id)
        
        # Calculate progress for each sub job
        data = []
        for sub_job in sub_jobs:
            sub_job_data = sub_job_service.get_sub_job_metrics(sub_job.id)
            if sub_job_data:
                data.append({
                    'label': sub_job.name,
                    'value': sub_job_data['overall_progress'],
                    'color': f'hsl({(len(data) * 30) % 360}, 70%, 50%)'  # Generate different colors
                })
        
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
