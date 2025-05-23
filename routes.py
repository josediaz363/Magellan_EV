from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
import traceback
import io
import json
from datetime import datetime
from models import db, Project, SubJob, WorkItem, CostCode, RuleOfCredit, RuleOfCreditStep

main_bp = Blueprint('main', __name__)

# ===== INDEX ROUTES =====

@main_bp.route('/')
def index():
    """Index page"""
    try:
        projects = Project.query.all()
        work_items = WorkItem.query.all()
        return render_template('index.html', projects=projects, work_items=work_items)
    except Exception as e:
        flash(f'Error loading index page: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('index.html', projects=[], work_items=[])

# ===== PROJECT ROUTES =====

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
    if request.method == 'POST':
        try:
            project_id_str = request.form.get('project_id_str')
            name = request.form.get('name')
            description = request.form.get('description')
            
            project = Project(
                project_id_str=project_id_str,
                name=name,
                description=description
            )
            
            db.session.add(project)
            db.session.commit()
            
            flash('Project added successfully!', 'success')
            return redirect(url_for('main.projects'))
        except Exception as e:
            flash(f'Error adding project: {str(e)}', 'danger')
            traceback.print_exc()
            return render_template('add_project.html')
    
    return render_template('add_project.html')

@main_bp.route('/edit_project/<int:project_id>', methods=['GET', 'POST'])
def edit_project(project_id):
    """Edit a project"""
    try:
        project = Project.query.get_or_404(project_id)
        
        if request.method == 'POST':
            project.project_id_str = request.form.get('project_id_str')
            project.name = request.form.get('name')
            project.description = request.form.get('description')
            
            db.session.commit()
            
            flash('Project updated successfully!', 'success')
            return redirect(url_for('main.projects'))
        
        return render_template('edit_project.html', project=project)
    except Exception as e:
        flash(f'Error editing project: {str(e)}', 'danger')
        return redirect(url_for('main.projects'))

@main_bp.route('/view_project/<int:project_id>')
def view_project(project_id):
    """View a project"""
    try:
        project = Project.query.get_or_404(project_id)
        sub_jobs = SubJob.query.filter_by(project_id=project_id).all()
        return render_template('view_project.html', project=project, sub_jobs=sub_jobs)
    except Exception as e:
        flash(f'Error viewing project: {str(e)}', 'danger')
        return redirect(url_for('main.projects'))

@main_bp.route('/delete_project/<int:project_id>', methods=['POST'])
def delete_project(project_id):
    """Delete a project"""
    try:
        project = Project.query.get_or_404(project_id)
        
        db.session.delete(project)
        db.session.commit()
        
        flash('Project deleted successfully!', 'success')
        return redirect(url_for('main.projects'))
    except Exception as e:
        flash(f'Error deleting project: {str(e)}', 'danger')
        return redirect(url_for('main.projects'))

# ===== SUB JOB ROUTES =====

@main_bp.route('/add_sub_job/<int:project_id>', methods=['GET', 'POST'])
def add_sub_job(project_id):
    """Add a new sub job to a project"""
    try:
        project = Project.query.get_or_404(project_id)
        
        if request.method == 'POST':
            sub_job_id_str = request.form.get('sub_job_id_str')
            name = request.form.get('name')
            description = request.form.get('description')
            
            sub_job = SubJob(
                project_id=project_id,
                sub_job_id_str=sub_job_id_str,
                name=name,
                description=description
            )
            
            db.session.add(sub_job)
            db.session.commit()
            
            flash('Sub job added successfully!', 'success')
            return redirect(url_for('main.view_project', project_id=project_id))
        
        return render_template('add_sub_job.html', project=project)
    except Exception as e:
        flash(f'Error adding sub job: {str(e)}', 'danger')
        return redirect(url_for('main.view_project', project_id=project_id))

@main_bp.route('/edit_sub_job/<int:sub_job_id>', methods=['GET', 'POST'])
def edit_sub_job(sub_job_id):
    """Edit a sub job"""
    try:
        sub_job = SubJob.query.get_or_404(sub_job_id)
        
        if request.method == 'POST':
            sub_job.sub_job_id_str = request.form.get('sub_job_id_str')
            sub_job.name = request.form.get('name')
            sub_job.description = request.form.get('description')
            
            db.session.commit()
            
            flash('Sub job updated successfully!', 'success')
            return redirect(url_for('main.view_project', project_id=sub_job.project_id))
        
        return render_template('edit_sub_job.html', sub_job=sub_job)
    except Exception as e:
        flash(f'Error editing sub job: {str(e)}', 'danger')
        return redirect(url_for('main.projects'))

@main_bp.route('/view_sub_job/<int:sub_job_id>')
def view_sub_job(sub_job_id):
    """View a sub job"""
    try:
        sub_job = SubJob.query.get_or_404(sub_job_id)
        work_items = WorkItem.query.filter_by(sub_job_id=sub_job_id).all()
        return render_template('view_sub_job.html', sub_job=sub_job, work_items=work_items)
    except Exception as e:
        flash(f'Error viewing sub job: {str(e)}', 'danger')
        return redirect(url_for('main.projects'))

@main_bp.route('/delete_sub_job/<int:sub_job_id>', methods=['POST'])
def delete_sub_job(sub_job_id):
    """Delete a sub job"""
    try:
        sub_job = SubJob.query.get_or_404(sub_job_id)
        project_id = sub_job.project_id
        
        db.session.delete(sub_job)
        db.session.commit()
        
        flash('Sub job deleted successfully!', 'success')
        return redirect(url_for('main.view_project', project_id=project_id))
    except Exception as e:
        flash(f'Error deleting sub job: {str(e)}', 'danger')
        return redirect(url_for('main.projects'))

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
    try:
        rules_of_credit = RuleOfCredit.query.all()
        
        if request.method == 'POST':
            cost_code_id_str = request.form.get('cost_code_id_str')
            description = request.form.get('description')
            discipline = request.form.get('discipline')
            rule_of_credit_id = request.form.get('rule_of_credit_id')
            
            cost_code = CostCode(
                cost_code_id_str=cost_code_id_str,
                description=description,
                discipline=discipline,
                rule_of_credit_id=rule_of_credit_id if rule_of_credit_id else None
            )
            
            db.session.add(cost_code)
            db.session.commit()
            
            flash('Cost code added successfully!', 'success')
            return redirect(url_for('main.list_cost_codes'))
        
        return render_template('add_cost_code.html', rules_of_credit=rules_of_credit)
    except Exception as e:
        flash(f'Error adding cost code: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_cost_codes'))

