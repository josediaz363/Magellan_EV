import os
import base64
import datetime
from flask import render_template, send_file
from weasyprint import HTML, CSS
from io import BytesIO
from models import Project, SubJob, WorkItem, CostCode, RuleOfCredit

def encode_logo_to_base64():
    """Encode the logo image to base64 for embedding in HTML"""
    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                            'static', 'images', 'magellan_logo_white.png')
    
    if not os.path.exists(logo_path):
        # Return empty string if logo doesn't exist
        return ""
    
    with open(logo_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    
    return encoded_string

def prepare_report_data(project_id, sub_job_id=None, report_type='hours'):
    """Prepare data for reports"""
    project = Project.query.get_or_404(project_id)
    sub_job = None if sub_job_id is None else SubJob.query.get_or_404(sub_job_id)
    
    # Get work items
    if sub_job_id:
        work_items = WorkItem.query.filter_by(sub_job_id=sub_job_id).all()
    else:
        work_items = WorkItem.query.filter_by(project_id=project_id).all()
    
    # Group work items by discipline and cost code
    grouped_data = group_work_items_by_discipline_and_cost_code(work_items)
    
    # Calculate subtotals
    project_totals = calculate_project_totals(grouped_data, report_type)
    
    # Current date for report
    report_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Encode logo
    logo_base64 = encode_logo_to_base64()
    
    return {
        'project': project,
        'sub_job': sub_job,
        'grouped_work_items': grouped_data,
        'project_totals': project_totals,
        'report_date': report_date,
        'logo_base64': logo_base64
    }

def group_work_items_by_discipline_and_cost_code(work_items):
    """Group work items by discipline and cost code for hierarchical display"""
    grouped_data = {}
    
    for work_item in work_items:
        # Skip if cost code doesn't exist
        if not work_item.cost_code:
            continue
        
        discipline = work_item.cost_code.discipline
        cost_code_id_str = work_item.cost_code.cost_code_id_str
        
        # Initialize discipline if not exists
        if discipline not in grouped_data:
            grouped_data[discipline] = {
                'cost_codes': {},
                'subtotals': {
                    'budgeted_hours': 0,
                    'earned_hours': 0,
                    'budgeted_quantity': 0,
                    'earned_quantity': 0,
                    'percent_complete_hours': 0,
                    'percent_complete_quantity': 0
                }
            }
        
        # Initialize cost code if not exists
        if cost_code_id_str not in grouped_data[discipline]['cost_codes']:
            # Get rule of credit steps if available
            roc_step_headers = []
            if work_item.cost_code.rule_of_credit:
                rule = work_item.cost_code.rule_of_credit
                steps = rule.get_steps()
                roc_step_headers = [step['name'] for step in steps]
                
                # Ensure we have exactly 7 columns for ROC steps
                if len(roc_step_headers) < 7:
                    roc_step_headers.extend([''] * (7 - len(roc_step_headers)))
                elif len(roc_step_headers) > 7:
                    roc_step_headers = roc_step_headers[:7]
            else:
                # If no rule of credit, add empty headers
                roc_step_headers = [''] * 7
            
            grouped_data[discipline]['cost_codes'][cost_code_id_str] = {
                'work_items': [],
                'roc_step_headers': roc_step_headers,
                'subtotals': {
                    'budgeted_hours': 0,
                    'earned_hours': 0,
                    'budgeted_quantity': 0,
                    'earned_quantity': 0,
                    'percent_complete_hours': 0,
                    'percent_complete_quantity': 0
                }
            }
        
        # Add work item to the group
        # Process ROC steps progress
        roc_steps_progress = {}
        progress_data = work_item.get_steps_progress()
        for step_name, percentage in progress_data.items():
            roc_steps_progress[step_name] = percentage
        
        # Add processed work item
        work_item_data = {
            'id': work_item.id,
            'work_item_id_str': work_item.work_item_id_str,
            'description': work_item.description,
            'budgeted_man_hours': work_item.budgeted_man_hours or 0,
            'earned_man_hours': work_item.earned_man_hours or 0,
            'budgeted_quantity': work_item.budgeted_quantity or 0,
            'earned_quantity': work_item.earned_quantity or 0,
            'unit_of_measure': work_item.unit_of_measure or '',
            'percent_complete_hours': work_item.percent_complete_hours or 0,
            'percent_complete_quantity': work_item.percent_complete_quantity or 0,
            'roc_steps_progress': roc_steps_progress
        }
        
        grouped_data[discipline]['cost_codes'][cost_code_id_str]['work_items'].append(work_item_data)
        
        # Update cost code subtotals
        cc_subtotals = grouped_data[discipline]['cost_codes'][cost_code_id_str]['subtotals']
        cc_subtotals['budgeted_hours'] += work_item.budgeted_man_hours or 0
        cc_subtotals['earned_hours'] += work_item.earned_man_hours or 0
        cc_subtotals['budgeted_quantity'] += work_item.budgeted_quantity or 0
        cc_subtotals['earned_quantity'] += work_item.earned_quantity or 0
        
        # Update discipline subtotals
        disc_subtotals = grouped_data[discipline]['subtotals']
        disc_subtotals['budgeted_hours'] += work_item.budgeted_man_hours or 0
        disc_subtotals['earned_hours'] += work_item.earned_man_hours or 0
        disc_subtotals['budgeted_quantity'] += work_item.budgeted_quantity or 0
        disc_subtotals['earned_quantity'] += work_item.earned_quantity or 0
    
    # Calculate percentages for subtotals
    for discipline, discipline_data in grouped_data.items():
        disc_subtotals = discipline_data['subtotals']
        if disc_subtotals['budgeted_hours'] > 0:
            disc_subtotals['percent_complete_hours'] = (disc_subtotals['earned_hours'] / disc_subtotals['budgeted_hours']) * 100
        if disc_subtotals['budgeted_quantity'] > 0:
            disc_subtotals['percent_complete_quantity'] = (disc_subtotals['earned_quantity'] / disc_subtotals['budgeted_quantity']) * 100
        
        for cost_code, cost_code_data in discipline_data['cost_codes'].items():
            cc_subtotals = cost_code_data['subtotals']
            if cc_subtotals['budgeted_hours'] > 0:
                cc_subtotals['percent_complete_hours'] = (cc_subtotals['earned_hours'] / cc_subtotals['budgeted_hours']) * 100
            if cc_subtotals['budgeted_quantity'] > 0:
                cc_subtotals['percent_complete_quantity'] = (cc_subtotals['earned_quantity'] / cc_subtotals['budgeted_quantity']) * 100
    
    return grouped_data

def calculate_project_totals(grouped_data, report_type):
    """Calculate project totals from grouped data"""
    totals = {
        'budgeted_hours': 0,
        'earned_hours': 0,
        'budgeted_quantity': 0,
        'earned_quantity': 0,
        'percent_complete_hours': 0,
        'percent_complete_quantity': 0
    }
    
    for discipline, discipline_data in grouped_data.items():
        disc_subtotals = discipline_data['subtotals']
        totals['budgeted_hours'] += disc_subtotals['budgeted_hours']
        totals['earned_hours'] += disc_subtotals['earned_hours']
        totals['budgeted_quantity'] += disc_subtotals['budgeted_quantity']
        totals['earned_quantity'] += disc_subtotals['earned_quantity']
    
    # Calculate percentages
    if totals['budgeted_hours'] > 0:
        totals['percent_complete_hours'] = (totals['earned_hours'] / totals['budgeted_hours']) * 100
    if totals['budgeted_quantity'] > 0:
        totals['percent_complete_quantity'] = (totals['earned_quantity'] / totals['budgeted_quantity']) * 100
    
    return totals

def generate_pdf_report(data, template_path, output_path=None):
    """Generate PDF from template and data"""
    # Render HTML template with data
    html_content = render_template(template_path, **data)
    
    # Create PDF using WeasyPrint
    html = HTML(string=html_content)
    
    if output_path:
        # Save to file if output path is provided
        html.write_pdf(output_path)
        return output_path
    else:
        # Return PDF as BytesIO if no output path
        pdf_file = BytesIO()
        html.write_pdf(pdf_file)
        pdf_file.seek(0)
        return pdf_file

def generate_hours_report_pdf(project_id, sub_job_id=None, output_path=None):
    """Generate hours report PDF"""
    data = prepare_report_data(project_id, sub_job_id, 'hours')
    return generate_pdf_report(data, 'hours_report_template.html', output_path)

def generate_quantities_report_pdf(project_id, sub_job_id=None, output_path=None):
    """Generate quantities report PDF"""
    data = prepare_report_data(project_id, sub_job_id, 'quantities')
    return generate_pdf_report(data, 'quantities_report_template.html', output_path)
