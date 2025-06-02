"""
Fixed routes.py for Magellan EV Tracker v3.0
- Added dashboard route with proper service method calls
- Added work_items route to resolve BuildError
- Added reports route to resolve BuildError
- Updated cost_codes route to use correct service method name
- Fixed parameter passing to match service expectations
- Enhanced error handling and logging
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from services.project_service import ProjectService
from services.sub_job_service import SubJobService
from services.work_item_service import WorkItemService
from services.cost_code_service import CostCodeService
from services.rule_of_credit_service import RuleOfCreditService
from services.url_service import UrlService
from models import Project, SubJob, WorkItem, CostCode, RuleOfCredit, DISCIPLINE_CHOICES
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

# Use the complete discipline list from models
DEFAULT_DISCIPLINES = DISCIPLINE_CHOICES

@main_bp.route('/')
def index():
    """Home page route - matches v1.32 pattern"""
    try:
        projects = ProjectService.get_all_projects()
        work_items = WorkItemService.get_recent_work_items(10)  # Get 10 most recent work items
        return render_template('index.html', projects=projects, work_items=work_items)
    except Exception as e:
        logger.error(f'Error loading index page: {str(e)}')
        flash(f'Error loading index page: {str(e)}', 'danger')
        return render_template('index.html', projects=[], work_items=[])

@main_bp.route('/dashboard')
def dashboard():
    """Dashboard route - added to match application expectations"""
    try:
        # Log database queries for debugging
        logger.info("Loading dashboard")
        
        # Use the count methods from each service
        projects_count = ProjectService.count_projects() if hasattr(ProjectService, 'count_projects') else 0
        sub_jobs_count = SubJobService.count_sub_jobs() if hasattr(SubJobService, 'count_sub_jobs') else 0
        work_items_count = WorkItemService.count_work_items() if hasattr(WorkItemService, 'count_work_items') else 0
        rules_count = RuleOfCreditService.count_rules_of_credit() if hasattr(RuleOfCreditService, 'count_rules_of_credit') else 0
        
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

# Reports route - added to resolve BuildError
@main_bp.route('/reports')
def reports():
    """Reports route - added to resolve BuildError for 'main.reports'"""
    try:
        logger.info("Loading reports page")
        projects = ProjectService.get_all_projects()
        logger.info(f"Found {len(projects)} projects for reports page")
        return render_template('reports.html', projects=projects)
    except Exception as e:
        logger.error(f"Error loading reports page: {str(e)}")
        flash(f"Error loading reports page: {str(e)}", "error")
        return render_template('reports.html', projects=[])

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
        
        return render_template('projects.html', projects=projects)
    except Exception as e:
        logger.error(f"Error loading projects: {str(e)}")
        flash(f"Error loading projects: {str(e)}", "error")
        return render_template('projects.html', projects=[])

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

@main_bp.route('/work_items')
def work_items():
    """Work items route - added to resolve BuildError"""
    try:
        sub_job_id = request.args.get('sub_job_id', type=int)
        
        if sub_job_id:
            # Get work items for a specific sub job
            sub_job = SubJobService.get_sub_job_by_id(sub_job_id)
            if not sub_job:
                flash("Sub job not found", "error")
                return redirect(url_for('main.projects'))
                
            work_items = WorkItemService.get_sub_job_work_items(sub_job_id)
            project = ProjectService.get_project_details(sub_job.project_id)
            
            logger.info(f"Found {len(work_items)} work items for sub job {sub_job_id}")
            
            return render_template('work_items.html', 
                                  work_items=work_items, 
                                  sub_job=sub_job, 
                                  project=project)
        else:
            # Get all work items
            work_items = WorkItemService.get_all_work_items()
            logger.info(f"Found {len(work_items)} work items (all sub jobs)")
            
            return render_template('work_items.html', 
                                  work_items=work_items, 
                                  sub_job=None, 
                                  project=None)
    except Exception as e:
        logger.error(f"Error loading work items: {str(e)}")
        flash(f"Error loading work items: {str(e)}", "error")
        return render_template('work_items.html', 
                              work_items=[], 
                              sub_job=None, 
                              project=None)

@main_bp.route('/cost_codes')
def cost_codes():
    try:
        project_id = request.args.get('project_id', type=int)
        projects = ProjectService.get_all_projects()
        
        # Log the request for debugging
        logger.info(f"Loading cost codes for project_id: {project_id}")
        
        if project_id:
            project = ProjectService.get_project_details(project_id)
            # Use the correct method name: get_project_cost_codes
            cost_codes = CostCodeService.get_project_cost_codes(project_id)
            logger.info(f"Found {len(cost_codes)} cost codes for project {project_id}")
            
            # Debug log each cost code
            for cc in cost_codes:
                logger.info(f"Cost code: {cc.id}, {cc.cost_code_id_str}, project_id={cc.project_id}")
                
            return render_template('cost_codes.html', 
                                  cost_codes=cost_codes, 
                                  project=project, 
                                  disciplines=DEFAULT_DISCIPLINES, 
                                  projects=projects)
        else:
            cost_codes = CostCodeService.get_all_cost_codes()
            logger.info(f"Found {len(cost_codes)} cost codes (all projects)")
            return render_template('cost_codes.html', 
                                  cost_codes=cost_codes, 
                                  project=None, 
                                  disciplines=DEFAULT_DISCIPLINES, 
                                  projects=projects)
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
                # Get form data
                project_id = request.form.get('project_id', type=int)
                cost_code_id_str = request.form.get('cost_code_id_str', '')
                description = request.form.get('description', '')
                discipline = request.form.get('discipline', '')
                rule_of_credit_id = request.form.get('rule_of_credit_id', type=int)
                
                # Log the attempt
                logger.info(f"Creating cost code: {cost_code_id_str} for project {project_id}, discipline={discipline}")
                
                # Create cost code with correct parameter names
                # Pass cost_code_id_str as 'code' and include discipline
                cost_code = CostCodeService.create_cost_code(
                    project_id=project_id,
                    code=cost_code_id_str,  # Map to the parameter name expected by the service
                    description=description,
                    discipline=discipline,   # Include the required discipline parameter
                    rule_of_credit_id=rule_of_credit_id
                )
                
                flash(f"Cost Code {cost_code_id_str} created successfully!", "success")
                return redirect(url_for('main.cost_codes', project_id=project_id))
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

# API routes for reports page
@main_bp.route('/api/get_sub_jobs/<int:project_id>')
def api_get_sub_jobs(project_id):
    """API endpoint to get sub jobs for a project (used by reports.html)"""
    try:
        sub_jobs = SubJobService.get_project_sub_jobs(project_id)
        return jsonify([{
            'id': sub_job.id,
            'name': sub_job.name
        } for sub_job in sub_jobs])
    except Exception as e:
        logger.error(f"Error fetching sub jobs for API: {str(e)}")
        return jsonify([])

# Export routes for reports
@main_bp.route('/export/quantities/pdf/<int:project_id>')
@main_bp.route('/export/quantities/pdf/<int:project_id>/<int:sub_job_id>')
def export_quantities_pdf(project_id, sub_job_id=None):
    """Export quantities report as PDF"""
    try:
        logger.info(f"Exporting quantities PDF for project {project_id}, sub_job {sub_job_id}")
        flash("PDF export functionality will be implemented in a future version.", "info")
        return redirect(url_for('main.reports'))
    except Exception as e:
        logger.error(f"Error exporting quantities PDF: {str(e)}")
        flash(f"Error exporting quantities PDF: {str(e)}", "error")
        return redirect(url_for('main.reports'))

@main_bp.route('/export/quantities/excel/<int:project_id>')
@main_bp.route('/export/quantities/excel/<int:project_id>/<int:sub_job_id>')
def export_quantities_excel(project_id, sub_job_id=None):
    """Export quantities report as Excel"""
    try:
        logger.info(f"Exporting quantities Excel for project {project_id}, sub_job {sub_job_id}")
        flash("Excel export functionality will be implemented in a future version.", "info")
        return redirect(url_for('main.reports'))
    except Exception as e:
        logger.error(f"Error exporting quantities Excel: {str(e)}")
        flash(f"Error exporting quantities Excel: {str(e)}", "error")
        return redirect(url_for('main.reports'))

@main_bp.route('/export/hours/pdf/<int:project_id>')
@main_bp.route('/export/hours/pdf/<int:project_id>/<int:sub_job_id>')
def export_hours_pdf(project_id, sub_job_id=None):
    """Export hours report as PDF"""
    try:
        logger.info(f"Exporting hours PDF for project {project_id}, sub_job {sub_job_id}")
        flash("PDF export functionality will be implemented in a future version.", "info")
        return redirect(url_for('main.reports'))
    except Exception as e:
        logger.error(f"Error exporting hours PDF: {str(e)}")
        flash(f"Error exporting hours PDF: {str(e)}", "error")
        return redirect(url_for('main.reports'))

@main_bp.route('/export/hours/excel/<int:project_id>')
@main_bp.route('/export/hours/excel/<int:project_id>/<int:sub_job_id>')
def export_hours_excel(project_id, sub_job_id=None):
    """Export hours report as Excel"""
    try:
        logger.info(f"Exporting hours Excel for project {project_id}, sub_job {sub_job_id}")
        flash("Excel export functionality will be implemented in a future version.", "info")
        return redirect(url_for('main.reports'))
    except Exception as e:
        logger.error(f"Error exporting hours Excel: {str(e)}")
        flash(f"Error exporting hours Excel: {str(e)}", "error")
        return redirect(url_for('main.reports'))