@main_bp.route('/edit_cost_code/<int:cost_code_id>', methods=['GET', 'POST'])
def edit_cost_code(cost_code_id):
    """Edit a cost code"""
    try:
        cost_code = CostCode.query.get_or_404(cost_code_id)
        rules_of_credit = RuleOfCredit.query.all()
        
        if request.method == 'POST':
            cost_code.cost_code_id_str = request.form.get('cost_code_id_str')
            cost_code.description = request.form.get('description')
            cost_code.discipline = request.form.get('discipline')
            rule_of_credit_id = request.form.get('rule_of_credit_id')
            cost_code.rule_of_credit_id = rule_of_credit_id if rule_of_credit_id else None
            
            db.session.commit()
            
            flash('Cost code updated successfully!', 'success')
            return redirect(url_for('main.list_cost_codes'))
        
        return render_template('edit_cost_code.html', cost_code=cost_code, rules_of_credit=rules_of_credit)
    except Exception as e:
        flash(f'Error editing cost code: {str(e)}', 'danger')
        return redirect(url_for('main.list_cost_codes'))

@main_bp.route('/delete_cost_code/<int:cost_code_id>', methods=['POST'])
def delete_cost_code(cost_code_id):
    """Delete a cost code"""
    try:
        cost_code = CostCode.query.get_or_404(cost_code_id)
        
        db.session.delete(cost_code)
        db.session.commit()
        
        flash('Cost code deleted successfully!', 'success')
        return redirect(url_for('main.list_cost_codes'))
    except Exception as e:
        flash(f'Error deleting cost code: {str(e)}', 'danger')
        return redirect(url_for('main.list_cost_codes'))

