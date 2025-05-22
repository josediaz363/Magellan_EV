from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from models import db, Project, SubJob, RuleOfCredit, CostCode, WorkItem, DISCIPLINE_CHOICES
import json
import uuid
import traceback
import os
import datetime
import io

# Import PDF export functionality
from reports.pdf_export import generate_quantities_report_pdf

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

# ===== REPORTS ROUTES =====

@main_bp.route('/reports')
def reports_index():
    """Reports page"""
    try:
        projects = Project.query.all()
        sub_jobs = SubJob.query.all()
        return render_template('reports_index.html', projects=projects, sub_jobs=sub_jobs)
    except Exception as e:
        flash(f'Error loading reports page: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('reports_index.html', projects=[], sub_jobs=[])

@main_bp.route('/reports/quantities_pdf')
def quantities_report_pdf():
    """Generate quantities PDF report"""
    try:
        project_id = request.args.get('project_id')
        sub_job_id = request.args.get('sub_job_id')
        
        if not project_id and not sub_job_id:
            flash('Please select a project or sub job', 'danger')
            return redirect(url_for('main.reports_index'))
        
        # Generate PDF
        pdf_data = generate_quantities_report_pdf(
            project_id=project_id, 
            sub_job_id=sub_job_id
        )
        
        # Create filename
        if sub_job_id:
            sub_job = SubJob.query.get_or_404(sub_job_id)
            project = Project.query.get_or_404(sub_job.project_id)
            filename = f"{project.project_id_str}_{sub_job.name}_quantities_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        else:
            project = Project.query.get_or_404(project_id)
            filename = f"{project.project_id_str}_quantities_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Return PDF file
        return send_file(
            io.BytesIO(pdf_data),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        flash(f'Error generating PDF report: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.reports_index'))

# ===== PROJECT ROUTES =====

@main_bp.route('/projects')
def projects():
    """List all projects"""
    try:
        all_projects = Project.query.all()
        
        # Calculate project-level totals for each project
        for project in all_projects:
            # Initialize totals
            project.total_budgeted_hours = 0
            project.total_earned_hours = 0
            project.total_budgeted_quantity = 0
            project.total_earned_quantity = 0
            
            # Get all work items for this project
            work_items = WorkItem.query.filter_by(project_id=project.id).all()
            
            # Sum up the values
            for item in work_items:
                project.total_budgeted_hours += item.budgeted_man_hours or 0
                project.total_earned_hours += item.earned_man_hours or 0
                
                # For quantity, we need to be careful about different units of measure
                # For simplicity, we're just summing them up here
                project.total_budgeted_quantity += item.budgeted_quantity or 0
                project.total_earned_quantity += item.earned_quantity or 0
            
            # Calculate overall progress percentage
            if project.total_budgeted_hours > 0:
                project.overall_progress = (project.total_earned_hours / project.total_budgeted_hours) * 100
            else:
                project.overall_progress = 0
                
        return render_template('projects.html', projects=all_projects)
    except Exception as e:
        flash(f'Error loading projects: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('projects.html', projects=[])

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
                    "name": step_names[i],
                    "weight": weight
                })
                total_weight += weight
        
        # Validate total weight
        if abs(total_weight - 100) > 0.1:  # Allow small rounding errors
            flash("Error: The total weight of all steps must equal 100%", "danger")
            return render_template('add_rule_of_credit.html')
        
        # Create new rule
        new_rule = RuleOfCredit(
            name=name,
            description=description
        )
        new_rule.set_steps(steps)
        
        # Add to database
        db.session.add(new_rule)
        db.session.commit()
        
        flash('Rule of Credit added successfully!', 'success')
        # Redirect to rules page
        return redirect(url_for('main.list_rules_of_credit'))
    
    return render_template('add_rule_of_credit.html')

@main_bp.route('/edit_rule_of_credit/<int:rule_id>', methods=['GET', 'POST'])
def edit_rule_of_credit(rule_id):
    """Edit an existing rule of credit"""
    rule = RuleOfCredit.query.get_or_404(rule_id)
    
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
                    "name": step_names[i],
                    "weight": weight
                })
                total_weight += weight
        
        # Validate total weight
        if abs(total_weight - 100) > 0.1:  # Allow small rounding errors
            flash("Error: The total weight of all steps must equal 100%", "danger")
            return render_template('edit_rule_of_credit.html', rule=rule)
        
        # Update rule
        rule.name = name
        rule.description = description
        rule.set_steps(steps)
        
        db.session.commit()
        
        flash('Rule of Credit updated successfully!', 'success')
        return redirect(url_for('main.list_rules_of_credit'))
    
    return render_template('edit_rule_of_credit.html', rule=rule)

