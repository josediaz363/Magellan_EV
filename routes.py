from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, send_file
from models import db, Project, SubJob, WorkItem, CostCode, RuleOfCredit
from datetime import datetime
import os
from reports.pdf_export import generate_project_pdf

main = Blueprint('main', __name__)

@main.route('/')
def index():
    projects = Project.query.all()
    work_items = WorkItem.query.order_by(WorkItem.id.desc()).limit(10).all()
    return render_template('index.html', projects=projects, work_items=work_items)

@main.route('/settings')
def settings():
    return render_template('settings.html')

@main.route('/projects')
def projects():
    search_query = request.args.get('search', '')
    status_filter = request.args.get('status', 'All Status')
    sort_by = request.args.get('sort_by', 'name')
    
    query = Project.query
    
    if search_query:
        query = query.filter(Project.name.ilike(f'%{search_query}%') | 
                            Project.project_id.ilike(f'%{search_query}%') |
                            Project.description.ilike(f'%{search_query}%'))
    
    if status_filter != 'All Status':
        query = query.filter(Project.status == status_filter)
    
    if sort_by == 'name':
        query = query.order_by(Project.name)
    elif sort_by == 'id':
        query = query.order_by(Project.project_id)
    elif sort_by == 'progress':
        query = query.order_by(Project.percent_complete.desc())
    
    projects = query.all()
    
    return render_template('projects.html', projects=projects)

@main.route('/project/<int:project_id>')
def view_project(project_id):
    project = Project.query.get_or_404(project_id)
    sub_jobs = SubJob.query.filter_by(project_id=project_id).all()
    
    search_query = request.args.get('search', '')
    area_filter = request.args.get('area', 'All Areas')
    
    if search_query:
        sub_jobs = [sj for sj in sub_jobs if search_query.lower() in sj.name.lower() or 
                                            search_query.lower() in sj.sub_job_id.lower()]
    
    if area_filter != 'All Areas':
        sub_jobs = [sj for sj in sub_jobs if sj.area == area_filter]
    
    areas = list(set([sj.area for sj in SubJob.query.filter_by(project_id=project_id).all()]))
    
    return render_template('view_project.html', project=project, sub_jobs=sub_jobs, areas=areas)

@main.route('/add_project', methods=['GET', 'POST'])
def add_project():
    if request.method == 'POST':
        name = request.form.get('name')
        project_id = request.form.get('project_id')
        description = request.form.get('description')
        status = request.form.get('status', 'In Progress')
        
        new_project = Project(
            name=name,
            project_id=project_id,
            description=description,
            status=status,
            percent_complete=0
        )
        
        db.session.add(new_project)
        db.session.commit()
        
        flash('Project added successfully!', 'success')
        return redirect(url_for('main.projects'))
    
    return render_template('add_project.html')

@main.route('/edit_project/<int:project_id>', methods=['GET', 'POST'])
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    
    if request.method == 'POST':
        project.name = request.form.get('name')
        project.project_id = request.form.get('project_id')
        project.description = request.form.get('description')
        project.status = request.form.get('status')
        
        db.session.commit()
        
        flash('Project updated successfully!', 'success')
        return redirect(url_for('main.view_project', project_id=project.id))
    
    return render_template('edit_project.html', project=project)

@main.route('/delete_project/<int:project_id>', methods=['POST'])
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Delete associated sub jobs
    sub_jobs = SubJob.query.filter_by(project_id=project_id).all()
    for sub_job in sub_jobs:
        # Delete associated work items
        work_items = WorkItem.query.filter_by(sub_job_id=sub_job.id).all()
        for work_item in work_items:
            db.session.delete(work_item)
        db.session.delete(sub_job)
    
    db.session.delete(project)
    db.session.commit()
    
    flash('Project deleted successfully!', 'success')
    return redirect(url_for('main.projects'))