# ===== RULE OF CREDIT ROUTES =====

@main_bp.route('/rules_of_credit')
def list_rules_of_credit():
    """List all rules of credit"""
    try:
        rules_of_credit = RuleOfCredit.query.all()
        return render_template('list_rules_of_credit.html', rules_of_credit=rules_of_credit)
    except Exception as e:
        flash(f'Error loading rules of credit: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('list_rules_of_credit.html', rules_of_credit=[])

@main_bp.route('/add_rule_of_credit', methods=['GET', 'POST'])
def add_rule_of_credit():
    """Add a new rule of credit"""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            description = request.form.get('description')
            
            rule_of_credit = RuleOfCredit(
                name=name,
                description=description
            )
            
            db.session.add(rule_of_credit)
            db.session.commit()
            
            # Add steps
            steps_data = request.form.get('steps_json')
            if steps_data:
                steps = json.loads(steps_data)
                for step in steps:
                    step_obj = RuleOfCreditStep(
                        rule_of_credit_id=rule_of_credit.id,
                        name=step['name'],
                        percentage=step['percentage'],
                        order=step['order']
                    )
                    db.session.add(step_obj)
                
                db.session.commit()
            
            flash('Rule of credit added successfully!', 'success')
            return redirect(url_for('main.list_rules_of_credit'))
        except Exception as e:
            flash(f'Error adding rule of credit: {str(e)}', 'danger')
            traceback.print_exc()
            return render_template('add_rule_of_credit.html')
    
    return render_template('add_rule_of_credit.html')

@main_bp.route('/edit_rule_of_credit/<int:rule_of_credit_id>', methods=['GET', 'POST'])
def edit_rule_of_credit(rule_of_credit_id):
    """Edit a rule of credit"""
    try:
        rule_of_credit = RuleOfCredit.query.get_or_404(rule_of_credit_id)
        
        if request.method == 'POST':
            rule_of_credit.name = request.form.get('name')
            rule_of_credit.description = request.form.get('description')
            
            # Delete existing steps
            RuleOfCreditStep.query.filter_by(rule_of_credit_id=rule_of_credit_id).delete()
            
            # Add new steps
            steps_data = request.form.get('steps_json')
            if steps_data:
                steps = json.loads(steps_data)
                for step in steps:
                    step_obj = RuleOfCreditStep(
                        rule_of_credit_id=rule_of_credit.id,
                        name=step['name'],
                        percentage=step['percentage'],
                        order=step['order']
                    )
                    db.session.add(step_obj)
            
            db.session.commit()
            
            flash('Rule of credit updated successfully!', 'success')
            return redirect(url_for('main.list_rules_of_credit'))
        
        steps = rule_of_credit.get_steps()
        return render_template('edit_rule_of_credit.html', rule_of_credit=rule_of_credit, steps=steps)
    except Exception as e:
        flash(f'Error editing rule of credit: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_rules_of_credit'))

@main_bp.route('/delete_rule_of_credit/<int:rule_of_credit_id>', methods=['POST'])
def delete_rule_of_credit(rule_of_credit_id):
    """Delete a rule of credit"""
    try:
        rule_of_credit = RuleOfCredit.query.get_or_404(rule_of_credit_id)
        
        db.session.delete(rule_of_credit)
        db.session.commit()
        
        flash('Rule of credit deleted successfully!', 'success')
        return redirect(url_for('main.list_rules_of_credit'))
    except Exception as e:
        flash(f'Error deleting rule of credit: {str(e)}', 'danger')
        return redirect(url_for('main.list_rules_of_credit'))

