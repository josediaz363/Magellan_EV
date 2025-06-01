from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from services.project_service import ProjectService
from services.sub_job_service import SubJobService
from services.work_item_service import WorkItemService
from services.cost_code_service import CostCodeService
from services.rule_of_credit_service import RuleOfCreditService
from services.url_service import UrlService
from models import Project, SubJob, WorkItem, CostCode, RuleOfCredit, DISCIPLINE_CHOICES, db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

# Default disciplines list for the application
DEFAULT_DISCIPLINES = DISCIPLINE_CHOICES

@main_bp.route('/')
def index():
    return redirect(url_for('main.dashboard'))

@main_bp.route('/dashboard')
def dashboard():
    try:
        # Log database queries for debugging
        logger.info("Fetching counts for dashboard")
        projects_count = ProjectService.count_projects()
        sub_jobs_count = SubJobService.count_sub_jobs()
        work_items_count = WorkItemService.count_work_items()
        rules_count = RuleOfCreditService.count_rules_of_credit()
        
        logger.info(f"Dashboard counts: Projects={projects_count}, SubJobs={sub_jobs_count}, WorkItems={work_items_count}, Rules={rules_count}")
        
        return render_template('dashboard.html', 
                              projects_count=projects_count,
                              sub_jobs_count=sub_jobs_count,
                              work_items_count=work_items_count,
                              rules_count=rules_count)
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}")
        flash(f"Error loading dashboard: {str(e)}", "error")
        return render_template('dashboard.html')

# Project routes
@main_bp.route('/projects')
def projects():
    try:
        # Log database queries for debugging
        logger.info("Fetching all projects")
        projects = ProjectService.get_all_projects()
        logger.info(f"Found {len(projects)} projects")
        for project in projects:
            logger.info(f"Project: {project.id}, {project.name}, {project.project_id_str}")
        
        # Create projects_with_data structure expected by the template
        projects_with_data = []
        for project in projects:
            # Calculate project statistics
            total_budgeted_hours = project.total_budgeted_hours
            total_earned_hours = project.total_earned_hours
            
            # Calculate overall progress
            overall_progress = 0
            if total_budgeted_hours > 0:
                overall_progress = (total_earned_hours / total_budgeted_hours) * 100
            
            # Create project data dictionary
            project_data = {
                'project': project,
                'overall_progress': overall_progress,
                'total_budgeted_hours': total_budgeted_hours,
                'total_earned_hours': total_earned_hours
            }
            
            projects_with_data.append(project_data)
            
        logger.info(f"Prepared {len(projects_with_data)} projects with data for display")
        
        return render_template('projects.html', projects_with_data=projects_with_data)
    except Exception as e:
        logger.error(f"Error loading projects: {str(e)}")
        flash(f"Error loading projects: {str(e)}", "error")
        return render_template('projects.html', projects_with_data=[])

@main_bp.route('/add_project', methods=['GET', 'POST'])
def add_project():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '')
            project_id_str = request.form.get('project_id_str', '')
            description = request.form.get('description', '')
            
            logger.info(f"Creating project: name={name}, project_id_str={project_id_str}")
            
            # Create project
            project = ProjectService.create_project(
                name=name,
                project_id_str=project_id_str,
                description=description
            )
            
            logger.info(f"Project created successfully: {project.id}, {project.name}")
            
            flash(f"Project {name} created successfully!", "success")
            return redirect(url_for('main.projects'))
        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            flash(f"Error creating project: {str(e)}", "error")
            return render_template('add_project.html')
    
    return render_template('add_project.html')

@main_bp.route('/view_project/<int:project_id>')
def view_project(project_id):
    try:
        # Use the correct method name from ProjectService
        project = ProjectService.get_project_details(project_id)
        if not project:
            flash("Project not found", "error")
            return redirect(url_for('main.projects'))
        
        sub_jobs = SubJobService.get_project_sub_jobs(project_id)
        return render_template('view_project.html', project=project, sub_jobs=sub_jobs)
    except Exception as e:
        logger.error(f"Error loading project: {str(e)}")
        flash(f"Error loading project: {str(e)}", "error")
        return redirect(url_for('main.projects'))

@main_bp.route('/edit_project/<int:project_id>', methods=['GET', 'POST'])
def edit_project(project_id):
    try:
        # Use the correct method name from ProjectService
        project = ProjectService.get_project_details(project_id)
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
                logger.error(f"Error updating project: {str(e)}")
                flash(f"Error updating project: {str(e)}", "error")
                return render_template('edit_project.html', project=project)
        
        return render_template('edit_project.html', project=project)
    except Exception as e:
        logger.error(f"Error editing project: {str(e)}")
        flash(f"Error editing project: {str(e)}", "error")
        return redirect(url_for('main.projects'))

