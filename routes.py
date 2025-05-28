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
        
        # Calculate overall progress for dashboard
        overall_progress = 0
        total_budgeted_hours = 0
        total_earned_hours = 0
        
        # Get all work items to calculate overall progress
        all_work_items = WorkItem.query.all()
        
        # Calculate totals
        for item in all_work_items:
            if item.budgeted_man_hours:
                total_budgeted_hours += item.budgeted_man_hours
                # Calculate earned hours based on percent complete
                earned_hours = item.budgeted_man_hours * (item.percent_complete_hours / 100) if item.percent_complete_hours else 0
                total_earned_hours += earned_hours
        
        # Calculate overall progress percentage
        if total_budgeted_hours > 0:
            overall_progress = (total_earned_hours / total_budgeted_hours) * 100
            overall_progress = round(overall_progress, 1)  # Round to 1 decimal place
        
        return render_template('index.html', 
                              projects=projects, 
                              work_items=work_items, 
                              overall_progress=overall_progress)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('index.html', projects=[], work_items=[], overall_progress=0)

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
                
            # Add project with calculated data to the list
            projects_with_data.append({
                'project': project,
                'total_budgeted_hours': total_budgeted_hours,
                'total_earned_hours': total_earned_hours,
                'total_budgeted_quantity': total_budgeted_quantity,
                'total_earned_quantity': total_earned_quantity,
                'overall_progress': overall_progress
            })
        
        return render_template('projects.html', projects=projects_with_data)
    except Exception as e:
        flash(f'Error loading projects: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('projects.html', projects=[])

@main_bp.route('/add_project', methods=['GET', 'POST'])
def add_project():
    """Add a new project"""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            description = request.form.get('description')
            
            new_project = Project(name=name, description=description)
            db.session.add(new_project)
            db.session.commit()
            
            flash('Project added successfully!', 'success')
            return redirect(url_for('main.projects'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding project: {str(e)}', 'danger')
            traceback.print_exc()
    
    return render_template('add_project.html')

@main_bp.route('/project/<int:project_id>')
def view_project(project_id):
    """View a specific project"""
    try:
        project = Project.query.get_or_404(project_id)
        sub_jobs = SubJob.query.filter_by(project_id=project_id).all()
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
        
        return render_template('view_project.html', 
                              project=project, 
                              sub_jobs=sub_jobs, 
                              work_items=work_items,
                              total_budgeted_hours=total_budgeted_hours,
                              total_earned_hours=total_earned_hours,
                              total_budgeted_quantity=total_budgeted_quantity,
                              total_earned_quantity=total_earned_quantity,
                              overall_progress=overall_progress)
    except Exception as e:
        flash(f'Error viewing project: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.projects'))

@main_bp.route('/edit_project/<int:project_id>', methods=['GET', 'POST'])
def edit_project(project_id):
    """Edit a project"""
    try:
        project = Project.query.get_or_404(project_id)
        
        if request.method == 'POST':
            project.name = request.form.get('name')
            project.description = request.form.get('description')
            
            db.session.commit()
            flash('Project updated successfully!', 'success')
            return redirect(url_for('main.view_project', project_id=project.id))
        
        return render_template('edit_project.html', project=project)
    except Exception as e:
        db.session.rollback()
        flash(f'Error editing project: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.projects'))

# ===== WORK ITEMS ROUTES =====

@main_bp.route('/work_items')
def work_items():
    """List all work items"""
    try:
        # Get filter parameters
        project_id = request.args.get('project_id', type=int)
        sub_job_id = request.args.get('sub_job_id', type=int)
        cost_code_id = request.args.get('cost_code_id', type=int)
        search = request.args.get('search', '')
        
        # Base query
        query = WorkItem.query
        
        # Apply filters
        if project_id:
            query = query.filter_by(project_id=project_id)
        if sub_job_id:
            query = query.filter_by(sub_job_id=sub_job_id)
        if cost_code_id:
            query = query.filter_by(cost_code_id=cost_code_id)
        if search:
            query = query.filter(WorkItem.description.ilike(f'%{search}%'))
        
        # Get results
        work_items = query.order_by(WorkItem.id.desc()).all()
        
        # Get projects and cost codes for filters
        projects = Project.query.all()
        cost_codes = CostCode.query.all()
        
        return render_template('work_items.html', 
                              work_items=work_items, 
                              projects=projects, 
                              cost_codes=cost_codes)
    except Exception as e:
        flash(f'Error loading work items: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('work_items.html', work_items=[], projects=[], cost_codes=[])

@main_bp.route('/add_work_item', methods=['GET', 'POST'])
def add_work_item():
    """Add a new work item"""
    try:
        projects = Project.query.all()
        cost_codes = CostCode.query.all()
        rules_of_credit = RuleOfCredit.query.all()
        
        if request.method == 'POST':
            project_id = request.form.get('project_id', type=int)
            sub_job_id = request.form.get('sub_job_id', type=int)
            cost_code_id = request.form.get('cost_code_id', type=int)
            rule_of_credit_id = request.form.get('rule_of_credit_id', type=int)
            description = request.form.get('description')
            discipline = request.form.get('discipline')
            area = request.form.get('area')
            deliverable = request.form.get('deliverable')
            drawing_number = request.form.get('drawing_number')
            activity_id = request.form.get('activity_id')
            unit_of_measure = request.form.get('unit_of_measure')
            budgeted_quantity = request.form.get('budgeted_quantity', type=float)
            budgeted_man_hours = request.form.get('budgeted_man_hours', type=float)
            
            new_work_item = WorkItem(
                project_id=project_id,
                sub_job_id=sub_job_id,
                cost_code_id=cost_code_id,
                rule_of_credit_id=rule_of_credit_id,
                description=description,
                discipline=discipline,
                area=area,
                deliverable=deliverable,
                drawing_number=drawing_number,
                activity_id=activity_id,
                unit_of_measure=unit_of_measure,
                budgeted_quantity=budgeted_quantity,
                budgeted_man_hours=budgeted_man_hours,
                percent_complete_hours=0,
                percent_complete_quantity=0
            )
            
            db.session.add(new_work_item)
            db.session.commit()
            
            flash('Work item added successfully!', 'success')
            return redirect(url_for('main.work_items'))
        
        return render_template('add_work_item.html', 
                              projects=projects, 
                              cost_codes=cost_codes, 
                              rules_of_credit=rules_of_credit,
                              disciplines=DISCIPLINE_CHOICES)
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding work item: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.work_items'))

@main_bp.route('/work_item/<int:work_item_id>')
def view_work_item(work_item_id):
    """View a specific work item"""
    try:
        work_item = WorkItem.query.get_or_404(work_item_id)
        return render_template('view_work_item.html', work_item=work_item)
    except Exception as e:
        flash(f'Error viewing work item: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.work_items'))

@main_bp.route('/edit_work_item/<int:work_item_id>', methods=['GET', 'POST'])
def edit_work_item(work_item_id):
    """Edit a work item"""
    try:
        work_item = WorkItem.query.get_or_404(work_item_id)
        projects = Project.query.all()
        cost_codes = CostCode.query.all()
        rules_of_credit = RuleOfCredit.query.all()
        
        if request.method == 'POST':
            work_item.project_id = request.form.get('project_id', type=int)
            work_item.sub_job_id = request.form.get('sub_job_id', type=int)
            work_item.cost_code_id = request.form.get('cost_code_id', type=int)
            work_item.rule_of_credit_id = request.form.get('rule_of_credit_id', type=int)
            work_item.description = request.form.get('description')
            work_item.discipline = request.form.get('discipline')
            work_item.area = request.form.get('area')
            work_item.deliverable = request.form.get('deliverable')
            work_item.drawing_number = request.form.get('drawing_number')
            work_item.activity_id = request.form.get('activity_id')
            work_item.unit_of_measure = request.form.get('unit_of_measure')
            work_item.budgeted_quantity = request.form.get('budgeted_quantity', type=float)
            work_item.budgeted_man_hours = request.form.get('budgeted_man_hours', type=float)
            
            db.session.commit()
            flash('Work item updated successfully!', 'success')
            return redirect(url_for('main.view_work_item', work_item_id=work_item.id))
        
        return render_template('edit_work_item.html', 
                              work_item=work_item, 
                              projects=projects, 
                              cost_codes=cost_codes, 
                              rules_of_credit=rules_of_credit,
                              disciplines=DISCIPLINE_CHOICES)
    except Exception as e:
        db.session.rollback()
        flash(f'Error editing work item: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.work_items'))