# ===== WORK ITEM ROUTES =====

@main_bp.route('/work_items')
def work_items():
    """Work items page"""
    try:
        projects = Project.query.all()
        sub_jobs = SubJob.query.all()
        work_items = WorkItem.query.all()
        return render_template('work_items.html', projects=projects, sub_jobs=sub_jobs, work_items=work_items)
    except Exception as e:
        flash(f'Error loading work items: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('work_items.html', projects=[], sub_jobs=[], work_items=[])

@main_bp.route('/add_work_item', methods=['GET', 'POST'])
def add_work_item():
    """Add a new work item"""
    try:
        projects = Project.query.all()
        sub_jobs = SubJob.query.all()
        cost_codes = CostCode.query.all()
        
        if request.method == 'POST':
            work_item_id_str = request.form.get('work_item_id_str')
            description = request.form.get('description')
            project_id = request.form.get('project_id')
            sub_job_id = request.form.get('sub_job_id')
            cost_code_id = request.form.get('cost_code_id')
            unit_of_measure = request.form.get('unit_of_measure')
            budgeted_quantity = request.form.get('budgeted_quantity')
            budgeted_hours = request.form.get('budgeted_hours')
            
            work_item = WorkItem(
                work_item_id_str=work_item_id_str,
                description=description,
                project_id=project_id,
                sub_job_id=sub_job_id,
                cost_code_id=cost_code_id if cost_code_id else None,
                unit_of_measure=unit_of_measure,
                budgeted_quantity=float(budgeted_quantity) if budgeted_quantity else 0,
                budgeted_hours=float(budgeted_hours) if budgeted_hours else 0,
                earned_quantity=0,
                earned_hours=0,
                progress_data='{}'
            )
            
            db.session.add(work_item)
            db.session.commit()
            
            flash('Work item added successfully!', 'success')
            return redirect(url_for('main.work_items'))
        
        return render_template('add_work_item.html', projects=projects, sub_jobs=sub_jobs, cost_codes=cost_codes)
    except Exception as e:
        flash(f'Error adding work item: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.work_items'))

@main_bp.route('/edit_work_item/<int:work_item_id>', methods=['GET', 'POST'])
def edit_work_item(work_item_id):
    """Edit a work item"""
    try:
        work_item = WorkItem.query.get_or_404(work_item_id)
        projects = Project.query.all()
        sub_jobs = SubJob.query.all()
        cost_codes = CostCode.query.all()
        
        if request.method == 'POST':
            work_item.work_item_id_str = request.form.get('work_item_id_str')
            work_item.description = request.form.get('description')
            work_item.project_id = request.form.get('project_id')
            work_item.sub_job_id = request.form.get('sub_job_id')
            cost_code_id = request.form.get('cost_code_id')
            work_item.cost_code_id = cost_code_id if cost_code_id else None
            work_item.unit_of_measure = request.form.get('unit_of_measure')
            budgeted_quantity = request.form.get('budgeted_quantity')
            work_item.budgeted_quantity = float(budgeted_quantity) if budgeted_quantity else 0
            budgeted_hours = request.form.get('budgeted_hours')
            work_item.budgeted_hours = float(budgeted_hours) if budgeted_hours else 0
            
            db.session.commit()
            
            flash('Work item updated successfully!', 'success')
            return redirect(url_for('main.work_items'))
        
        return render_template('edit_work_item.html', work_item=work_item, projects=projects, sub_jobs=sub_jobs, cost_codes=cost_codes)
    except Exception as e:
        flash(f'Error editing work item: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.work_items'))

@main_bp.route('/view_work_item/<int:work_item_id>')
def view_work_item(work_item_id):
    """View a work item"""
    try:
        work_item = WorkItem.query.get_or_404(work_item_id)
        return render_template('view_work_item.html', work_item=work_item)
    except Exception as e:
        flash(f'Error viewing work item: {str(e)}', 'danger')
        return redirect(url_for('main.work_items'))