@main.route('/add_sub_job/<int:project_id>', methods=['GET', 'POST'])
def add_sub_job(project_id):
    project = Project.query.get_or_404(project_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        sub_job_id = request.form.get('sub_job_id')
        area = request.form.get('area')
        description = request.form.get('description')
        
        new_sub_job = SubJob(
            name=name,
            sub_job_id=sub_job_id,
            area=area,
            description=description,
            project_id=project_id,
            percent_complete=0
        )
        
        db.session.add(new_sub_job)
        db.session.commit()
        
        flash('Sub Job added successfully!', 'success')
        return redirect(url_for('main.view_project', project_id=project_id))
    
    return render_template('add_sub_job.html', project=project)

@main.route('/sub_job/<int:sub_job_id>')
def view_sub_job(sub_job_id):
    sub_job = SubJob.query.get_or_404(sub_job_id)
    project = Project.query.get_or_404(sub_job.project_id)
    
    search_query = request.args.get('search', '')
    discipline_filter = request.args.get('discipline', 'All Disciplines')
    
    work_items = WorkItem.query.filter_by(sub_job_id=sub_job_id)
    
    if search_query:
        work_items = work_items.filter(WorkItem.description.ilike(f'%{search_query}%'))
    
    if discipline_filter != 'All Disciplines':
        work_items = work_items.filter(WorkItem.discipline == discipline_filter)
    
    work_items = work_items.all()
    
    disciplines = list(set([wi.discipline for wi in WorkItem.query.filter_by(sub_job_id=sub_job_id).all() if wi.discipline]))
    
    # Calculate total budgeted hours
    total_budgeted_hours = sum(item.budgeted_hours for item in work_items if item.budgeted_hours)
    
    # Calculate total earned hours
    total_earned_hours = sum(item.earned_hours for item in work_items if item.earned_hours)
    
    return render_template('view_sub_job.html', 
                          sub_job=sub_job, 
                          project=project, 
                          work_items=work_items,
                          disciplines=disciplines,
                          total_budgeted_hours=total_budgeted_hours,
                          total_earned_hours=total_earned_hours)

@main.route('/edit_sub_job/<int:sub_job_id>', methods=['GET', 'POST'])
def edit_sub_job(sub_job_id):
    sub_job = SubJob.query.get_or_404(sub_job_id)
    
    if request.method == 'POST':
        sub_job.name = request.form.get('name')
        sub_job.sub_job_id = request.form.get('sub_job_id')
        sub_job.area = request.form.get('area')
        sub_job.description = request.form.get('description')
        
        db.session.commit()
        
        flash('Sub Job updated successfully!', 'success')
        return redirect(url_for('main.view_sub_job', sub_job_id=sub_job.id))
    
    return render_template('edit_sub_job.html', sub_job=sub_job)

@main.route('/delete_sub_job/<int:sub_job_id>', methods=['POST'])
def delete_sub_job(sub_job_id):
    sub_job = SubJob.query.get_or_404(sub_job_id)
    project_id = sub_job.project_id
    
    # Delete associated work items
    work_items = WorkItem.query.filter_by(sub_job_id=sub_job_id).all()
    for work_item in work_items:
        db.session.delete(work_item)
    
    db.session.delete(sub_job)
    db.session.commit()
    
    flash('Sub Job deleted successfully!', 'success')
    return redirect(url_for('main.view_project', project_id=project_id))

@main.route('/work_items')
def work_items():
    search_query = request.args.get('search', '')
    project_filter = request.args.get('project', 'All Projects')
    discipline_filter = request.args.get('discipline', 'All Disciplines')
    sort_by = request.args.get('sort_by', 'id')
    
    query = WorkItem.query.join(SubJob).join(Project)
    
    if search_query:
        query = query.filter(WorkItem.description.ilike(f'%{search_query}%'))
    
    if project_filter != 'All Projects':
        query = query.filter(Project.id == project_filter)
    
    if discipline_filter != 'All Disciplines':
        query = query.filter(WorkItem.discipline == discipline_filter)
    
    if sort_by == 'id':
        query = query.order_by(WorkItem.id)
    elif sort_by == 'description':
        query = query.order_by(WorkItem.description)
    elif sort_by == 'progress':
        query = query.order_by(WorkItem.percent_complete_quantity.desc())
    
    work_items = query.all()
    projects = Project.query.all()
    disciplines = list(set([wi.discipline for wi in WorkItem.query.all() if wi.discipline]))
    
    return render_template('work_items.html', 
                          work_items=work_items, 
                          projects=projects, 
                          disciplines=disciplines)

@main.route('/add_work_item/<int:sub_job_id>', methods=['GET', 'POST'])
def add_work_item(sub_job_id):
    sub_job = SubJob.query.get_or_404(sub_job_id)
    cost_codes = CostCode.query.all()
    rules_of_credit = RuleOfCredit.query.all()
    
    if request.method == 'POST':
        description = request.form.get('description')
        discipline = request.form.get('discipline')
        cost_code_id = request.form.get('cost_code_id')
        rule_of_credit_id = request.form.get('rule_of_credit_id')
        drawing_number = request.form.get('drawing_number')
        activity_id = request.form.get('activity_id')
        budgeted_quantity = request.form.get('budgeted_quantity')
        unit_of_measure = request.form.get('unit_of_measure')
        budgeted_hours = request.form.get('budgeted_hours')
        
        new_work_item = WorkItem(
            description=description,
            discipline=discipline,
            cost_code_id=cost_code_id if cost_code_id else None,
            rule_of_credit_id=rule_of_credit_id if rule_of_credit_id else None,
            drawing_number=drawing_number,
            activity_id=activity_id,
            budgeted_quantity=float(budgeted_quantity) if budgeted_quantity else 0,
            earned_quantity=0,
            unit_of_measure=unit_of_measure,
            budgeted_hours=float(budgeted_hours) if budgeted_hours else 0,
            earned_hours=0,
            percent_complete_quantity=0,
            percent_complete_hours=0,
            sub_job_id=sub_job_id
        )
        
        db.session.add(new_work_item)
        db.session.commit()
        
        flash('Work Item added successfully!', 'success')
        return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))
    
    return render_template('add_work_item.html', sub_job=sub_job, cost_codes=cost_codes, rules_of_credit=rules_of_credit)