@main_bp.route('/delete_rule_of_credit/<int:rule_id>', methods=['POST'])
def delete_rule_of_credit(rule_id):
    """Delete a rule of credit"""
    rule = RuleOfCredit.query.get_or_404(rule_id)
    
    # Check if rule is being used by any cost codes
    cost_codes = CostCode.query.filter_by(rule_of_credit_id=rule_id).all()
    if cost_codes:
        flash('Cannot delete rule of credit as it is being used by cost codes.', 'danger')
        return redirect(url_for('main.list_rules_of_credit'))
    
    db.session.delete(rule)
    db.session.commit()
    
    flash('Rule of Credit deleted successfully!', 'success')
    return redirect(url_for('main.list_rules_of_credit'))

# ===== COST CODE ROUTES =====

@main_bp.route('/cost_codes')
def list_cost_codes():
    """List all cost codes"""
    try:
        all_cost_codes = CostCode.query.all()
        projects = Project.query.all()
        disciplines = DISCIPLINE_CHOICES
        return render_template('list_cost_codes.html', 
                              cost_codes=all_cost_codes, 
                              projects=projects, 
                              disciplines=disciplines)
    except Exception as e:
        flash(f'Error loading cost codes: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

@main_bp.route('/add_cost_code', methods=['GET', 'POST'])
def add_cost_code():
    """Add a new cost code"""
    try:
        if request.method == 'POST':
            try:
                code = request.form.get('code')
                description = request.form.get('description')
                discipline = request.form.get('discipline')
                project_id = request.form.get('project_id')
                rule_of_credit_id = request.form.get('rule_of_credit_id') or None
                
                # Check if code already exists
                existing_code = CostCode.query.filter_by(cost_code_id_str=code).first()
                if existing_code:
                    flash('Cost code already exists!', 'danger')
                    projects = Project.query.all()
                    rules = RuleOfCredit.query.all()
                    return render_template('add_cost_code.html', projects=projects, rules=rules, disciplines=DISCIPLINE_CHOICES)
                
                # Create new cost code
                new_cost_code = CostCode(
                    cost_code_id_str=code,
                    description=description,
                    discipline=discipline,
                    project_id=project_id,
                    rule_of_credit_id=rule_of_credit_id
                )
                
                db.session.add(new_cost_code)
                db.session.commit()
                
                flash('Cost code added successfully!', 'success')
                return redirect(url_for('main.list_cost_codes'))
            except Exception as e:
                flash(f'Error adding cost code: {str(e)}', 'danger')
                traceback.print_exc()
                projects = Project.query.all()
                rules = RuleOfCredit.query.all()
                return render_template('add_cost_code.html', projects=projects, rules=rules, disciplines=DISCIPLINE_CHOICES)
        
        projects = Project.query.all()
        rules = RuleOfCredit.query.all()
        return render_template('add_cost_code.html', projects=projects, rules=rules, disciplines=DISCIPLINE_CHOICES)
    except Exception as e:
        flash(f'Error loading add cost code page: {str(e)}', 'danger')
        return redirect(url_for('main.list_cost_codes'))

@main_bp.route('/edit_cost_code/<int:cost_code_id>', methods=['GET', 'POST'])
def edit_cost_code(cost_code_id):
    """Edit an existing cost code"""
    cost_code = CostCode.query.get_or_404(cost_code_id)
    
    if request.method == 'POST':
        try:
            cost_code.cost_code_id_str = request.form.get('code')
            cost_code.description = request.form.get('description')
            cost_code.discipline = request.form.get('discipline')
            cost_code.project_id = request.form.get('project_id')
            cost_code.rule_of_credit_id = request.form.get('rule_of_credit_id') or None
            
            db.session.commit()
            
            flash('Cost code updated successfully!', 'success')
            return redirect(url_for('main.list_cost_codes'))
        except Exception as e:
            flash(f'Error updating cost code: {str(e)}', 'danger')
            traceback.print_exc()
            projects = Project.query.all()
            rules = RuleOfCredit.query.all()
            return render_template('edit_cost_code.html', 
                                  cost_code=cost_code, 
                                  projects=projects, 
                                  rules=rules, 
                                  disciplines=DISCIPLINE_CHOICES)
    
    projects = Project.query.all()
    rules = RuleOfCredit.query.all()
    return render_template('edit_cost_code.html', 
                          cost_code=cost_code, 
                          projects=projects, 
                          rules=rules, 
                          disciplines=DISCIPLINE_CHOICES)

@main_bp.route('/delete_cost_code/<int:cost_code_id>', methods=['POST'])
def delete_cost_code(cost_code_id):
    """Delete a cost code"""
    cost_code = CostCode.query.get_or_404(cost_code_id)
    
    # Check if cost code is being used by any work items
    work_items = WorkItem.query.filter_by(cost_code_id=cost_code_id).all()
    if work_items:
        flash('Cannot delete cost code as it is being used by work items.', 'danger')
        return redirect(url_for('main.list_cost_codes'))
    
    db.session.delete(cost_code)
    db.session.commit()
    
    flash('Cost code deleted successfully!', 'success')
    return redirect(url_for('main.list_cost_codes'))

# ===== WORK ITEM ROUTES =====

@main_bp.route('/work_items')
def work_items():
    """List all work items"""
    try:
        all_work_items = WorkItem.query.all()
        return render_template('work_items.html', work_items=all_work_items)
    except Exception as e:
        flash(f'Error loading work items: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('work_items.html', work_items=[])

@main_bp.route('/add_work_item', methods=['GET', 'POST'])
def add_work_item():
    """Add a new work item"""
    try:
        if request.method == 'POST':
            try:
                # Get form data
                project_id = request.form.get('project_id')
                sub_job_id = request.form.get('sub_job_id')
                cost_code_id = request.form.get('cost_code_id')
                description = request.form.get('description')
                uom = request.form.get('uom')
                budgeted_quantity = request.form.get('budgeted_quantity')
                budgeted_man_hours = request.form.get('budgeted_man_hours')
                
                # Create work item ID
                work_item_id = f"WI-{uuid.uuid4().hex[:8].upper()}"
                
                # Create new work item
                new_work_item = WorkItem(
                    work_item_id=work_item_id,
                    project_id=project_id,
                    sub_job_id=sub_job_id,
                    cost_code_id=cost_code_id,
                    description=description,
                    uom=uom,
                    budgeted_quantity=float(budgeted_quantity) if budgeted_quantity else None,
                    budgeted_man_hours=float(budgeted_man_hours) if budgeted_man_hours else None
                )
                
                db.session.add(new_work_item)
                db.session.commit()
                
                flash('Work item added successfully!', 'success')
                
                # Redirect based on where the request came from
                if sub_job_id:
                    return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))
                else:
                    return redirect(url_for('main.work_items'))
            except Exception as e:
                flash(f'Error adding work item: {str(e)}', 'danger')
                traceback.print_exc()
                
                projects = Project.query.all()
                sub_jobs = []
                cost_codes = []
                
                if 'sub_job_id' in request.form and request.form.get('sub_job_id'):
                    sub_job_id = request.form.get('sub_job_id')
                    sub_job = SubJob.query.get(sub_job_id)
                    if sub_job:
                        sub_jobs = [sub_job]
                        project_id = sub_job.project_id
                        cost_codes = CostCode.query.filter_by(project_id=project_id).all()
                
                return render_template('add_work_item.html', 
                                      projects=projects, 
                                      sub_jobs=sub_jobs, 
                                      cost_codes=cost_codes)
        
        # GET request
        projects = Project.query.all()
        sub_jobs = []
        cost_codes = []
        
        # If sub_job_id is provided, pre-select it
        sub_job_id = request.args.get('sub_job_id')
        if sub_job_id:
            sub_job = SubJob.query.get(sub_job_id)
            if sub_job:
                sub_jobs = [sub_job]
                project_id = sub_job.project_id
                cost_codes = CostCode.query.filter_by(project_id=project_id).all()
        
        return render_template('add_work_item.html', 
                              projects=projects, 
                              sub_jobs=sub_jobs, 
                              cost_codes=cost_codes)
    except Exception as e:
        flash(f'Error loading add work item page: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.work_items'))

