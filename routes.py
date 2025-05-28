from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import traceback
from datetime import datetime, timedelta
from sqlalchemy import func, desc, or_
from .models import db, Project, SubJob, WorkItem, CostCode, RuleOfCredit, ProjectCostCode, DISCIPLINE_CHOICES
import json
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Dashboard page"""
    try:
        # Get all projects for the dropdown
        projects = Project.query.all()
        
        # Get recent work items (limit to 10)
        work_items = WorkItem.query.order_by(WorkItem.id.desc()).limit(10).all()
        
        return render_template('index.html', projects=projects, work_items=work_items)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('index.html', projects=[], work_items=[])

@main_bp.route('/projects')
def projects():
    """Projects page"""
    try:
        # Get all projects with additional data
        projects_with_data = []
        projects = Project.query.all()
        
        for project in projects:
            # Get sub jobs count
            sub_jobs_count = SubJob.query.filter_by(project_id=project.id).count()
            
            # Get work items count
            work_items_count = WorkItem.query.join(SubJob).filter(SubJob.project_id == project.id).count()
            
            # Calculate total budgeted and earned hours
            total_budgeted_hours = db.session.query(func.sum(WorkItem.budgeted_man_hours)).join(SubJob).filter(SubJob.project_id == project.id).scalar() or 0
            total_earned_hours = db.session.query(func.sum(WorkItem.earned_man_hours)).join(SubJob).filter(SubJob.project_id == project.id).scalar() or 0
            
            # Calculate progress
            progress = 0
            if total_budgeted_hours > 0:
                progress = (total_earned_hours / total_budgeted_hours) * 100
            
            # Add to projects with data
            projects_with_data.append({
                'project': project,
                'sub_jobs_count': sub_jobs_count,
                'work_items_count': work_items_count,
                'total_budgeted_hours': total_budgeted_hours,
                'total_earned_hours': total_earned_hours,
                'progress': progress
            })
        
        return render_template('projects.html', projects=projects_with_data)
    except Exception as e:
        flash(f'Error loading projects: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('projects.html', projects=[])

@main_bp.route('/add_project', methods=['GET', 'POST'])
def add_project():
    """Add a new project"""
    try:
        if request.method == 'POST':
            # Get form data
            project_id_str = request.form.get('project_id')
            name = request.form.get('name')
            description = request.form.get('description')
            
            # Create new project
            new_project = Project(
                project_id_str=project_id_str,
                name=name,
                description=description
            )
            
            db.session.add(new_project)
            db.session.commit()
            
            flash('Project added successfully!', 'success')
            return redirect(url_for('main.projects'))
        
        return render_template('add_project.html')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding project: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('add_project.html')

@main_bp.route('/view_project/<int:project_id>')
def view_project(project_id):
    """View a project"""
    try:
        project = Project.query.get_or_404(project_id)
        sub_jobs = SubJob.query.filter_by(project_id=project_id).all()
        
        # Calculate project metrics
        total_budgeted_hours = db.session.query(func.sum(WorkItem.budgeted_man_hours)).join(SubJob).filter(SubJob.project_id == project_id).scalar() or 0
        total_earned_hours = db.session.query(func.sum(WorkItem.earned_man_hours)).join(SubJob).filter(SubJob.project_id == project_id).scalar() or 0
        
        # Calculate progress for each sub job
        sub_jobs_with_progress = []
        for sub_job in sub_jobs:
            work_items_count = WorkItem.query.filter_by(sub_job_id=sub_job.id).count()
            
            # Calculate sub job progress
            sub_job_budgeted_hours = db.session.query(func.sum(WorkItem.budgeted_man_hours)).filter(WorkItem.sub_job_id == sub_job.id).scalar() or 0
            sub_job_earned_hours = db.session.query(func.sum(WorkItem.earned_man_hours)).filter(WorkItem.sub_job_id == sub_job.id).scalar() or 0
            
            sub_job_progress = 0
            if sub_job_budgeted_hours > 0:
                sub_job_progress = (sub_job_earned_hours / sub_job_budgeted_hours) * 100
            
            sub_jobs_with_progress.append({
                'sub_job': sub_job,
                'work_items_count': work_items_count,
                'progress': sub_job_progress
            })
        
        # Calculate overall progress
        overall_progress = 0
        if total_budgeted_hours > 0:
            overall_progress = (total_earned_hours / total_budgeted_hours) * 100
        
        return render_template('view_project.html', 
                              project=project, 
                              sub_jobs=sub_jobs_with_progress,
                              total_budgeted_hours=total_budgeted_hours,
                              total_earned_hours=total_earned_hours,
                              overall_progress=overall_progress)
    except Exception as e:
        flash(f'Error loading project: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.projects'))

@main_bp.route('/edit_project/<int:project_id>', methods=['GET', 'POST'])
def edit_project(project_id):
    """Edit a project"""
    try:
        project = Project.query.get_or_404(project_id)
        
        if request.method == 'POST':
            # Update project data
            project.project_id_str = request.form.get('project_id')
            project.name = request.form.get('name')
            project.description = request.form.get('description')
            
            db.session.commit()
            
            flash('Project updated successfully!', 'success')
            return redirect(url_for('main.view_project', project_id=project_id))
        
        return render_template('edit_project.html', project=project)
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating project: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.view_project', project_id=project_id))

@main_bp.route('/delete_project/<int:project_id>', methods=['POST'])
def delete_project(project_id):
    """Delete a project"""
    try:
        project = Project.query.get_or_404(project_id)
        
        # Delete all sub jobs and work items associated with this project
        sub_jobs = SubJob.query.filter_by(project_id=project_id).all()
        for sub_job in sub_jobs:
            work_items = WorkItem.query.filter_by(sub_job_id=sub_job.id).all()
            for work_item in work_items:
                db.session.delete(work_item)
            db.session.delete(sub_job)
        
        # Delete project cost code associations
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
            # Get form data
            sub_job_id_str = request.form.get('sub_job_id')
            name = request.form.get('name')
            area = request.form.get('area')
            description = request.form.get('description')
            
            # Create new sub job
            new_sub_job = SubJob(
                sub_job_id_str=sub_job_id_str,
                name=name,
                area=area,
                description=description,
                project_id=project_id
            )
            
            db.session.add(new_sub_job)
            db.session.commit()
            
            flash('Sub job added successfully!', 'success')
            return redirect(url_for('main.view_project', project_id=project_id))
        
        return render_template('add_sub_job.html', project=project)
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding sub job: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.view_project', project_id=project_id))

@main_bp.route('/view_sub_job/<int:sub_job_id>')
def view_sub_job(sub_job_id):
    """View a sub job"""
    try:
        sub_job = SubJob.query.get_or_404(sub_job_id)
        work_items = WorkItem.query.filter_by(sub_job_id=sub_job_id).all()
        
        # Calculate sub job metrics
        total_budgeted_hours = db.session.query(func.sum(WorkItem.budgeted_man_hours)).filter(WorkItem.sub_job_id == sub_job_id).scalar() or 0
        total_earned_hours = db.session.query(func.sum(WorkItem.earned_man_hours)).filter(WorkItem.sub_job_id == sub_job_id).scalar() or 0
        
        # Calculate overall progress
        overall_progress = 0
        if total_budgeted_hours > 0:
            overall_progress = (total_earned_hours / total_budgeted_hours) * 100
        
        return render_template('view_sub_job.html', 
                              sub_job=sub_job, 
                              work_items=work_items,
                              total_budgeted_hours=total_budgeted_hours,
                              total_earned_hours=total_earned_hours,
                              overall_progress=overall_progress)
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
    """Edit a cost code"""
    try:
        cost_code = CostCode.query.get_or_404(cost_code_id)
        
        if request.method == 'POST':
            # Update cost code data
            cost_code.cost_code_id_str = request.form.get('code')
            cost_code.description = request.form.get('description')
            cost_code.discipline = request.form.get('discipline')
            cost_code.rule_of_credit_id = request.form.get('rule_of_credit_id') or None
            
            # Update project associations
            project_ids = request.form.getlist('project_ids')
            
            # Remove existing associations
            ProjectCostCode.query.filter_by(cost_code_id=cost_code_id).delete()
            
            # Create new associations
            for project_id in project_ids:
                project_cost_code = ProjectCostCode(
                    project_id=project_id,
                    cost_code_id=cost_code_id
                )
                db.session.add(project_cost_code)
            
            db.session.commit()
            
            flash('Cost code updated successfully!', 'success')
            return redirect(url_for('main.list_cost_codes'))
        
        # Get all projects and rules of credit for the form
        projects = Project.query.all()
        rules = RuleOfCredit.query.all()
        
        # Get associated project IDs
        associated_project_ids = [pcc.project_id for pcc in ProjectCostCode.query.filter_by(cost_code_id=cost_code_id).all()]
        
        return render_template('edit_cost_code.html', 
                              cost_code=cost_code,
                              projects=projects,
                              rules=rules,
                              associated_project_ids=associated_project_ids,
                              disciplines=DISCIPLINE_CHOICES)
    except Exception as e:
        db.session.rollback()
        flash(f'Error editing cost code: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_cost_codes'))

@main_bp.route('/delete_cost_code/<int:cost_code_id>', methods=['POST'])
def delete_cost_code(cost_code_id):
    """Delete a cost code"""
    try:
        cost_code = CostCode.query.get_or_404(cost_code_id)
        
        # Check if cost code is used by any work items
        work_items = WorkItem.query.filter_by(cost_code_id=cost_code_id).all()
        if work_items:
            flash('Cannot delete cost code that is used by work items.', 'danger')
            return redirect(url_for('main.list_cost_codes'))
        
        # Delete project associations
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
            # Get form data
            name = request.form.get('name')
            description = request.form.get('description')
            
            # Get milestone data
            milestones = []
            for i in range(10):  # Assuming max 10 milestones
                milestone_name = request.form.get(f'milestone_name_{i}')
                milestone_weight = request.form.get(f'milestone_weight_{i}')
                
                if milestone_name and milestone_weight:
                    milestones.append({
                        'name': milestone_name,
                        'weight': float(milestone_weight)
                    })
            
            # Create new rule of credit
            new_rule = RuleOfCredit(
                name=name,
                description=description,
                milestones=json.dumps(milestones)
            )
            
            db.session.add(new_rule)
            db.session.commit()
            
            flash('Rule of credit added successfully!', 'success')
            return redirect(url_for('main.list_rules_of_credit'))
        
        return render_template('add_rule_of_credit.html')
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
            # Update rule data
            rule.name = request.form.get('name')
            rule.description = request.form.get('description')
            
            # Get milestone data
            milestones = []
            for i in range(10):  # Assuming max 10 milestones
                milestone_name = request.form.get(f'milestone_name_{i}')
                milestone_weight = request.form.get(f'milestone_weight_{i}')
                
                if milestone_name and milestone_weight:
                    milestones.append({
                        'name': milestone_name,
                        'weight': float(milestone_weight)
                    })
            
            rule.milestones = json.dumps(milestones)
            
            db.session.commit()
            
            flash('Rule of credit updated successfully!', 'success')
            return redirect(url_for('main.list_rules_of_credit'))
        
        # Parse milestones for the form
        milestones = json.loads(rule.milestones) if rule.milestones else []
        
        return render_template('edit_rule_of_credit.html', rule=rule, milestones=milestones)
    except Exception as e:
        db.session.rollback()
        flash(f'Error editing rule of credit: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.list_rules_of_credit'))

@main_bp.route('/delete_rule_of_credit/<int:rule_id>', methods=['POST'])
def delete_rule_of_credit(rule_id):
    """Delete a rule of credit"""
    try:
        rule = RuleOfCredit.query.get_or_404(rule_id)
        
        # Check if rule is used by any cost codes
        cost_codes = CostCode.query.filter_by(rule_of_credit_id=rule_id).all()
        if cost_codes:
            flash('Cannot delete rule of credit that is used by cost codes.', 'danger')
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
    """List all work items"""
    try:
        work_items = WorkItem.query.all()
        return render_template('work_items.html', work_items=work_items)
    except Exception as e:
        flash(f'Error loading work items: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('work_items.html', work_items=[])

@main_bp.route('/add_work_item', methods=['GET', 'POST'])
@main_bp.route('/add_work_item/<int:sub_job_id>', methods=['GET', 'POST'])
def add_work_item(sub_job_id=None):
    """Add a new work item"""
    try:
        if request.method == 'POST':
            # Get form data
            work_item_id_str = request.form.get('work_item_id')
            description = request.form.get('description')
            project_id = request.form.get('project_id')
            sub_job_id = request.form.get('sub_job_id')
            cost_code_id = request.form.get('cost_code_id')
            unit_of_measure = request.form.get('unit_of_measure')
            budgeted_quantity = request.form.get('budgeted_quantity')
            budgeted_man_hours = request.form.get('budgeted_man_hours')
            
            # Create new work item
            new_work_item = WorkItem(
                work_item_id_str=work_item_id_str,
                description=description,
                sub_job_id=sub_job_id,
                cost_code_id=cost_code_id,
                unit_of_measure=unit_of_measure,
                budgeted_quantity=float(budgeted_quantity) if budgeted_quantity else 0,
                budgeted_man_hours=float(budgeted_man_hours) if budgeted_man_hours else 0,
                earned_quantity=0,
                earned_man_hours=0,
                percent_complete_hours=0,
                milestone_progress=json.dumps({})
            )
            
            db.session.add(new_work_item)
            db.session.commit()
            
            flash('Work item added successfully!', 'success')
            return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))
        
        # Get projects for the form
        projects = Project.query.all()
        
        # If sub_job_id is provided, get the sub job and its project
        selected_sub_job = None
        selected_project = None
        if sub_job_id:
            selected_sub_job = SubJob.query.get_or_404(sub_job_id)
            selected_project = selected_sub_job.project
        
        return render_template('add_work_item.html', 
                              projects=projects,
                              selected_project=selected_project,
                              selected_sub_job=selected_sub_job)
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding work item: {str(e)}', 'danger')
        traceback.print_exc()
        if sub_job_id:
            return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))
        else:
            return redirect(url_for('main.work_items'))

@main_bp.route('/view_work_item/<int:work_item_id>')
def view_work_item(work_item_id):
    """View a work item"""
    try:
        work_item = WorkItem.query.get_or_404(work_item_id)
        
        # Parse milestone progress
        milestone_progress = json.loads(work_item.milestone_progress) if work_item.milestone_progress else {}
        
        # Get rule of credit milestones if available
        milestones = []
        if work_item.cost_code and work_item.cost_code.rule_of_credit:
            milestones = json.loads(work_item.cost_code.rule_of_credit.milestones) if work_item.cost_code.rule_of_credit.milestones else []
        
        return render_template('view_work_item.html', 
                              work_item=work_item,
                              milestone_progress=milestone_progress,
                              milestones=milestones)
    except Exception as e:
        flash(f'Error loading work item: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.work_items'))

@main_bp.route('/edit_work_item/<int:work_item_id>', methods=['GET', 'POST'])
def edit_work_item(work_item_id):
    """Edit a work item"""
    try:
        work_item = WorkItem.query.get_or_404(work_item_id)
        
        if request.method == 'POST':
            # Update work item data
            work_item.work_item_id_str = request.form.get('work_item_id')
            work_item.description = request.form.get('description')
            
            # Get the sub job ID from the form
            new_sub_job_id = request.form.get('sub_job_id')
            if new_sub_job_id and new_sub_job_id != str(work_item.sub_job_id):
                work_item.sub_job_id = new_sub_job_id
            
            # Get the cost code ID from the form
            new_cost_code_id = request.form.get('cost_code_id')
            if new_cost_code_id and new_cost_code_id != str(work_item.cost_code_id):
                work_item.cost_code_id = new_cost_code_id
                # Reset milestone progress if cost code changes
                work_item.milestone_progress = json.dumps({})
            
            work_item.unit_of_measure = request.form.get('unit_of_measure')
            work_item.budgeted_quantity = float(request.form.get('budgeted_quantity')) if request.form.get('budgeted_quantity') else 0
            work_item.budgeted_man_hours = float(request.form.get('budgeted_man_hours')) if request.form.get('budgeted_man_hours') else 0
            
            db.session.commit()
            
            flash('Work item updated successfully!', 'success')
            return redirect(url_for('main.view_work_item', work_item_id=work_item_id))
        
        # Get projects for the form
        projects = Project.query.all()
        
        # Get the current project and sub job
        sub_job = SubJob.query.get(work_item.sub_job_id)
        project = sub_job.project if sub_job else None
        
        return render_template('edit_work_item.html', 
                              work_item=work_item,
                              projects=projects,
                              selected_project=project,
                              selected_sub_job=sub_job)
    except Exception as e:
        db.session.rollback()
        flash(f'Error editing work item: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.view_work_item', work_item_id=work_item_id))

@main_bp.route('/update_work_item_progress/<int:work_item_id>', methods=['GET', 'POST'])
def update_work_item_progress(work_item_id):
    """Update work item progress"""
    try:
        work_item = WorkItem.query.get_or_404(work_item_id)
        
        # Get rule of credit milestones if available
        milestones = []
        if work_item.cost_code and work_item.cost_code.rule_of_credit:
            milestones = json.loads(work_item.cost_code.rule_of_credit.milestones) if work_item.cost_code.rule_of_credit.milestones else []
        
        # Parse current milestone progress
        milestone_progress = json.loads(work_item.milestone_progress) if work_item.milestone_progress else {}
        
        if request.method == 'POST':
            # Update milestone progress
            new_milestone_progress = {}
            total_progress = 0
            
            for milestone in milestones:
                milestone_name = milestone['name']
                milestone_weight = milestone['weight']
                
                # Get progress value from form
                progress_value = request.form.get(f'milestone_{milestone_name}')
                if progress_value:
                    progress_percent = float(progress_value)
                    new_milestone_progress[milestone_name] = progress_percent
                    total_progress += (progress_percent / 100) * milestone_weight
            
            # Update work item
            work_item.milestone_progress = json.dumps(new_milestone_progress)
            work_item.percent_complete_hours = total_progress
            work_item.earned_man_hours = (total_progress / 100) * work_item.budgeted_man_hours
            work_item.earned_quantity = (total_progress / 100) * work_item.budgeted_quantity
            
            db.session.commit()
            
            flash('Work item progress updated successfully!', 'success')
            return redirect(url_for('main.view_work_item', work_item_id=work_item_id))
        
        return render_template('update_work_item_progress.html', 
                              work_item=work_item,
                              milestones=milestones,
                              milestone_progress=milestone_progress)
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating work item progress: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.view_work_item', work_item_id=work_item_id))

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
        return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting work item: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.view_work_item', work_item_id=work_item_id))

@main_bp.route('/reports')
def reports():
    """Reports page"""
    try:
        projects = Project.query.all()
        return render_template('reports_index.html', projects=projects)
    except Exception as e:
        flash(f'Error loading reports: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('reports_index.html', projects=[])

@main_bp.route('/settings')
def settings():
    """Settings page"""
    return render_template('settings.html')

# API endpoints
@main_bp.route('/api/get_sub_jobs/<int:project_id>')
def get_sub_jobs(project_id):
    """API endpoint to get sub jobs for a project"""
    try:
        sub_jobs = SubJob.query.filter_by(project_id=project_id).all()
        return jsonify([{'id': sub_job.id, 'name': sub_job.name} for sub_job in sub_jobs])
    except Exception as e:
        return jsonify({'error': str(e)})

@main_bp.route('/api/get_cost_codes/<int:project_id>')
def get_cost_codes(project_id):
    """API endpoint to get cost codes for a project"""
    try:
        # Get cost codes associated with the project through the join table
        project_cost_codes = ProjectCostCode.query.filter_by(project_id=project_id).all()
        cost_code_ids = [pcc.cost_code_id for pcc in project_cost_codes]
        cost_codes = CostCode.query.filter(CostCode.id.in_(cost_code_ids)).all()
        
        return jsonify([{'id': cc.id, 'name': f"{cc.cost_code_id_str} - {cc.description}"} for cc in cost_codes])
    except Exception as e:
        return jsonify({'error': str(e)})

@main_bp.route('/api/get_rule_of_credit/<int:cost_code_id>')
def get_rule_of_credit(cost_code_id):
    """API endpoint to get rule of credit for a cost code"""
    try:
        cost_code = CostCode.query.get_or_404(cost_code_id)
        if cost_code.rule_of_credit:
            rule = cost_code.rule_of_credit
            milestones = json.loads(rule.milestones) if rule.milestones else []
            return jsonify({
                'id': rule.id,
                'name': rule.name,
                'description': rule.description,
                'milestones': milestones
            })
        else:
            return jsonify({'error': 'No rule of credit associated with this cost code'})
    except Exception as e:
        return jsonify({'error': str(e)})

@main_bp.route('/api/get_project_progress/<int:project_id>')
def get_project_progress(project_id):
    """API endpoint to get overall progress for a project"""
    try:
        # Calculate project metrics
        total_budgeted_hours = db.session.query(func.sum(WorkItem.budgeted_man_hours)).join(SubJob).filter(SubJob.project_id == project_id).scalar() or 0
        total_earned_hours = db.session.query(func.sum(WorkItem.earned_man_hours)).join(SubJob).filter(SubJob.project_id == project_id).scalar() or 0
        
        # Calculate overall progress
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