@main.route('/view_work_item/<int:work_item_id>')
def view_work_item(work_item_id):
    work_item = WorkItem.query.get_or_404(work_item_id)
    sub_job = SubJob.query.get_or_404(work_item.sub_job_id)
    project = Project.query.get_or_404(sub_job.project_id)
    
    return render_template('view_work_item.html', 
                          work_item=work_item, 
                          sub_job=sub_job, 
                          project=project)

@main.route('/edit_work_item/<int:work_item_id>', methods=['GET', 'POST'])
def edit_work_item(work_item_id):
    work_item = WorkItem.query.get_or_404(work_item_id)
    cost_codes = CostCode.query.all()
    rules_of_credit = RuleOfCredit.query.all()
    
    if request.method == 'POST':
        work_item.description = request.form.get('description')
        work_item.discipline = request.form.get('discipline')
        work_item.cost_code_id = request.form.get('cost_code_id') if request.form.get('cost_code_id') else None
        work_item.rule_of_credit_id = request.form.get('rule_of_credit_id') if request.form.get('rule_of_credit_id') else None
        work_item.drawing_number = request.form.get('drawing_number')
        work_item.activity_id = request.form.get('activity_id')
        work_item.budgeted_quantity = float(request.form.get('budgeted_quantity')) if request.form.get('budgeted_quantity') else 0
        work_item.unit_of_measure = request.form.get('unit_of_measure')
        work_item.budgeted_hours = float(request.form.get('budgeted_hours')) if request.form.get('budgeted_hours') else 0
        
        db.session.commit()
        
        flash('Work Item updated successfully!', 'success')
        return redirect(url_for('main.view_work_item', work_item_id=work_item.id))
    
    return render_template('edit_work_item.html', 
                          work_item=work_item, 
                          cost_codes=cost_codes, 
                          rules_of_credit=rules_of_credit)

@main.route('/delete_work_item/<int:work_item_id>', methods=['POST'])
def delete_work_item(work_item_id):
    work_item = WorkItem.query.get_or_404(work_item_id)
    sub_job_id = work_item.sub_job_id
    
    db.session.delete(work_item)
    db.session.commit()
    
    flash('Work Item deleted successfully!', 'success')
    return redirect(url_for('main.view_sub_job', sub_job_id=sub_job_id))

