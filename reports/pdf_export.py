import os
import datetime
from flask import render_template
from weasyprint import HTML

def generate_quantities_report_pdf(project_id=None, sub_job_id=None):
    """
    Generate a PDF report for quantities data
    
    Args:
        project_id (int): Project ID to generate report for
        sub_job_id (int): Sub Job ID to generate report for
        
    Returns:
        bytes: PDF file data
    """
    from models import Project, SubJob, WorkItem, CostCode
    
    # Get data based on project_id or sub_job_id
    if sub_job_id:
        sub_job = SubJob.query.get_or_404(sub_job_id)
        project = Project.query.get_or_404(sub_job.project_id)
        work_items = WorkItem.query.filter_by(sub_job_id=sub_job_id).all()
        report_title = f"Sub Job by Quantities"
        report_subtitle = f"{project.project_id_str} - {project.name} - {sub_job.name}"
    elif project_id:
        project = Project.query.get_or_404(project_id)
        work_items = WorkItem.query.filter_by(project_id=project_id).all()
        report_title = f"Project by Quantities"
        report_subtitle = f"{project.project_id_str} - {project.name}"
    else:
        raise ValueError("Either project_id or sub_job_id must be provided")
    
    # Group work items by discipline and cost code
    grouped_items = {}
    discipline_totals = {}
    total_budgeted_quantity = 0
    total_earned_quantity = 0
    
    for item in work_items:
        if not item.cost_code:
            continue
            
        discipline = item.cost_code.discipline
        cost_code_id = item.cost_code_id
        
        # Initialize discipline if not exists
        if discipline not in grouped_items:
            grouped_items[discipline] = {}
            discipline_totals[discipline] = {
                'total_budgeted_quantity': 0,
                'total_earned_quantity': 0
            }
        
        # Initialize cost code if not exists
        if cost_code_id not in grouped_items[discipline]:
            grouped_items[discipline][cost_code_id] = {
                'cost_code': item.cost_code,
                'items': [],
                'total_budgeted_quantity': 0,
                'total_earned_quantity': 0
            }
        
        # Add work item to group
        grouped_items[discipline][cost_code_id]['items'].append(item)
        
        # Update totals
        budgeted_quantity = item.budgeted_quantity or 0
        earned_quantity = item.earned_quantity or 0
        
        grouped_items[discipline][cost_code_id]['total_budgeted_quantity'] += budgeted_quantity
        grouped_items[discipline][cost_code_id]['total_earned_quantity'] += earned_quantity
        
        discipline_totals[discipline]['total_budgeted_quantity'] += budgeted_quantity
        discipline_totals[discipline]['total_earned_quantity'] += earned_quantity
        
        total_budgeted_quantity += budgeted_quantity
        total_earned_quantity += earned_quantity
    
    # Calculate overall progress
    overall_progress = 0
    if total_budgeted_quantity > 0:
        overall_progress = (total_earned_quantity / total_budgeted_quantity) * 100
    
    # Render HTML template
    html_content = render_template(
        'quantities_report_template.html',
        report_title=report_title,
        report_subtitle=report_subtitle,
        grouped_items=grouped_items,
        discipline_totals=discipline_totals,
        total_budgeted_quantity=total_budgeted_quantity,
        total_earned_quantity=total_earned_quantity,
        overall_progress=overall_progress,
        page_number=1,
        current_date=datetime.datetime.now().strftime("%Y-%m-%d")
    )
    
    # Generate PDF
    pdf = HTML(string=html_content, base_url=os.path.dirname(os.path.abspath(__file__)))
    return pdf.write_pdf()