@main_bp.route('/view_work_item/<int:work_item_id>')
def view_work_item(work_item_id):
    """View a specific work item"""
    try:
        work_item = WorkItem.query.get_or_404(work_item_id)
        return render_template('view_work_item.html', work_item=work_item)
    except Exception as e:
        flash(f'Error loading work item: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.work_items'))

@main_bp.route('/edit_work_item/<int:work_item_id>', methods=['GET', 'POST'])
def edit_work_item(work_item_id):
    """Edit an existing work item"""
    try:
        work_item = WorkItem.query.get_or_404(work_item_id)
        
        if request.method == 'POST':
            try:
                # Update work item
                work_item.description = request.form.get('description')
                work_item.uom = request.form.get('uom')
                work_item.budgeted_quantity = float(request.form.get('budgeted_quantity')) if request.form.get('budgeted_quantity') else None
                work_item.budgeted_man_hours = float(request.form.get('budgeted_man_hours')) if request.form.get('budgeted_man_hours') else None
                
                db.session.commit()
                
                flash('Work item updated successfully!', 'success')
                return redirect(url_for('main.view_work_item', work_item_id=work_item.id))
            except Exception as e:
                flash(f'Error updating work item: {str(e)}', 'danger')
                traceback.print_exc()
                return render_template('edit_work_item.html', work_item=work_item)
        
        return render_template('edit_work_item.html', work_item=work_item)
    except Exception as e:
        flash(f'Error loading edit work item page: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.work_items'))