@main.route('/update_work_item_progress/<int:work_item_id>', methods=['GET', 'POST'])
def update_work_item_progress(work_item_id):
    work_item = WorkItem.query.get_or_404(work_item_id)
    
    if request.method == 'POST':
        earned_quantity = float(request.form.get('earned_quantity')) if request.form.get('earned_quantity') else 0
        
        # Update earned quantity
        work_item.earned_quantity = earned_quantity
        
        # Calculate percent complete for quantity
        if work_item.budgeted_quantity > 0:
            work_item.percent_complete_quantity = (earned_quantity / work_item.budgeted_quantity) * 100
        else:
            work_item.percent_complete_quantity = 0
        
        # Calculate earned hours based on percent complete
        work_item.earned_hours = (work_item.percent_complete_quantity / 100) * work_item.budgeted_hours
        work_item.percent_complete_hours = work_item.percent_complete_quantity
        
        # Update sub job progress
        sub_job = SubJob.query.get(work_item.sub_job_id)
        work_items = WorkItem.query.filter_by(sub_job_id=sub_job.id).all()
        
        total_budgeted_hours = sum(item.budgeted_hours for item in work_items if item.budgeted_hours)
        total_earned_hours = sum(item.earned_hours for item in work_items if item.earned_hours)
        
        if total_budgeted_hours > 0:
            sub_job.percent_complete = (total_earned_hours / total_budgeted_hours) * 100
        else:
            sub_job.percent_complete = 0
        
        # Update project progress
        project = Project.query.get(sub_job.project_id)
        sub_jobs = SubJob.query.filter_by(project_id=project.id).all()
        
        # Calculate weighted progress based on budgeted hours in each sub job
        total_project_budgeted_hours = 0
        total_project_earned_hours = 0
        
        for sj in sub_jobs:
            sj_work_items = WorkItem.query.filter_by(sub_job_id=sj.id).all()
            sj_budgeted_hours = sum(item.budgeted_hours for item in sj_work_items if item.budgeted_hours)
            sj_earned_hours = sum(item.earned_hours for item in sj_work_items if item.earned_hours)
            
            total_project_budgeted_hours += sj_budgeted_hours
            total_project_earned_hours += sj_earned_hours
        
        if total_project_budgeted_hours > 0:
            project.percent_complete = (total_project_earned_hours / total_project_budgeted_hours) * 100
        else:
            project.percent_complete = 0
        
        db.session.commit()
        
        flash('Work Item progress updated successfully!', 'success')
        return redirect(url_for('main.view_work_item', work_item_id=work_item.id))
    
    return render_template('update_work_item_progress.html', work_item=work_item)

@main.route('/cost_codes')
def list_cost_codes():
    search_query = request.args.get('search', '')
    project_filter = request.args.get('project', 'All Projects')
    discipline_filter = request.args.get('discipline', 'All Disciplines')
    
    query = CostCode.query
    
    if search_query:
        query = query.filter(CostCode.cost_code_id_str.ilike(f'%{search_query}%') | 
                            CostCode.description.ilike(f'%{search_query}%'))
    
    if discipline_filter != 'All Disciplines':
        query = query.filter(CostCode.discipline == discipline_filter)
    
    cost_codes = query.all()
    
    # Filter by project if needed (this would require joining with work items and sub jobs)
    if project_filter != 'All Projects':
        work_items = WorkItem.query.join(SubJob).filter(SubJob.project_id == project_filter).all()
        cost_code_ids = [wi.cost_code_id for wi in work_items if wi.cost_code_id]
        cost_codes = [cc for cc in cost_codes if cc.id in cost_code_ids]
    
    projects = Project.query.all()
    disciplines = list(set([cc.discipline for cc in CostCode.query.all() if cc.discipline]))
    
    return render_template('list_cost_codes.html', 
                          cost_codes=cost_codes, 
                          projects=projects, 
                          disciplines=disciplines)

@main.route('/add_cost_code', methods=['GET', 'POST'])
def add_cost_code():
    if request.method == 'POST':
        cost_code_id_str = request.form.get('cost_code_id_str')
        description = request.form.get('description')
        discipline = request.form.get('discipline')
        
        new_cost_code = CostCode(
            cost_code_id_str=cost_code_id_str,
            description=description,
            discipline=discipline
        )
        
        db.session.add(new_cost_code)
        db.session.commit()
        
        flash('Cost Code added successfully!', 'success')
        return redirect(url_for('main.list_cost_codes'))
    
    return render_template('add_cost_code.html')