@main_bp.route('/update_work_item_progress/<int:work_item_id>', methods=['GET', 'POST'])
def update_work_item_progress(work_item_id):
    """Update work item progress"""
    try:
        work_item = WorkItem.query.get_or_404(work_item_id)
        
        if request.method == 'POST':
            work_item.percent_complete_hours = request.form.get('percent_complete_hours', type=float)
            work_item.percent_complete_quantity = request.form.get('percent_complete_quantity', type=float)
            
            # Calculate earned values
            work_item.earned_man_hours = work_item.budgeted_man_hours * (work_item.percent_complete_hours / 100) if work_item.percent_complete_hours else 0
            work_item.earned_quantity = work_item.budgeted_quantity * (work_item.percent_complete_quantity / 100) if work_item.percent_complete_quantity else 0
            
            db.session.commit()
            flash('Progress updated successfully!', 'success')
            return redirect(url_for('main.view_work_item', work_item_id=work_item.id))
        
        return render_template('update_work_item_progress.html', work_item=work_item)
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating progress: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.work_items'))

# ===== COST CODE ROUTES =====

@main_bp.route('/cost_codes')
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
    if request.method == 'POST':
        try:
            code = request.form.get('code')
            description = request.form.get('description')
            
            new_cost_code = CostCode(code=code, description=description)
            db.session.add(new_cost_code)
            db.session.commit()
            
            flash('Cost code added successfully!', 'success')
            return redirect(url_for('main.list_cost_codes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding cost code: {str(e)}', 'danger')
            traceback.print_exc()
    
    return render_template('add_cost_code.html')

@main_bp.route('/edit_cost_code/<int:cost_code_id>', methods=['GET', 'POST'])
def edit_cost_code(cost_code_id):
    """Edit a cost code"""
    try:
        cost_code = CostCode.query.get_or_404(cost_code_id)
        
        if request.method == 'POST':
            cost_code.code = request.form.get('code')
            cost_code.description = request.form.get('description')
            
            db.session.commit()
            flash('Cost code updated successfully!', 'success')
            return redirect(url_for('main.list_cost_codes'))
        
        return render_template('edit_cost_code.html', cost_code=cost_code)
    except Exception as e:
        db.session.rollback()
        flash(f'Error editing cost code: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_cost_codes'))

