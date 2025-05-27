import os
import io
import datetime
from fpdf import FPDF

class QuantitiesPDF(FPDF):
    def __init__(self):
        # Initialize with landscape orientation ('L')
        super().__init__(orientation='L')
        
    def header(self):
        # Logo - Use Fortis logo instead of Magellan
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'images', 'Fortis.png')
        if os.path.exists(logo_path):
            # Adjust logo position for landscape orientation
            self.image(logo_path, 10, 8, 40)
        
        # Set up header section with 3 rows as specified
        # Top row: "Quantity Report"
        self.set_font('Arial', 'B', 16)
        self.set_xy(120, 8)
        self.cell(60, 8, 'Quantity Report', 0, 1, 'C')
        
        # Middle row: "Progress Detail"
        self.set_xy(120, 16)
        self.cell(60, 8, 'Progress Detail', 0, 1, 'C')
        
        # Bottom row: Project name (without project ID)
        if hasattr(self, 'project_name'):
            self.set_font('Arial', '', 12)
            self.set_xy(120, 24)
            self.cell(60, 8, self.project_name, 0, 1, 'C')
        
        # Page info on the right
        self.set_font('Arial', '', 9)
        self.set_xy(250, 8)
        self.cell(30, 5, f'Page: {self.page_no()}', 0, 1, 'R')
        
        # Progress info
        if hasattr(self, 'overall_progress'):
            self.set_xy(250, 13)
            self.cell(30, 5, f'Progress: {self.overall_progress:.1f}%', 0, 1, 'R')
        
        # Date info
        self.set_xy(250, 18)
        self.cell(30, 5, f'Date: {datetime.datetime.now().strftime("%Y-%m-%d")}', 0, 1, 'R')
        
        # Line break after header
        self.ln(25)
        self.line(10, 35, 287, 35)
        
        # Add sub job information if available
        if hasattr(self, 'sub_job_name') and hasattr(self, 'sub_job_description'):
            self.set_font('Arial', 'B', 10)
            self.set_xy(10, 38)
            self.cell(100, 5, f'Sub Job: {self.sub_job_name}', 0, 0, 'L')
            
            if self.sub_job_description:
                self.set_xy(120, 38)
                self.cell(167, 5, f'Description: {self.sub_job_description}', 0, 0, 'L')
            
            self.ln(8)
        else:
            self.ln(5)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Page number
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        # Arial 12
        self.set_font('Arial', 'B', 12)
        # Background color
        self.set_fill_color(200, 200, 200)
        # Title
        self.cell(0, 6, title, 0, 1, 'L', 1)
        # Line break
        self.ln(4)

    def table_header(self):
        # Colors, line width and bold font
        self.set_fill_color(240, 240, 240)
        self.set_text_color(0, 0, 0)
        self.set_font('Arial', 'B', 9)
        self.set_line_width(0.3)
        
        # Adjust column widths for landscape orientation
        col_widths = [25, 60, 15, 25, 25, 20, 15, 15, 15, 15, 15, 15, 15]
        
        # Calculate total table width
        self.table_width = sum(col_widths)
        
        # Header row 1
        self.cell(col_widths[0], 7, 'Work Item', 1, 0, 'C', 1)
        self.cell(col_widths[1], 7, 'Description', 1, 0, 'C', 1)
        self.cell(col_widths[2], 7, 'UOM', 1, 0, 'C', 1)
        
        # Use multi-line cells for header text that needs wrapping
        current_x = self.get_x()
        current_y = self.get_y()
        self.multi_cell(col_widths[3], 3.5, 'Budgeted Quantity', 1, 'C', 1)
        self.set_xy(current_x + col_widths[3], current_y)
        
        current_x = self.get_x()
        current_y = self.get_y()
        self.multi_cell(col_widths[4], 3.5, 'Earned Quantity', 1, 'C', 1)
        self.set_xy(current_x + col_widths[4], current_y)
        
        self.cell(col_widths[5], 7, '% Complete', 1, 0, 'C', 1)
        
        # Rules of Credit header (spans 7 columns)
        rules_width = sum(col_widths[6:])
        self.cell(rules_width, 7, 'Rules of Credit', 1, 1, 'C', 1)
        
        # No space between header and table content
        self.set_xy(10, self.get_y())

    def discipline_row(self, discipline):
        # Set font
        self.set_font('Arial', 'B', 9)
        # Background color
        self.set_fill_color(220, 220, 220)
        # Discipline row - use exact table width to prevent overhang
        self.cell(self.table_width, 6, discipline, 1, 1, 'L', 1)

    def cost_code_row(self, cost_code, steps):
        # Set font
        self.set_font('Arial', '', 9)
        # Background color
        self.set_fill_color(240, 240, 240)
        
        # Adjust column widths for landscape orientation
        col_widths = [25, 60, 15, 25, 25, 20, 15, 15, 15, 15, 15, 15, 15]
        cost_code_text = f"{cost_code.cost_code_id_str} - {cost_code.description}"
        
        # Cost code cell (spans first 6 columns)
        cost_code_width = sum(col_widths[:6])
        self.cell(cost_code_width, 6, cost_code_text, 1, 0, 'L', 1)
        
        # Rules of Credit step names
        self.set_font('Arial', '', 7)
        steps_list = cost_code.rule_of_credit.get_steps() if cost_code.rule_of_credit else []
        
        # Add up to 7 step names
        for i in range(7):
            if i < len(steps_list):
                self.cell(col_widths[i+6], 6, steps_list[i]['name'], 1, 0, 'C', 1)
            else:
                self.cell(col_widths[i+6], 6, '', 1, 0, 'C', 1)
        
        self.ln()

    def work_item_row(self, item):
        # Set font
        self.set_font('Arial', '', 9)
        
        # Calculate progress
        progress = 0
        if item.budgeted_quantity and item.budgeted_quantity > 0:
            progress = (item.earned_quantity or 0) / item.budgeted_quantity * 100
        
        # Adjust column widths for landscape orientation
        col_widths = [25, 60, 15, 25, 25, 20, 15, 15, 15, 15, 15, 15, 15]
        
        # Handle text wrapping for description - ensure no text bleeds over cell lines
        description = item.description
        if len(description) > 50:  # Increased character limit for landscape
            # Calculate how many lines we need
            lines = len(description) // 50 + (1 if len(description) % 50 > 0 else 0)
            row_height = 6 * lines  # Adjust row height based on number of lines
        else:
            row_height = 6
        
        # Work item cells
        self.cell(col_widths[0], row_height, str(item.work_item_id_str), 1, 0, 'L')
        
        # Multi-line cell for description
        current_x = self.get_x()
        current_y = self.get_y()
        self.multi_cell(col_widths[1], row_height / (1 if len(description) <= 50 else lines), description, 1, 'L')
        self.set_xy(current_x + col_widths[1], current_y)
        
        self.cell(col_widths[2], row_height, item.unit_of_measure or '', 1, 0, 'C')
        self.cell(col_widths[3], row_height, f"{item.budgeted_quantity or 0:.2f}", 1, 0, 'R')
        self.cell(col_widths[4], row_height, f"{item.earned_quantity or 0:.2f}", 1, 0, 'R')
        self.cell(col_widths[5], row_height, f"{progress:.1f}%", 1, 0, 'R')
        
        # Rules of Credit progress steps
        self.set_font('Arial', '', 7)
        progress_data = item.get_steps_progress()
        
        # Get the rule of credit steps
        steps = []
        if item.cost_code and item.cost_code.rule_of_credit:
            steps = item.cost_code.rule_of_credit.get_steps()
        
        for i in range(7):
            if i < len(steps):
                step_name = steps[i]['name']
                progress_value = progress_data.get(step_name, 0)
                self.cell(col_widths[i+6], row_height, f"{progress_value:.0f}%", 1, 0, 'C')
            else:
                self.cell(col_widths[i+6], row_height, '', 1, 0, 'C')
        
        self.ln()

    def total_row(self, title, budgeted, earned, is_grand_total=False):
        # Set font
        self.set_font('Arial', 'B', 9)
        # Background color
        if is_grand_total:
            self.set_fill_color(200, 200, 200)
        else:
            self.set_fill_color(240, 240, 240)
        
        # Calculate progress
        progress = 0
        if budgeted > 0:
            progress = (earned / budgeted) * 100
        
        # Adjust column widths for landscape orientation
        col_widths = [25, 60, 15, 25, 25, 20, 15, 15, 15, 15, 15, 15, 15]
        
        # Title spans first 3 columns
        title_width = sum(col_widths[:3])
        self.cell(title_width, 6, title, 1, 0, 'L', 1)
        
        # Values
        self.cell(col_widths[3], 6, f"{budgeted:.2f}", 1, 0, 'R', 1)
        self.cell(col_widths[4], 6, f"{earned:.2f}", 1, 0, 'R', 1)
        self.cell(col_widths[5], 6, f"{progress:.1f}%", 1, 0, 'R', 1)
        
        # Empty cells for Rules of Credit - use exact width to prevent overhang
        rules_width = sum(col_widths[6:])
        self.cell(rules_width, 6, '', 1, 1, 'C', 1)