@main_bp.route('/update_work_item_progress/<int:work_item_id>', methods=['GET', 'POST'])
def update_work_item_progress(work_item_id):
    """Update work item progress"""
    try:
        work_item = WorkItem.query.get_or_404(work_item_id)
        
        if not work_item.cost_code or not work_item.cost_code.rule_of_credit:
            flash('No rule of credit steps defined for this work item\'s cost code. Please add a rule of credit to the cost code first.', 'warning')
            return render_template('update_work_item_progress.html', work_item=work_item, rule_steps=[])
        
        rule_steps = work_item.cost_code.rule_of_credit.get_steps()
        
        if request.method == 'POST':
            progress_data = {}
            total_percentage = 0
            
            for step in rule_steps:
                step_name = step['name']
                step_progress = request.form.get(f'step_{step_name}')
                if step_progress:
                    progress_data[step_name] = int(step_progress)
                    total_percentage += int(step_progress) * (step['percentage'] / 100)
            
            # Update work item progress
            work_item.set_progress_data(progress_data)
            
            # Calculate earned values
            if work_item.budgeted_quantity:
                work_item.earned_quantity = work_item.budgeted_quantity * (total_percentage / 100)
            
            if work_item.budgeted_hours:
                work_item.earned_hours = work_item.budgeted_hours * (total_percentage / 100)
            
            db.session.commit()
            
            flash('Work item progress updated successfully!', 'success')
            return redirect(url_for('main.view_work_item', work_item_id=work_item_id))
        
        progress_data = work_item.get_steps_progress()
        
        # Add progress to steps
        step_progress = {}
        for step in rule_steps:
            step_name = step['name']
            step_progress[step_name] = progress_data.get(step_name, 0)
        
        return render_template('update_work_item_progress.html', 
                              work_item=work_item,
                              rule_steps=rule_steps,  # Changed variable name from 'steps' to 'rule_steps'
                              step_progress=step_progress)
    except Exception as e:
        flash(f'Error loading progress update form: {str(e)}', 'danger')
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
        return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))
    except Exception as e:
        flash(f'Error deleting work item: {str(e)}', 'danger')
        return redirect(url_for('main.work_items'))

# ===== REPORTS ROUTES =====

@main_bp.route('/reports')
def reports_index():
    """Reports index page"""
    try:
        projects = Project.query.all()
        return render_template('reports_index.html', projects=projects)
    except Exception as e:
        flash(f'Error loading reports page: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.index'))

# ===== PDF EXPORT ROUTES =====

@main_bp.route('/export/quantities/pdf/<int:project_id>')
def export_quantities_pdf_project(project_id):
    """Export quantities report as PDF for a project"""
    try:
        # Import the PDF generation function
        from reports.pdf_export import generate_quantities_report_pdf
        
        # Generate PDF - now returns BytesIO object directly
        buffer = generate_quantities_report_pdf(project_id=project_id)
        
        # Create a filename
        project = Project.query.get_or_404(project_id)
        filename = f"{project.project_id_str}_quantities_report.pdf"
        
        # Return the PDF file - send the BytesIO buffer directly
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.reports_index'))

@main_bp.route('/export/quantities/pdf/<int:project_id>/<int:sub_job_id>')
def export_quantities_pdf_subjob(project_id, sub_job_id):
    """Export quantities report as PDF for a sub job"""
    try:
        # Import the PDF generation function
        from reports.pdf_export import generate_quantities_report_pdf
        
        # Generate PDF - now returns BytesIO object directly
        buffer = generate_quantities_report_pdf(project_id=project_id, sub_job_id=sub_job_id)
        
        # Create a filename
        project = Project.query.get_or_404(project_id)
        sub_job = SubJob.query.get_or_404(sub_job_id)
        filename = f"{project.project_id_str}_{sub_job.sub_job_id_str}_quantities_report.pdf"
        
        # Return the PDF file - send the BytesIO buffer directly
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.reports_index'))
