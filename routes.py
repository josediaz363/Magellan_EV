"""
Fixed routes.py for Magellan EV Tracker v3.0
- Updated cost_codes route to use correct service method name
- Fixed parameter passing to match CostCodeService expectations
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