# ===== RULES OF CREDIT ROUTES =====

@main_bp.route('/rules_of_credit')
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
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            description = request.form.get('description')
            
            # Get step data from form
            steps_data = []
            step_count = int(request.form.get('step_count', 0))
            
            for i in range(step_count):
                step_name = request.form.get(f'step_name_{i}')
                step_weight = float(request.form.get(f'step_weight_{i}', 0))
                
                if step_name and step_weight > 0:
                    steps_data.append({
                        'name': step_name,
                        'weight': step_weight
                    })
            
            # Validate total weight is 100%
            total_weight = sum(step['weight'] for step in steps_data)
            if not (99.5 <= total_weight <= 100.5):  # Allow small rounding errors
                flash(f'Total weight must be 100%. Current total: {total_weight}%', 'danger')
                return render_template('add_rule_of_credit.html')
            
            # Create new rule of credit
            new_rule = RuleOfCredit(
                name=name,
                description=description,
                steps=json.dumps(steps_data)
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

@main_bp.route('/edit_rule_of_credit/<int:rule_id>', methods=['GET', 'POST'])
def edit_rule_of_credit(rule_id):
    """Edit a rule of credit"""
    try:
        rule = RuleOfCredit.query.get_or_404(rule_id)
        
        if request.method == 'POST':
            rule.name = request.form.get('name')
            rule.description = request.form.get('description')
            
            # Get step data from form
            steps_data = []
            step_count = int(request.form.get('step_count', 0))
            
            for i in range(step_count):
                step_name = request.form.get(f'step_name_{i}')
                step_weight = float(request.form.get(f'step_weight_{i}', 0))
                
                if step_name and step_weight > 0:
                    steps_data.append({
                        'name': step_name,
                        'weight': step_weight
                    })
            
            # Validate total weight is 100%
            total_weight = sum(step['weight'] for step in steps_data)
            if not (99.5 <= total_weight <= 100.5):  # Allow small rounding errors
                flash(f'Total weight must be 100%. Current total: {total_weight}%', 'danger')
                return render_template('edit_rule_of_credit.html', rule=rule)
            
            rule.steps = json.dumps(steps_data)
            
            db.session.commit()
            flash('Rule of credit updated successfully!', 'success')
            return redirect(url_for('main.list_rules_of_credit'))
        
        return render_template('edit_rule_of_credit.html', rule=rule)
    except Exception as e:
        db.session.rollback()
        flash(f'Error editing rule of credit: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_rules_of_credit'))

# ===== REPORTS ROUTES =====

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

@main_bp.route('/generate_report', methods=['POST'])
def generate_report():
    """Generate a report"""
    try:
        report_type = request.form.get('report_type')
        project_id = request.form.get('project_id', type=int)
        
        if report_type == 'progress':
            # Import the report generation module
            from reports.pdf_export import generate_progress_report
            
            # Generate the report
            pdf_data = generate_progress_report(project_id)
            
            # Create a response with the PDF
            return send_file(
                io.BytesIO(pdf_data),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'progress_report_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
            )
        else:
            flash('Invalid report type', 'danger')
            return redirect(url_for('main.reports_index'))
    except Exception as e:
        flash(f'Error generating report: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.reports_index'))

# ===== API ROUTES =====

@main_bp.route('/api/projects/<int:project_id>/subjobs')
def get_project_subjobs(project_id):
    """Get sub jobs for a project"""
    try:
        sub_jobs = SubJob.query.filter_by(project_id=project_id).all()
        return jsonify([{
            'id': sub_job.id,
            'name': sub_job.name
        } for sub_job in sub_jobs])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