@main.route('/edit_cost_code/<int:cost_code_id>', methods=['GET', 'POST'])
def edit_cost_code(cost_code_id):
    cost_code = CostCode.query.get_or_404(cost_code_id)
    
    if request.method == 'POST':
        cost_code.cost_code_id_str = request.form.get('cost_code_id_str')
        cost_code.description = request.form.get('description')
        cost_code.discipline = request.form.get('discipline')
        
        db.session.commit()
        
        flash('Cost Code updated successfully!', 'success')
        return redirect(url_for('main.list_cost_codes'))
    
    return render_template('edit_cost_code.html', cost_code=cost_code)

@main.route('/delete_cost_code/<int:cost_code_id>', methods=['POST'])
def delete_cost_code(cost_code_id):
    cost_code = CostCode.query.get_or_404(cost_code_id)
    
    # Check if cost code is used in any work items
    work_items = WorkItem.query.filter_by(cost_code_id=cost_code_id).all()
    if work_items:
        flash('Cannot delete Cost Code as it is used in Work Items!', 'danger')
        return redirect(url_for('main.list_cost_codes'))
    
    db.session.delete(cost_code)
    db.session.commit()
    
    flash('Cost Code deleted successfully!', 'success')
    return redirect(url_for('main.list_cost_codes'))

@main.route('/rules_of_credit')
def list_rules_of_credit():
    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'name')
    
    query = RuleOfCredit.query
    
    if search_query:
        query = query.filter(RuleOfCredit.name.ilike(f'%{search_query}%') | 
                            RuleOfCredit.description.ilike(f'%{search_query}%'))
    
    if sort_by == 'name':
        query = query.order_by(RuleOfCredit.name)
    elif sort_by == 'description':
        query = query.order_by(RuleOfCredit.description)
    
    rules_of_credit = query.all()
    
    return render_template('list_rules_of_credit.html', rules_of_credit=rules_of_credit)

@main.route('/add_rule_of_credit', methods=['GET', 'POST'])
def add_rule_of_credit():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        rule_type = request.form.get('rule_type')
        
        new_rule = RuleOfCredit(
            name=name,
            description=description,
            rule_type=rule_type
        )
        
        db.session.add(new_rule)
        db.session.commit()
        
        flash('Rule of Credit added successfully!', 'success')
        return redirect(url_for('main.list_rules_of_credit'))
    
    return render_template('add_rule_of_credit.html')

@main.route('/edit_rule_of_credit/<int:rule_id>', methods=['GET', 'POST'])
def edit_rule_of_credit(rule_id):
    rule = RuleOfCredit.query.get_or_404(rule_id)
    
    if request.method == 'POST':
        rule.name = request.form.get('name')
        rule.description = request.form.get('description')
        rule.rule_type = request.form.get('rule_type')
        
        db.session.commit()
        
        flash('Rule of Credit updated successfully!', 'success')
        return redirect(url_for('main.list_rules_of_credit'))
    
    return render_template('edit_rule_of_credit.html', rule=rule)

@main.route('/delete_rule_of_credit/<int:rule_id>', methods=['POST'])
def delete_rule_of_credit(rule_id):
    rule = RuleOfCredit.query.get_or_404(rule_id)
    
    # Check if rule is used in any work items
    work_items = WorkItem.query.filter_by(rule_of_credit_id=rule_id).all()
    if work_items:
        flash('Cannot delete Rule of Credit as it is used in Work Items!', 'danger')
        return redirect(url_for('main.list_rules_of_credit'))
    
    db.session.delete(rule)
    db.session.commit()
    
    flash('Rule of Credit deleted successfully!', 'success')
    return redirect(url_for('main.list_rules_of_credit'))

@main.route('/reports')
def reports_index():
    projects = Project.query.all()
    return render_template('reports_index.html', projects=projects)

@main.route('/generate_project_report/<int:project_id>')
def generate_project_report(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Generate PDF report
    pdf_path = generate_project_pdf(project)
    
    # Send the file
    return send_file(pdf_path, as_attachment=True, download_name=f"{project.name}_report.pdf")
