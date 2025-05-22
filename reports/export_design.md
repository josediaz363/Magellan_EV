# Export Functionality Design for Magellan EV Tracker

## Overview
This document outlines the design for PDF and Excel export functionality for the Magellan EV Tracker application, based on the approved report templates.

## Report Types
Two main report types will be supported:
1. **Hours Report** - Focusing on budgeted and earned hours
2. **Quantities Report** - Focusing on budgeted and earned quantities

## Export Formats
Each report type will be available in two formats:
1. **PDF** - Using WeasyPrint to generate PDF files from HTML templates
2. **Excel** - Using openpyxl to generate Excel files with similar formatting

## Data Structure
Reports will be organized hierarchically:
- Project level
- Discipline level (grouping)
- Cost Code level (grouping)
- Work Item level (detail)

## Common Elements

### Header Section
- Left: Logo
- Center: Report title, subtitle, project name, project ID
- Right: Page information, date

### Table Structure
- Column headers with appropriate widths
- Work items grouped by discipline and cost code
- Rules of Credit steps displayed as columns
- Subtotals at cost code and discipline levels
- Grand total at the bottom

## PDF Export Implementation

### Technology
- WeasyPrint for HTML to PDF conversion
- Jinja2 templates for dynamic content generation

### Template Structure
- Base on existing hours_report_template.html and quantities_report_template.html
- Ensure proper CSS styling for all elements
- Support for dynamic Rules of Credit columns

### Special Considerations
- Ensure Rules of Credit step names are correctly aligned
- Make font size of Rules of Credit steps 2 points smaller
- Right-align text in header right section
- Remove space between report title and subtitle

## Excel Export Implementation

### Technology
- openpyxl for Excel file generation

### Worksheet Structure
- Match the same data organization as PDF reports
- Use Excel native formatting for headers, grouping, and totals
- Apply appropriate cell styles (borders, colors, alignment)

### Special Considerations
- Set column widths to match PDF layout
- Make 'Work Item' and 'Description' columns thinner
- Make Rules of Credit columns wider
- Use smaller font for Rules of Credit steps
- Implement Excel formulas for subtotals and totals

## UI Integration

### Export Buttons
- Add export buttons to relevant pages:
  - Project view page
  - Sub job view page
- Provide options for both PDF and Excel formats
- Use dropdown or separate buttons for each format

### Routes
- Create new routes for handling export requests:
  - `/export/pdf/hours/<project_id>` - Project hours report (PDF)
  - `/export/pdf/hours/<project_id>/<sub_job_id>` - Sub job hours report (PDF)
  - `/export/pdf/quantities/<project_id>` - Project quantities report (PDF)
  - `/export/pdf/quantities/<project_id>/<sub_job_id>` - Sub job quantities report (PDF)
  - `/export/excel/hours/<project_id>` - Project hours report (Excel)
  - `/export/excel/hours/<project_id>/<sub_job_id>` - Sub job hours report (Excel)
  - `/export/excel/quantities/<project_id>` - Project quantities report (Excel)
  - `/export/excel/quantities/<project_id>/<sub_job_id>` - Sub job quantities report (Excel)

## Data Processing

### Common Functions
- `prepare_report_data(project_id, sub_job_id=None, report_type='hours')` - Prepare data for both PDF and Excel reports
- `group_work_items_by_discipline_and_cost_code(work_items)` - Group work items for hierarchical display
- `calculate_subtotals(grouped_data, report_type)` - Calculate subtotals at each level

### PDF-Specific Functions
- `generate_pdf_report(data, template_path, output_path)` - Generate PDF from template and data
- `encode_logo_to_base64()` - Encode logo for embedding in PDF

### Excel-Specific Functions
- `generate_excel_report(data, output_path, report_type)` - Generate Excel file from data
- `apply_excel_formatting(worksheet, report_type)` - Apply formatting to Excel worksheet
- `add_excel_formulas(worksheet, row_indices, report_type)` - Add calculation formulas

## Implementation Plan
1. Create report data preparation functions
2. Implement PDF export functionality
3. Implement Excel export functionality
4. Add UI elements for export options
5. Test with various data scenarios
6. Optimize performance for large datasets