@main_bp.route('/delete_work_item/<int:work_item_id>', methods=['POST'])
def delete_work_item(work_item_id):
    """Delete a work item"""
    try:
        work_item = WorkItem.query.get_or_404(work_item_id)
        sub_job_id = work_item.sub_job_id
        
        db.session.delete(work_item)
        db.session.commit()
        
        flash('Work item deleted successfully!', 'success')
        
        # Redirect based on where the request came from
        if sub_job_id:
            return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))
        else:
            return redirect(url_for('main.work_items'))
    except Exception as e:
        flash(f'Error deleting work item: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.work_items'))

@main_bp.route('/update_work_item_progress/<int:work_item_id>', methods=['GET', 'POST'])
def update_work_item_progress(work_item_id):
    """Update progress for a work item"""
    try:
        work_item = WorkItem.query.get_or_404(work_item_id)
        
        if request.method == 'POST':
            try:
                # Get progress data
                progress_steps = []
                
                if work_item.cost_code and work_item.cost_code.rule_of_credit:
                    rule = work_item.cost_code.rule_of_credit
                    steps = rule.steps
                    
                    for i, step in enumerate(steps):
                        step_percentage = request.form.get(f'step_{i}_percentage')
                        if step_percentage:
                            progress_steps.append({
                                "step_id": i,
                                "name": step["name"],
                                "percentage": float(step_percentage)
                            })
                
                # Update work item progress
                work_item.set_progress_steps(progress_steps)
                
                # Calculate earned values based on progress
                if work_item.budgeted_quantity is not None:
                    total_progress = sum(step["percentage"] * steps[step["step_id"]]["weight"] / 100 for step in progress_steps)
                    work_item.earned_quantity = work_item.budgeted_quantity * total_progress / 100
                
                if work_item.budgeted_man_hours is not None:
                    total_progress = sum(step["percentage"] * steps[step["step_id"]]["weight"] / 100 for step in progress_steps)
                    work_item.earned_man_hours = work_item.budgeted_man_hours * total_progress / 100
                
                db.session.commit()
                
                flash('Work item progress updated successfully!', 'success')
                return redirect(url_for('main.view_work_item', work_item_id=work_item.id))
            except Exception as e:
                flash(f'Error updating work item progress: {str(e)}', 'danger')
                traceback.print_exc()
                return render_template('update_work_item_progress.html', work_item=work_item)
        
        return render_template('update_work_item_progress.html', work_item=work_item)
    except Exception as e:
        flash(f'Error loading update work item progress page: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.work_items'))

# ===== API ROUTES =====

@main_bp.route('/api/get_sub_jobs/<int:project_id>')
def get_sub_jobs(project_id):
    """Get sub jobs for a project"""
    try:
        sub_jobs = SubJob.query.filter_by(project_id=project_id).all()
        return jsonify([{
            'id': sj.id,
            'name': sj.name,
            'description': sj.description,
            'area': sj.area,
            'sub_job_id_str': sj.sub_job_id_str
        } for sj in sub_jobs])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/get_cost_codes/<int:project_id>')
def get_cost_codes(project_id):
    """Get cost codes for a project"""
    try:
        cost_codes = CostCode.query.filter_by(project_id=project_id).all()
        return jsonify([{
            'id': cc.id,
            'code': cc.cost_code_id_str,
            'description': cc.description,
            'discipline': cc.discipline
        } for cc in cost_codes])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/get_rule_of_credit/<int:cost_code_id>')
def get_rule_of_credit(cost_code_id):
    """Get rule of credit for a cost code"""
    try:
        cost_code = CostCode.query.get_or_404(cost_code_id)
        if cost_code.rule_of_credit:
            return jsonify({
                'id': cost_code.rule_of_credit.id,
                'name': cost_code.rule_of_credit.name,
                'description': cost_code.rule_of_credit.description,
                'steps': cost_code.rule_of_credit.steps
            })
        else:
            return jsonify(None)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
