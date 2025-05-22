import os
import io
import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfgen import canvas
from reportlab.platypus.flowables import Flowable
from flask import current_app

def generate_quantities_report_pdf(project_id=None, sub_job_id=None):
    """
    Generate a PDF report for quantities data using ReportLab
    
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
        report_title = "Progress Detail"
        report_subtitle = f"{project.project_id_str} - {project.name} - {sub_job.name}"
    elif project_id:
        project = Project.query.get_or_404(project_id)
        work_items = WorkItem.query.filter_by(project_id=project_id).all()
        report_title = "Progress Detail"
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
    
    # Create PDF buffer
    buffer = io.BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontSize=16,
        alignment=1,  # Center alignment
        spaceAfter=0
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        alignment=1,  # Center alignment
        spaceAfter=12
    )
    normal_style = styles['Normal']
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Normal'],
        fontSize=9,
        alignment=2,  # Right alignment
    )
    discipline_style = ParagraphStyle(
        'Discipline',
        parent=styles['Normal'],
        fontSize=9,
        backColor=colors.lightgrey,
        fontName='Helvetica-Bold'
    )
    cost_code_style = ParagraphStyle(
        'CostCode',
        parent=styles['Normal'],
        fontSize=9,
        backColor=colors.whitesmoke,
    )
    rules_style = ParagraphStyle(
        'Rules',
        parent=styles['Normal'],
        fontSize=7,
        alignment=1,  # Center alignment
    )
    
    # Elements to add to PDF
    elements = []
    
    # Custom header with logo, title, and page info
    class HeaderCanvas(canvas.Canvas):
        def __init__(self, *args, **kwargs):
            canvas.Canvas.__init__(self, *args, **kwargs)
            self.pages = []
            
        def showPage(self):
            self.pages.append(dict(self.__dict__))
            self._startPage()
            
        def save(self):
            page_count = len(self.pages)
            for page in self.pages:
                self.__dict__.update(page)
                self.draw_header(page_count)
                canvas.Canvas.showPage(self)
            canvas.Canvas.save(self)
            
        def draw_header(self, page_count):
            # Logo
            logo_path = os.path.join(current_app.root_path, 'static', 'images', 'magellan_logo_white.png')
            if os.path.exists(logo_path):
                self.drawImage(logo_path, 0.5*inch, 10*inch, width=1*inch, preserveAspectRatio=True)
            
            # Title and subtitle
            self.setFont('Helvetica-Bold', 16)
            self.drawCentredString(4.25*inch, 10.5*inch, report_title)
            self.setFont('Helvetica', 12)
            self.drawCentredString(4.25*inch, 10.2*inch, report_subtitle)
            
            # Page info
            self.setFont('Helvetica', 9)
            page_text = f"Page: {self._pageNumber}"
            progress_text = f"Progress: {overall_progress:.1f}%"
            date_text = f"Date: {datetime.datetime.now().strftime('%Y-%m-%d')}"
            
            # Right-align the text
            self.drawRightString(8*inch, 10.5*inch, page_text)
            self.drawRightString(8*inch, 10.3*inch, progress_text)
            self.drawRightString(8*inch, 10.1*inch, date_text)
            
            # Bottom border
            self.line(0.5*inch, 10*inch, 8*inch, 10*inch)
    
    # Table data
    table_data = []
    
    # Table header
    header_row = [
        Paragraph('<b>Work Item</b>', normal_style),
        Paragraph('<b>Description</b>', normal_style),
        Paragraph('<b>UOM</b>', normal_style),
        Paragraph('<b>Budgeted Quantity</b>', normal_style),
        Paragraph('<b>Earned Quantity</b>', normal_style),
        Paragraph('<b>% Complete</b>', normal_style),
    ]
    
    # Add Rules of Credit header
    for i in range(7):
        header_row.append(Paragraph('<b>Rules of Credit</b>', normal_style) if i == 3 else Paragraph('', normal_style))
    
    table_data.append(header_row)
    
    # Table style
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('SPAN', (6, 0), (12, 0)),  # Span Rules of Credit header
        ('ALIGN', (6, 0), (12, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (3, 1), (5, -1), 'RIGHT'),  # Right-align numeric columns
    ]
    
    row_index = 1
    
    # Add data rows
    for discipline, cost_codes in grouped_items.items():
        # Discipline header
        discipline_row = [Paragraph(discipline, discipline_style)]
        discipline_row.extend([Paragraph('', discipline_style) for _ in range(12)])
        table_data.append(discipline_row)
        table_style.append(('SPAN', (0, row_index), (12, row_index)))
        table_style.append(('BACKGROUND', (0, row_index), (12, row_index), colors.lightgrey))
        row_index += 1
        
        for cost_code_id, data in cost_codes.items():
            # Cost code header
            cost_code_text = f"{data['cost_code'].code} - {data['cost_code'].description}"
            cost_code_row = [Paragraph(cost_code_text, cost_code_style)]
            cost_code_row.extend([Paragraph('', cost_code_style) for _ in range(5)])
            
            # Add Rules of Credit steps
            steps = data['cost_code'].rule_of_credit.steps if data['cost_code'].rule_of_credit else []
            for i in range(7):
                if i < len(steps):
                    cost_code_row.append(Paragraph(steps[i].name, rules_style))
                else:
                    cost_code_row.append(Paragraph('', rules_style))
            
            table_data.append(cost_code_row)
            table_style.append(('SPAN', (0, row_index), (5, row_index)))
            table_style.append(('BACKGROUND', (0, row_index), (12, row_index), colors.whitesmoke))
            row_index += 1
            
            # Work items
            for item in data['items']:
                progress = 0
                if item.budgeted_quantity and item.budgeted_quantity > 0:
                    progress = (item.earned_quantity or 0) / item.budgeted_quantity * 100
                
                item_row = [
                    Paragraph(str(item.work_item_id), normal_style),
                    Paragraph(item.description, normal_style),
                    Paragraph(item.uom or '', normal_style),
                    Paragraph(f"{item.budgeted_quantity or 0:.2f}", normal_style),
                    Paragraph(f"{item.earned_quantity or 0:.2f}", normal_style),
                    Paragraph(f"{progress:.1f}%", normal_style),
                ]
                
                # Add Rules of Credit progress steps
                progress_steps = getattr(item, 'progress_steps', []) or []
                for i in range(7):
                    if i < len(progress_steps):
                        item_row.append(Paragraph(f"{progress_steps[i].percentage:.0f}%", rules_style))
                    else:
                        item_row.append(Paragraph('', rules_style))
                
                table_data.append(item_row)
                row_index += 1
            
            # Cost code total
            cost_code_progress = 0
            if data['total_budgeted_quantity'] > 0:
                cost_code_progress = data['total_earned_quantity'] / data['total_budgeted_quantity'] * 100
            
            cost_code_total_row = [
                Paragraph('<b>Cost Code Total</b>', normal_style),
                Paragraph('', normal_style),
                Paragraph('', normal_style),
                Paragraph(f"<b>{data['total_budgeted_quantity']:.2f}</b>", normal_style),
                Paragraph(f"<b>{data['total_earned_quantity']:.2f}</b>", normal_style),
                Paragraph(f"<b>{cost_code_progress:.1f}%</b>", normal_style),
            ]
            cost_code_total_row.extend([Paragraph('', normal_style) for _ in range(7)])
            
            table_data.append(cost_code_total_row)
            table_style.append(('SPAN', (0, row_index), (2, row_index)))
            table_style.append(('BACKGROUND', (0, row_index), (12, row_index), colors.whitesmoke))
            row_index += 1
        
        # Discipline total
        discipline_progress = 0
        if discipline_totals[discipline]['total_budgeted_quantity'] > 0:
            discipline_progress = discipline_totals[discipline]['total_earned_quantity'] / discipline_totals[discipline]['total_budgeted_quantity'] * 100
        
        discipline_total_row = [
            Paragraph('<b>Discipline Total</b>', normal_style),
            Paragraph('', normal_style),
            Paragraph('', normal_style),
            Paragraph(f"<b>{discipline_totals[discipline]['total_budgeted_quantity']:.2f}</b>", normal_style),
            Paragraph(f"<b>{discipline_totals[discipline]['total_earned_quantity']:.2f}</b>", normal_style),
            Paragraph(f"<b>{discipline_progress:.1f}%</b>", normal_style),
        ]
        discipline_total_row.extend([Paragraph('', normal_style) for _ in range(7)])
        
        table_data.append(discipline_total_row)
        table_style.append(('SPAN', (0, row_index), (2, row_index)))
        table_style.append(('BACKGROUND', (0, row_index), (12, row_index), colors.whitesmoke))
        row_index += 1
    
    # Grand total
    grand_total_row = [
        Paragraph('<b>Grand Total</b>', normal_style),
        Paragraph('', normal_style),
        Paragraph('', normal_style),
        Paragraph(f"<b>{total_budgeted_quantity:.2f}</b>", normal_style),
        Paragraph(f"<b>{total_earned_quantity:.2f}</b>", normal_style),
        Paragraph(f"<b>{overall_progress:.1f}%</b>", normal_style),
    ]
    grand_total_row.extend([Paragraph('', normal_style) for _ in range(7)])
    
    table_data.append(grand_total_row)
    table_style.append(('SPAN', (0, row_index), (2, row_index)))
    table_style.append(('BACKGROUND', (0, row_index), (12, row_index), colors.lightgrey))
    
    # Create table
    col_widths = [0.8*inch, 2*inch, 0.5*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.5*inch, 0.5*inch, 0.5*inch, 0.5*inch, 0.5*inch, 0.5*inch, 0.5*inch]
    table = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle(table_style))
    
    elements.append(table)
    
    # Build PDF
    doc.build(elements, canvasmaker=HeaderCanvas)
    
    # Get PDF data
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data
