import os
import io
from fpdf import FPDF
from datetime import datetime

def generate_quantities_report_pdf(project_id, sub_job_id=None):
    """
    Generate a PDF report for quantities by project or sub job
    
    Args:
        project_id (int): Project ID
        sub_job_id (int, optional): Sub Job ID. If provided, report will be filtered by sub job.
        
    Returns:
        BytesIO: PDF file as a BytesIO object
    """
    from models import Project, SubJob, WorkItem
    
    # Get project and optional sub job
    project = Project.query.get_or_404(project_id)
    sub_job = None
    if sub_job_id:
        sub_job = SubJob.query.get_or_404(sub_job_id)
    
    # Create PDF object
    pdf = FPDF()
    pdf.add_page()
    
    # Set up fonts
    pdf.set_font('Arial', 'B', 16)
    
    # Header
    pdf.cell(0, 10, 'Magellan EV Tracker', 0, 1, 'C')
    pdf.set_font('Arial', 'B', 14)
    
    if sub_job:
        pdf.cell(0, 10, f'Quantities Report - {project.name} - {sub_job.name}', 0, 1, 'C')
    else:
        pdf.cell(0, 10, f'Quantities Report - {project.name}', 0, 1, 'C')
    
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'R')
    
    # Project details
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Project Details:', 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(40, 6, 'Project ID:', 0, 0)
    pdf.cell(0, 6, project.project_id_str, 0, 1)
    pdf.cell(40, 6, 'Project Name:', 0, 0)
    pdf.cell(0, 6, project.name, 0, 1)
    
    if sub_job:
        pdf.cell(40, 6, 'Sub Job ID:', 0, 0)
        pdf.cell(0, 6, sub_job.sub_job_id_str, 0, 1)
        pdf.cell(40, 6, 'Sub Job Name:', 0, 0)
        pdf.cell(0, 6, sub_job.name, 0, 1)
    
    # Work Items Table
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Work Items:', 0, 1)
    
    # Table header
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(25, 7, 'ID', 1, 0, 'C')
    pdf.cell(60, 7, 'Description', 1, 0, 'C')
    pdf.cell(20, 7, 'UOM', 1, 0, 'C')
    pdf.cell(25, 7, 'Budgeted', 1, 0, 'C')
    pdf.cell(25, 7, 'Earned', 1, 0, 'C')
    pdf.cell(25, 7, '% Complete', 1, 1, 'C')
    
    # Table data
    pdf.set_font('Arial', '', 10)
    
    if sub_job:
        work_items = WorkItem.query.filter_by(project_id=project_id, sub_job_id=sub_job_id).all()
    else:
        work_items = WorkItem.query.filter_by(project_id=project_id).all()
    
    for item in work_items:
        # Calculate percent complete
        if item.budgeted_quantity and item.budgeted_quantity > 0:
            percent_complete = (item.earned_quantity / item.budgeted_quantity) * 100
        else:
            percent_complete = 0
        
        # Add row to table
        pdf.cell(25, 6, item.work_item_id_str, 1, 0)
        pdf.cell(60, 6, item.description[:30], 1, 0)  # Truncate long descriptions
        pdf.cell(20, 6, item.unit_of_measure or '', 1, 0, 'C')
        pdf.cell(25, 6, f"{item.budgeted_quantity:.2f}", 1, 0, 'R')
        pdf.cell(25, 6, f"{item.earned_quantity:.2f}", 1, 0, 'R')
        pdf.cell(25, 6, f"{percent_complete:.1f}%", 1, 1, 'R')
    
    # Summary
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Summary:', 0, 1)
    pdf.set_font('Arial', '', 10)
    
    # Calculate totals
    total_budgeted = sum(item.budgeted_quantity or 0 for item in work_items)
    total_earned = sum(item.earned_quantity or 0 for item in work_items)
    overall_percent = (total_earned / total_budgeted * 100) if total_budgeted > 0 else 0
    
    pdf.cell(40, 6, 'Total Budgeted Quantity:', 0, 0)
    pdf.cell(0, 6, f"{total_budgeted:.2f}", 0, 1)
    pdf.cell(40, 6, 'Total Earned Quantity:', 0, 0)
    pdf.cell(0, 6, f"{total_earned:.2f}", 0, 1)
    pdf.cell(40, 6, 'Overall Percent Complete:', 0, 0)
    pdf.cell(0, 6, f"{overall_percent:.1f}%", 0, 1)
    
    # Create a BytesIO object to store the PDF
    pdf_buffer = io.BytesIO()
    
    # Save the PDF to the BytesIO object
    pdf_data = pdf.output(dest='S').encode('latin1')  # Get PDF as bytes
    pdf_buffer.write(pdf_data)  # Write bytes to buffer
    pdf_buffer.seek(0)  # Reset buffer position to the beginning
    
    return pdf_buffer