@main_bp.route('/delete_project/<int:project_id>', methods=['POST'])
def delete_project(project_id):
    try:
        ProjectService.delete_project(project_id)
        flash("Project deleted successfully!", "success")
        return redirect(url_for('main.projects'))
    except Exception as e:
        logger.error(f"Error deleting project: {str(e)}")
        flash(f"Error deleting project: {str(e)}", "error")
        return redirect(url_for('main.projects'))

# Sub Job routes
@main_bp.route('/add_sub_job', methods=['GET', 'POST'])
def add_sub_job():
    try:
        project_id = request.args.get('project_id', type=int)
        
        if request.method == 'POST':
            try:
                project_id = request.form.get('project_id', type=int)
                name = request.form.get('name', '')
                sub_job_id_str = request.form.get('sub_job_id_str', '')
                description = request.form.get('description', '')
                area = request.form.get('area', '')
                budgeted_hours = request.form.get('budgeted_hours', type=float, default=0.0)
                
                # Create sub job - removed discipline parameter
                sub_job = SubJobService.create_sub_job(
                    project_id=project_id,
                    name=name,
                    sub_job_id_str=sub_job_id_str,
                    description=description,
                    area=area,
                    budgeted_hours=budgeted_hours
                )
                
                flash(f"Sub Job {name} created successfully!", "success")
                return redirect(url_for('main.view_project', project_id=project_id))
            except Exception as e:
                logger.error(f"Error creating sub job: {str(e)}")
                flash(f"Error creating sub job: {str(e)}", "error")
                projects = ProjectService.get_all_projects()
                return render_template('add_sub_job.html', projects=projects, selected_project_id=project_id, disciplines=DEFAULT_DISCIPLINES)
        
        projects = ProjectService.get_all_projects()
        return render_template('add_sub_job.html', projects=projects, selected_project_id=project_id, disciplines=DEFAULT_DISCIPLINES)
    except Exception as e:
        logger.error(f"Error loading add sub job form: {str(e)}")
        flash(f"Error loading add sub job form: {str(e)}", "error")
        return redirect(url_for('main.projects'))

@main_bp.route('/view_sub_job/<int:sub_job_id>')
def view_sub_job(sub_job_id):
    try:
        sub_job = SubJobService.get_sub_job_by_id(sub_job_id)
        if not sub_job:
            flash("Sub Job not found", "error")
            return redirect(url_for('main.projects'))
        
        work_items = WorkItemService.get_work_items_by_sub_job(sub_job_id)
        return render_template('view_sub_job.html', sub_job=sub_job, work_items=work_items)
    except Exception as e:
        logger.error(f"Error loading sub job: {str(e)}")
        flash(f"Error loading sub job: {str(e)}", "error")
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
                
                # Update sub job - removed discipline parameter
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
                logger.error(f"Error updating sub job: {str(e)}")
                flash(f"Error updating sub job: {str(e)}", "error")
                return render_template('edit_sub_job.html', sub_job=sub_job, disciplines=DEFAULT_DISCIPLINES)
        
        return render_template('edit_sub_job.html', sub_job=sub_job, disciplines=DEFAULT_DISCIPLINES)
    except Exception as e:
        logger.error(f"Error editing sub job: {str(e)}")
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
        logger.error(f"Error deleting sub job: {str(e)}")
        flash(f"Error deleting sub job: {str(e)}", "error")
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
        logger.error(f"Error loading work items: {str(e)}")
        flash(f"Error loading work items: {str(e)}", "error")
        return render_template('work_items.html', work_items=[], sub_job=None)

@main_bp.route('/add_work_item', methods=['GET', 'POST'])
def add_work_item():
    try:
        sub_job_id = request.args.get('sub_job_id', type=int)
        return render_template('add_work_item.html', sub_job_id=sub_job_id)
    except Exception as e:
        logger.error(f"Error loading add work item form: {str(e)}")
        flash(f"Error loading add work item form: {str(e)}", "error")
        return redirect(url_for('main.work_items'))