class HoursPDF(FPDF):
    def __init__(self):
        # Initialize with landscape orientation ('L')
        super().__init__(orientation='L')
        
    def header(self):
        # Logo - Use Fortis logo instead of Magellan
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'images', 'Fortis.png')
        if os.path.exists(logo_path):
            # Adjust logo position for landscape orientation
            self.image(logo_path, 10, 8, 40)
        
        # Set up header section with 3 rows as specified
        # Top row: "Hours Report"
        self.set_font('Arial', 'B', 16)
        self.set_xy(120, 8)
        self.cell(60, 8, 'Hours Report', 0, 1, 'C')
        
        # Middle row: "Progress Detail"
        self.set_xy(120, 16)
        self.cell(60, 8, 'Progress Detail', 0, 1, 'C')
        
        # Bottom row: Project name (without project ID)
        if hasattr(self, 'project_name'):
            self.set_font('Arial', '', 12)
            self.set_xy(120, 24)
            self.cell(60, 8, self.project_name, 0, 1, 'C')
        
        # Page info on the right
        self.set_font('Arial', '', 9)
        self.set_xy(250, 8)
        self.cell(30, 5, f'Page: {self.page_no()}', 0, 1, 'R')
        
        # Progress info
        if hasattr(self, 'overall_progress'):
            self.set_xy(250, 13)
            self.cell(30, 5, f'Progress: {self.overall_progress:.1f}%', 0, 1, 'R')
        
        # Date info
        self.set_xy(250, 18)
        self.cell(30, 5, f'Date: {datetime.datetime.now().strftime("%Y-%m-%d")}', 0, 1, 'R')
        
        # Line break after header
        self.ln(25)
        self.line(10, 35, 287, 35)
        
        # Add sub job information if available
        if hasattr(self, 'sub_job_name') and hasattr(self, 'sub_job_description'):
            self.set_font('Arial', 'B', 10)
            self.set_xy(10, 38)
            self.cell(100, 5, f'Sub Job: {self.sub_job_name}', 0, 0, 'L')
            
            if self.sub_job_description:
                self.set_xy(120, 38)
                self.cell(167, 5, f'Description: {self.sub_job_description}', 0, 0, 'L')
            
            self.ln(8)
        else:
            self.ln(5)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Page number
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        # Arial 12
        self.set_font('Arial', 'B', 12)
        # Background color
        self.set_fill_color(200, 200, 200)
        # Title
        self.cell(0, 6, title, 0, 1, 'L', 1)
        # Line break
        self.ln(4)

    def table_header(self):
        # Colors, line width and bold font
        self.set_fill_color(240, 240, 240)
        self.set_text_color(0, 0, 0)
        self.set_font('Arial', 'B', 9)
        self.set_line_width(0.3)
        
        # Adjust column widths for landscape orientation
        col_widths = [25, 60, 15, 25, 25, 20, 15, 15, 15, 15, 15, 15, 15]
        
        # Calculate total table width
        self.table_width = sum(col_widths)
        
        # Header row 1
        self.cell(col_widths[0], 7, 'Work Item', 1, 0, 'C', 1)
        self.cell(col_widths[1], 7, 'Description', 1, 0, 'C', 1)
        self.cell(col_widths[2], 7, 'UOM', 1, 0, 'C', 1)
        
        # Use multi-line cells for header text that needs wrapping
        current_x = self.get_x()
        current_y = self.get_y()
        self.multi_cell(col_widths[3], 3.5, 'Budgeted Hours', 1, 'C', 1)
        self.set_xy(current_x + col_widths[3], current_y)
        
        current_x = self.get_x()
        current_y = self.get_y()
        self.multi_cell(col_widths[4], 3.5, 'Earned Hours', 1, 'C', 1)
        self.set_xy(current_x + col_widths[4], current_y)
        
        self.cell(col_widths[5], 7, '% Complete', 1, 0, 'C', 1)
        
        # Rules of Credit header (spans 7 columns)
        rules_width = sum(col_widths[6:])
        self.cell(rules_width, 7, 'Rules of Credit', 1, 1, 'C', 1)
        
        # No space between header and table content
        self.set_xy(10, self.get_y())

    def discipline_row(self, discipline):
        # Set font
        self.set_font('Arial', 'B', 9)
        # Background color
        self.set_fill_color(220, 220, 220)
        # Discipline row - use exact table width to prevent overhang
        self.cell(self.table_width, 6, discipline, 1, 1, 'L', 1)

    def cost_code_row(self, cost_code, steps):
        # Set font
        self.set_font('Arial', '', 9)
        # Background color
        self.set_fill_color(240, 240, 240)
        
        # Adjust column widths for landscape orientation
        col_widths = [25, 60, 15, 25, 25, 20, 15, 15, 15, 15, 15, 15, 15]
        cost_code_text = f"{cost_code.cost_code_id_str} - {cost_code.description}"
        
        # Cost code cell (spans first 6 columns)
        cost_code_width = sum(col_widths[:6])
        self.cell(cost_code_width, 6, cost_code_text, 1, 0, 'L', 1)
        
        # Rules of Credit step names
        self.set_font('Arial', '', 7)
        steps_list = cost_code.rule_of_credit.get_steps() if cost_code.rule_of_credit else []
        
        # Add up to 7 step names
        for i in range(7):
            if i < len(steps_list):
                self.cell(col_widths[i+6], 6, steps_list[i]['name'], 1, 0, 'C', 1)
            else:
                self.cell(col_widths[i+6], 6, '', 1, 0, 'C', 1)
        
        self.ln()

    def work_item_row(self, item):
        # Set font
        self.set_font('Arial', '', 9)
        
        # Calculate progress
        progress = 0
        if item.budgeted_hours and item.budgeted_hours > 0:
            progress = (item.earned_hours or 0) / item.budgeted_hours * 100
        
        # Adjust column widths for landscape orientation
        col_widths = [25, 60, 15, 25, 25, 20, 15, 15, 15, 15, 15, 15, 15]
        
        # Handle text wrapping for description - ensure no text bleeds over cell lines
        description = item.description
        if len(description) > 50:  # Increased character limit for landscape
            # Calculate how many lines we need
            lines = len(description) // 50 + (1 if len(description) % 50 > 0 else 0)
            row_height = 6 * lines  # Adjust row height based on number of lines
        else:
            row_height = 6
        
        # Work item cells
        self.cell(col_widths[0], row_height, str(item.work_item_id_str), 1, 0, 'L')
        
        # Multi-line cell for description
        current_x = self.get_x()
        current_y = self.get_y()
        self.multi_cell(col_widths[1], row_height / (1 if len(description) <= 50 else lines), description, 1, 'L')
        self.set_xy(current_x + col_widths[1], current_y)
        
        self.cell(col_widths[2], row_height, item.unit_of_measure or '', 1, 0, 'C')
        self.cell(col_widths[3], row_height, f"{item.budgeted_hours or 0:.2f}", 1, 0, 'R')
        self.cell(col_widths[4], row_height, f"{item.earned_hours or 0:.2f}", 1, 0, 'R')
        self.cell(col_widths[5], row_height, f"{progress:.1f}%", 1, 0, 'R')
        
        # Rules of Credit progress steps
        self.set_font('Arial', '', 7)
        progress_data = item.get_steps_progress()
        
        # Get the rule of credit steps
        steps = []
        if item.cost_code and item.cost_code.rule_of_credit:
            steps = item.cost_code.rule_of_credit.get_steps()
        
        for i in range(7):
            if i < len(steps):
                step_name = steps[i]['name']
                progress_value = progress_data.get(step_name, 0)
                self.cell(col_widths[i+6], row_height, f"{progress_value:.0f}%", 1, 0, 'C')
            else:
                self.cell(col_widths[i+6], row_height, '', 1, 0, 'C')
        
        self.ln()

    def total_row(self, title, budgeted, earned, is_grand_total=False):
        # Set font
        self.set_font('Arial', 'B', 9)
        # Background color
        if is_grand_total:
            self.set_fill_color(200, 200, 200)
        else:
            self.set_fill_color(240, 240, 240)
        
        # Calculate progress
        progress = 0
        if budgeted > 0:
            progress = (earned / budgeted) * 100
        
        # Adjust column widths for landscape orientation
        col_widths = [25, 60, 15, 25, 25, 20, 15, 15, 15, 15, 15, 15, 15]
        
        # Title spans first 3 columns
        title_width = sum(col_widths[:3])
        self.cell(title_width, 6, title, 1, 0, 'L', 1)
        
        # Values
        self.cell(col_widths[3], 6, f"{budgeted:.2f}", 1, 0, 'R', 1)
        self.cell(col_widths[4], 6, f"{earned:.2f}", 1, 0, 'R', 1)
        self.cell(col_widths[5], 6, f"{progress:.1f}%", 1, 0, 'R', 1)
        
        # Empty cells for Rules of Credit - use exact width to prevent overhang
        rules_width = sum(col_widths[6:])
        self.cell(rules_width, 6, '', 1, 1, 'C', 1)


