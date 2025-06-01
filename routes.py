"""
Fixed routes.py for Magellan EV Tracker v3.0
- Removes all 'discipline' references from SubJob workflows
- Ensures all required template variables are defined
- Fixes variable naming consistency between routes and templates
- Fixes case-sensitivity in URL service import
- Fixes project listing to show newly created projects
- Fixes rule of credit creation by aligning parameter names with database model
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
import traceback
from models import db
from services.project_service import ProjectService
from services.sub_job_service import SubJobService
from services.cost_code_service import CostCodeService
from services.work_item_service import WorkItemService
from services.rule_of_credit_service import RuleOfCreditService
from utils.url_service import UrlService

# Define blueprint
main_bp = Blueprint('main', __name__)

# Index route
@main_bp.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        flash(f"Error loading index: {str(e)}", "error")
        return render_template('index.html')

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
            return redirect(url_for('main.sub_jobs'))
        
        project = ProjectService.get_project_by_id(sub_job.project_id)
        work_items = WorkItemService.get_work_items_by_sub_job(sub_job_id)
        
        # Calculate overall progress
        overall_progress = 0
        if work_items:
            total_budgeted = sum(item.budgeted_man_hours or 0 for item in work_items)
            total_earned = sum(item.earned_man_hours or 0 for item in work_items)
            if total_budgeted > 0:
                overall_progress = (total_earned / total_budgeted) * 100
        
        return render_template('view_sub_job.html', 
                              sub_job=sub_job, 
                              project=project, 
                              work_items=work_items,
                              overall_progress=overall_progress)
    except Exception as e:
        flash(f"Error viewing sub job: {str(e)}", "error")
        return redirect(url_for('main.sub_jobs'))

@main_bp.route('/edit_sub_job/<int:sub_job_id>', methods=['GET', 'POST'])
def edit_sub_job(sub_job_id):
    try:
        sub_job = SubJobService.get_sub_job_by_id(sub_job_id)
        if not sub_job:
            flash("Sub Job not found", "error")
            return redirect(url_for('main.sub_jobs'))
        
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
        return redirect(url_for('main.sub_jobs'))

@main_bp.route('/delete_sub_job/<int:sub_job_id>', methods=['POST'])
def delete_sub_job(sub_job_id):
    try:
        sub_job = SubJobService.get_sub_job_by_id(sub_job_id)
        if not sub_job:
            flash("Sub Job not found", "error")
            return redirect(url_for('main.sub_jobs'))
        
        project_id = sub_job.project_id
        SubJobService.delete_sub_job(sub_job_id)
        flash("Sub Job deleted successfully!", "success")
        return redirect(url_for('main.view_project', project_id=project_id))
    except Exception as e:
        flash(f"Error deleting sub job: {str(e)}", "error")
        return redirect(url_for('main.sub_jobs'))

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
                code = request.form.get('code', '')
                description = request.form.get('description', '')
                discipline = request.form.get('discipline', '')
                rule_of_credit_id = request.form.get('rule_of_credit_id', type=int)
                
                # Create cost code
                cost_code = CostCodeService.create_cost_code(
                    project_id=project_id,
                    code=code,
                    description=description,
                    discipline=discipline,
                    rule_of_credit_id=rule_of_credit_id
                )
                
                flash(f"Cost Code {code} created successfully!", "success")
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

# Rule of Credit routes
@main_bp.route('/rules_of_credit')
def rules_of_credit():
    try:
        rules = RuleOfCreditService.get_all_rules_of_credit()
        return render_template('rules_of_credit.html', rules=rules)
    except Exception as e:
        flash(f"Error loading rules of credit: {str(e)}", "error")
        return render_template('rules_of_credit.html', rules=[])

@main_bp.route('/add_rule_of_credit', methods=['GET', 'POST'])
def add_rule_of_credit():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '')
            description = request.form.get('description', '')
            steps_json = request.form.get('steps_json', '[]')
            
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

@main_bp.route('/edit_rule_of_credit/<int:rule_id>', methods=['GET', 'POST'])
def edit_rule_of_credit(rule_id):
    try:
        rule = RuleOfCreditService.get_rule_of_credit_by_id(rule_id)
        if not rule:
            flash("Rule of Credit not found", "error")
            return redirect(url_for('main.rules_of_credit'))
        
        if request.method == 'POST':
            try:
                name = request.form.get('name', '')
                description = request.form.get('description', '')
                steps_json = request.form.get('steps_json', '[]')
                
                # Update rule of credit
                RuleOfCreditService.update_rule_of_credit(
                    rule_id=rule_id,
                    name=name,
                    description=description,
                    steps_json=steps_json
                )
                
                flash(f"Rule of Credit {name} updated successfully!", "success")
                return redirect(url_for('main.rules_of_credit'))
            except Exception as e:
                flash(f"Error updating rule of credit: {str(e)}", "error")
                return render_template('edit_rule_of_credit.html', rule=rule)
        
        return render_template('edit_rule_of_credit.html', rule=rule)
    except Exception as e:
        flash(f"Error editing rule of credit: {str(e)}", "error")
        return redirect(url_for('main.rules_of_credit'))

@main_bp.route('/delete_rule_of_credit/<int:rule_id>', methods=['POST'])
def delete_rule_of_credit(rule_id):
    try:
        RuleOfCreditService.delete_rule_of_credit(rule_id)
        flash("Rule of Credit deleted successfully!", "success")
    except Exception as e:
        flash(f"Error deleting rule of credit: {str(e)}", "error")
    
    return redirect(url_for('main.rules_of_credit'))

# Work Item routes
@main_bp.route('/work_items')
def work_items():
    try:
        project_id = request.args.get('project_id', type=int)
        sub_job_id = request.args.get('sub_job_id', type=int)
        
        if sub_job_id:
            sub_job = SubJobService.get_sub_job_by_id(sub_job_id)
            work_items = WorkItemService.get_work_items_by_sub_job(sub_job_id)
            return render_template('work_items.html', work_items=work_items, sub_job=sub_job, project=None)
        elif project_id:
            project = ProjectService.get_project_by_id(project_id)
            work_items = WorkItemService.get_work_items_by_project(project_id)
            return render_template('work_items.html', work_items=work_items, sub_job=None, project=project)
        else:
            work_items = WorkItemService.get_all_work_items()
            return render_template('work_items.html', work_items=work_items, sub_job=None, project=None)
    except Exception as e:
        flash(f"Error loading work items: {str(e)}", "error")
        return render_template('work_items.html', work_items=[], sub_job=None, project=None)

@main_bp.route('/add_work_item', methods=['GET', 'POST'])
def add_work_item():
    try:
        project_id = request.args.get('project_id', type=int)
        sub_job_id = request.args.get('sub_job_id', type=int)
        
        if request.method == 'POST':
            try:
                project_id = request.form.get('project_id', type=int)
                sub_job_id = request.form.get('sub_job_id', type=int)
                cost_code_id = request.form.get('cost_code_id', type=int)
                work_item_id_str = request.form.get('work_item_id_str', '')
                description = request.form.get('description', '')
                budgeted_quantity = request.form.get('budgeted_quantity', type=float)
                unit_of_measure = request.form.get('unit_of_measure', '')
                budgeted_man_hours = request.form.get('budgeted_man_hours', type=float)
                
                # Create work item
                work_item = WorkItemService.create_work_item(
                    project_id=project_id,
                    sub_job_id=sub_job_id,
                    cost_code_id=cost_code_id,
                    work_item_id_str=work_item_id_str,
                    description=description,
                    budgeted_quantity=budgeted_quantity,
                    unit_of_measure=unit_of_measure,
                    budgeted_man_hours=budgeted_man_hours
                )
                
                flash(f"Work Item {work_item_id_str} created successfully!", "success")
                return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))
            except Exception as e:
                flash(f"Error creating work item: {str(e)}", "error")
                projects = ProjectService.get_all_projects()
                sub_jobs = []
                cost_codes = []
                
                if project_id:
                    sub_jobs = SubJobService.get_sub_jobs_by_project(project_id)
                    cost_codes = CostCodeService.get_cost_codes_by_project(project_id)
                
                return render_template('add_work_item.html', 
                                      projects=projects, 
                                      sub_jobs=sub_jobs, 
                                      cost_codes=cost_codes,
                                      selected_project_id=project_id,
                                      selected_sub_job_id=sub_job_id)
        
        projects = ProjectService.get_all_projects()
        sub_jobs = []
        cost_codes = []
        
        if project_id:
            sub_jobs = SubJobService.get_sub_jobs_by_project(project_id)
            cost_codes = CostCodeService.get_cost_codes_by_project(project_id)
        
        return render_template('add_work_item.html', 
                              projects=projects, 
                              sub_jobs=sub_jobs, 
                              cost_codes=cost_codes,
                              selected_project_id=project_id,
                              selected_sub_job_id=sub_job_id)
    except Exception as e:
        flash(f"Error loading add work item form: {str(e)}", "error")
        return redirect(url_for('main.projects'))

@main_bp.route('/view_work_item/<int:work_item_id>')
def view_work_item(work_item_id):
    try:
        work_item = WorkItemService.get_work_item_by_id(work_item_id)
        if not work_item:
            flash("Work Item not found", "error")
            return redirect(url_for('main.work_items'))
        
        sub_job = SubJobService.get_sub_job_by_id(work_item.sub_job_id)
        project = ProjectService.get_project_by_id(work_item.project_id)
        cost_code = CostCodeService.get_cost_code_by_id(work_item.cost_code_id)
        
        return render_template('view_work_item.html', 
                              work_item=work_item, 
                              sub_job=sub_job, 
                              project=project,
                              cost_code=cost_code)
    except Exception as e:
        flash(f"Error viewing work item: {str(e)}", "error")
        return redirect(url_for('main.work_items'))

@main_bp.route('/edit_work_item/<int:work_item_id>', methods=['GET', 'POST'])
def edit_work_item(work_item_id):
    try:
        work_item = WorkItemService.get_work_item_by_id(work_item_id)
        if not work_item:
            flash("Work Item not found", "error")
            return redirect(url_for('main.work_items'))
        
        if request.method == 'POST':
            try:
                description = request.form.get('description', '')
                budgeted_quantity = request.form.get('budgeted_quantity', type=float)
                unit_of_measure = request.form.get('unit_of_measure', '')
                budgeted_man_hours = request.form.get('budgeted_man_hours', type=float)
                
                # Update work item
                WorkItemService.update_work_item(
                    work_item_id=work_item_id,
                    description=description,
                    budgeted_quantity=budgeted_quantity,
                    unit_of_measure=unit_of_measure,
                    budgeted_man_hours=budgeted_man_hours
                )
                
                flash(f"Work Item updated successfully!", "success")
                return redirect(url_for('main.view_work_item', work_item_id=work_item_id))
            except Exception as e:
                flash(f"Error updating work item: {str(e)}", "error")
                return render_template('edit_work_item.html', work_item=work_item)
        
        return render_template('edit_work_item.html', work_item=work_item)
    except Exception as e:
        flash(f"Error editing work item: {str(e)}", "error")
        return redirect(url_for('main.work_items'))

@main_bp.route('/delete_work_item/<int:work_item_id>', methods=['POST'])
def delete_work_item(work_item_id):
    try:
        work_item = WorkItemService.get_work_item_by_id(work_item_id)
        if not work_item:
            flash("Work Item not found", "error")
            return redirect(url_for('main.work_items'))
        
        sub_job_id = work_item.sub_job_id
        WorkItemService.delete_work_item(work_item_id)
        flash("Work Item deleted successfully!", "success")
        return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))
    except Exception as e:
        flash(f"Error deleting work item: {str(e)}", "error")
        return redirect(url_for('main.work_items'))

@main_bp.route('/update_work_item_progress/<int:work_item_id>', methods=['GET', 'POST'])
def update_work_item_progress(work_item_id):
    try:
        work_item = WorkItemService.get_work_item_by_id(work_item_id)
        if not work_item:
            flash("Work Item not found", "error")
            return redirect(url_for('main.work_items'))
        
        cost_code = CostCodeService.get_cost_code_by_id(work_item.cost_code_id)
        if not cost_code or not cost_code.rule_of_credit_id:
            flash("No Rule of Credit associated with this Work Item's Cost Code", "error")
            return redirect(url_for('main.view_work_item', work_item_id=work_item_id))
        
        rule = RuleOfCreditService.get_rule_of_credit_by_id(cost_code.rule_of_credit_id)
        if not rule:
            flash("Rule of Credit not found", "error")
            return redirect(url_for('main.view_work_item', work_item_id=work_item_id))
        
        if request.method == 'POST':
            try:
                # Get progress data from form
                progress_data = {}
                for step in rule.get_steps():
                    step_name = step.get('name', '')
                    if step_name:
                        progress_value = request.form.get(f"progress_{step_name}", type=float, default=0)
                        progress_data[step_name] = progress_value
                
                # Update work item progress
                WorkItemService.update_work_item_progress(
                    work_item_id=work_item_id,
                    progress_data=progress_data
                )
                
                flash(f"Work Item progress updated successfully!", "success")
                return redirect(url_for('main.view_work_item', work_item_id=work_item_id))
            except Exception as e:
                flash(f"Error updating work item progress: {str(e)}", "error")
                return render_template('update_work_item_progress.html', 
                                      work_item=work_item, 
                                      rule=rule,
                                      current_progress=work_item.get_steps_progress())
        
        return render_template('update_work_item_progress.html', 
                              work_item=work_item, 
                              rule=rule,
                              current_progress=work_item.get_steps_progress())
    except Exception as e:
        flash(f"Error loading update progress form: {str(e)}", "error")
        return redirect(url_for('main.view_work_item', work_item_id=work_item_id))

# Reports routes
@main_bp.route('/reports')
def reports():
    try:
        projects = ProjectService.get_all_projects()
        return render_template('reports.html', projects=projects)
    except Exception as e:
        flash(f"Error loading reports: {str(e)}", "error")
        return render_template('reports.html', projects=[])