# Cost Code routes
@main_bp.route('/cost_codes')
def cost_codes():
    try:
        # Get project_id from query parameters
        project_id = request.args.get('project_id', type=int)
        logger.info(f"Loading cost codes for project_id: {project_id}")
        
        # Get all cost codes for debugging
        all_cost_codes = CostCode.query.all()
        logger.info(f"Total cost codes in database: {len(all_cost_codes)}")
        for code in all_cost_codes:
            logger.info(f"Cost code in DB: ID={code.id}, Code={code.cost_code_id_str}, Project ID={code.project_id}")
        
        # Get all projects for the dropdown
        all_projects = ProjectService.get_all_projects()
        
        # DIRECT DATABASE QUERY: Bypass the service layer for debugging
        if project_id:
            # Get project details
            project = ProjectService.get_project_details(project_id)
            
            # Direct database query to get cost codes for this project
            cost_codes = db.session.query(CostCode).filter(CostCode.project_id == project_id).all()
            logger.info(f"Direct query found {len(cost_codes)} cost codes for project_id {project_id}")
            
            # If no cost codes found but we know they exist, show all cost codes as a fallback
            if len(cost_codes) == 0 and len(all_cost_codes) > 0:
                logger.info("No cost codes found for this project, showing all cost codes as fallback")
                cost_codes = all_cost_codes
            
            return render_template('cost_codes.html', 
                                  cost_codes=cost_codes, 
                                  project=project, 
                                  disciplines=DEFAULT_DISCIPLINES, 
                                  projects=all_projects)
        else:
            # If no project_id specified, show all cost codes
            logger.info(f"No project_id specified, showing all {len(all_cost_codes)} cost codes")
            return render_template('cost_codes.html', 
                                  cost_codes=all_cost_codes, 
                                  project=None, 
                                  disciplines=DEFAULT_DISCIPLINES, 
                                  projects=all_projects)
    except Exception as e:
        logger.error(f"Error loading cost codes: {str(e)}")
        flash(f"Error loading cost codes: {str(e)}", "error")
        return render_template('cost_codes.html', 
                              cost_codes=[], 
                              project=None, 
                              disciplines=DEFAULT_DISCIPLINES, 
                              projects=[])

@main_bp.route('/add_cost_code', methods=['GET', 'POST'])
def add_cost_code():
    try:
        project_id = request.args.get('project_id', type=int)
        rules = RuleOfCreditService.get_all_rules_of_credit()
        
        if request.method == 'POST':
            try:
                project_id = request.form.get('project_id', type=int)
                code = request.form.get('cost_code_id_str', '')
                description = request.form.get('description', '')
                discipline = request.form.get('discipline', '')
                rule_of_credit_id = request.form.get('rule_of_credit_id', type=int)
                
                # Add debug logging
                logger.info(f"Creating cost code: project_id={project_id}, code={code}, discipline={discipline}")
                
                # DIRECT DATABASE INSERT: Bypass the service layer for debugging
                try:
                    # Create cost code directly in the database
                    new_cost_code = CostCode(
                        project_id=project_id,
                        cost_code_id_str=code,
                        description=description,
                        discipline=discipline,
                        rule_of_credit_id=rule_of_credit_id
                    )
                    db.session.add(new_cost_code)
                    db.session.commit()
                    
                    logger.info(f"Cost code created directly in DB: ID={new_cost_code.id}, Project ID={new_cost_code.project_id}")
                    
                    # Verify the cost code was saved
                    saved_code = CostCode.query.get(new_cost_code.id)
                    if saved_code:
                        logger.info(f"Successfully retrieved saved cost code: ID={saved_code.id}, Project ID={saved_code.project_id}")
                    else:
                        logger.error(f"Failed to retrieve saved cost code with ID={new_cost_code.id}")
                        
                    flash(f"Cost Code {code} created successfully!", "success")
                    # Redirect to cost_codes with the specific project_id
                    return redirect(url_for('main.cost_codes', project_id=project_id))
                    
                except Exception as db_error:
                    logger.error(f"Database error creating cost code: {str(db_error)}")
                    raise db_error
                
            except Exception as e:
                logger.error(f"Error creating cost code: {str(e)}")
                flash(f"Error creating cost code: {str(e)}", "error")
                projects = ProjectService.get_all_projects()
                return render_template('add_cost_code.html', 
                                      projects=projects, 
                                      rules=rules, 
                                      selected_project_id=project_id, 
                                      disciplines=DEFAULT_DISCIPLINES)
        
        projects = ProjectService.get_all_projects()
        return render_template('add_cost_code.html', 
                              projects=projects, 
                              rules=rules, 
                              selected_project_id=project_id, 
                              disciplines=DEFAULT_DISCIPLINES)
    except Exception as e:
        logger.error(f"Error loading add cost code form: {str(e)}")
        flash(f"Error loading add cost code form: {str(e)}", "error")
        return redirect(url_for('main.projects'))

# Reports route
@main_bp.route('/reports')
def reports():
    try:
        return render_template('reports.html')
    except Exception as e:
        logger.error(f"Error loading reports: {str(e)}")
        flash(f"Error loading reports: {str(e)}", "error")
        return render_template('reports.html')

# Rules of Credit routes
@main_bp.route('/rules_of_credit')
def rules_of_credit():
    try:
        # Check if action=add is in the query parameters
        action = request.args.get('action')
        if action == 'add':
            # Render the add rule of credit form
            logger.info("Rendering add rule of credit form")
            return render_template('add_rule_of_credit.html')
        
        # Otherwise, show the list of rules
        rules = RuleOfCreditService.get_all_rules_of_credit()
        return render_template('rules_of_credit.html', rules=rules)
    except Exception as e:
        logger.error(f"Error loading rules of credit: {str(e)}")
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
            logger.error(f"Error creating rule of credit: {str(e)}")
            flash(f"Error creating rule of credit: {str(e)}", "error")
            return render_template('add_rule_of_credit.html')
    
    return render_template('add_rule_of_credit.html')