def generate_quantities_report_pdf(project_id=None, sub_job_id=None):
    """
    Generate a PDF report for quantities data using FPDF2
    
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
        # Store project and sub job information separately
        project_name = project.name
        sub_job_name = sub_job.name
        sub_job_description = sub_job.description
    elif project_id:
        project = Project.query.get_or_404(project_id)
        work_items = WorkItem.query.filter_by(project_id=project_id).all()
        # Store project information
        project_name = project.name
        sub_job_name = None
        sub_job_description = None
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
    
    # Create PDF
    pdf = QuantitiesPDF()
    pdf.project_name = project_name
    pdf.overall_progress = overall_progress
    
    # Add sub job information if available
    if sub_job_name:
        pdf.sub_job_name = sub_job_name
        pdf.sub_job_description = sub_job_description
    
    # Set up the PDF
    pdf.set_auto_page_break(True, margin=15)
    pdf.add_page()
    
    # Add table header
    pdf.table_header()
    
    # Add data rows
    for discipline, cost_codes in grouped_items.items():
        # Discipline header
        pdf.discipline_row(discipline)
        
        for cost_code_id, data in cost_codes.items():
            # Cost code row with Rules of Credit steps
            pdf.cost_code_row(data['cost_code'], data['cost_code'].rule_of_credit.get_steps() if data['cost_code'].rule_of_credit else [])
            
            # Work items
            for item in data['items']:
                pdf.work_item_row(item)
            
            # Cost code total
            pdf.total_row(
                'Cost Code Total',
                data['total_budgeted_quantity'],
                data['total_earned_quantity']
            )
        
        # Discipline total
        pdf.total_row(
            'Discipline Total',
            discipline_totals[discipline]['total_budgeted_quantity'],
            discipline_totals[discipline]['total_earned_quantity']
        )
    
    # Grand total
    pdf.total_row(
        'Grand Total',
        total_budgeted_quantity,
        total_earned_quantity,
        is_grand_total=True
    )
    
    # Create a BytesIO object to store the PDF data
    pdf_buffer = io.BytesIO()
    
    # Output PDF to the BytesIO buffer
    pdf.output(pdf_buffer)
    
    # Reset buffer position to the beginning
    pdf_buffer.seek(0)
    
    # Return the BytesIO object containing the PDF data
    return pdf_buffer.getvalue()


def generate_hours_report_pdf(project_id=None, sub_job_id=None):
    """
    Generate a PDF report for hours data using FPDF2
    
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
        # Store project and sub job information separately
        project_name = project.name
        sub_job_name = sub_job.name
        sub_job_description = sub_job.description
    elif project_id:
        project = Project.query.get_or_404(project_id)
        work_items = WorkItem.query.filter_by(project_id=project_id).all()
        # Store project information
        project_name = project.name
        sub_job_name = None
        sub_job_description = None
    else:
        raise ValueError("Either project_id or sub_job_id must be provided")
    
    # Group work items by discipline and cost code
    grouped_items = {}
    discipline_totals = {}
    total_budgeted_hours = 0
    total_earned_hours = 0
    
    for item in work_items:
        if not item.cost_code:
            continue
            
        discipline = item.cost_code.discipline
        cost_code_id = item.cost_code_id
        
        # Initialize discipline if not exists
        if discipline not in grouped_items:
            grouped_items[discipline] = {}
            discipline_totals[discipline] = {
                'total_budgeted_hours': 0,
                'total_earned_hours': 0
            }
        
        # Initialize cost code if not exists
        if cost_code_id not in grouped_items[discipline]:
            grouped_items[discipline][cost_code_id] = {
                'cost_code': item.cost_code,
                'items': [],
                'total_budgeted_hours': 0,
                'total_earned_hours': 0
            }
        
        # Add work item to group
        grouped_items[discipline][cost_code_id]['items'].append(item)
        
        # Update totals
        budgeted_hours = item.budgeted_hours or 0
        earned_hours = item.earned_hours or 0
        
        grouped_items[discipline][cost_code_id]['total_budgeted_hours'] += budgeted_hours
        grouped_items[discipline][cost_code_id]['total_earned_hours'] += earned_hours
        
        discipline_totals[discipline]['total_budgeted_hours'] += budgeted_hours
        discipline_totals[discipline]['total_earned_hours'] += earned_hours
        
        total_budgeted_hours += budgeted_hours
        total_earned_hours += earned_hours
    
    # Calculate overall progress
    overall_progress = 0
    if total_budgeted_hours > 0:
        overall_progress = (total_earned_hours / total_budgeted_hours) * 100
    
    # Create PDF
    pdf = HoursPDF()
    pdf.project_name = project_name
    pdf.overall_progress = overall_progress
    
    # Add sub job information if available
    if sub_job_name:
        pdf.sub_job_name = sub_job_name
        pdf.sub_job_description = sub_job_description
    
    # Set up the PDF
    pdf.set_auto_page_break(True, margin=15)
    pdf.add_page()
    
    # Add table header
    pdf.table_header()
    
    # Add data rows
    for discipline, cost_codes in grouped_items.items():
        # Discipline header
        pdf.discipline_row(discipline)
        
        for cost_code_id, data in cost_codes.items():
            # Cost code row with Rules of Credit steps
            pdf.cost_code_row(data['cost_code'], data['cost_code'].rule_of_credit.get_steps() if data['cost_code'].rule_of_credit else [])
            
            # Work items
            for item in data['items']:
                pdf.work_item_row(item)
            
            # Cost code total
            pdf.total_row(
                'Cost Code Total',
                data['total_budgeted_hours'],
                data['total_earned_hours']
            )
        
        # Discipline total
        pdf.total_row(
            'Discipline Total',
            discipline_totals[discipline]['total_budgeted_hours'],
            discipline_totals[discipline]['total_earned_hours']
        )
    
    # Grand total
    pdf.total_row(
        'Grand Total',
        total_budgeted_hours,
        total_earned_hours,
        is_grand_total=True
    )
    
    # Create a BytesIO object to store the PDF data
    pdf_buffer = io.BytesIO()
    
    # Output PDF to the BytesIO buffer
    pdf.output(pdf_buffer)
    
    # Reset buffer position to the beginning
    pdf_buffer.seek(0)
    
    # Return the BytesIO object containing the PDF data
    return pdf_buffer.getvalue()
