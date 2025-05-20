import os
import sys
from flask import Blueprint, render_template, request, jsonify, current_app, send_file
from src.models import db, Project, SubJob, CostCode, RuleOfCredit, WorkItem
from src.alternative_report_generator import AlternativeReportGenerator

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
def reports_page():
    return render_template('reports.html')

@reports_bp.route('/generate', methods=['POST'])
def generate_report():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        project_id = data.get('project_id')
        sub_job_id = data.get('sub_job_id')
        report_type = data.get('report_type')
        
        if not project_id:
            return jsonify({'error': 'Project ID is required'}), 400
        
        if not report_type:
            return jsonify({'error': 'Report type is required'}), 400
        
        # Get project info
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': f'Project with ID {project_id} not found'}), 404
        
        # Get sub-job info if specified
        sub_job = None
        if sub_job_id:
            sub_job = SubJob.query.get(sub_job_id)
            if not sub_job:
                return jsonify({'error': f'Sub-job with ID {sub_job_id} not found'}), 404
        
        # Create output directory if it doesn't exist
        output_dir = os.path.join(current_app.root_path, '..', 'reports')
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize report generator
        logo_path = os.path.join(current_app.root_path, 'static', 'logo.png')
        db_path = os.path.join(current_app.root_path, 'ev_data.db')
        
        report_generator = AlternativeReportGenerator(db_path, logo_path)
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate file names
        if sub_job:
            base_name = f"{project.project_id_str}_{sub_job.sub_job_id_str}"
            display_name = f"{project.name}_{sub_job.name}"
        else:
            base_name = project.project_id_str
            display_name = project.name
        
        # Generate reports based on type
        if report_type == 'hours_pdf':
            output_path = os.path.join(output_dir, f"{base_name}_hours_{timestamp}.pdf")
            report_generator.generate_hours_pdf(project_id, output_path, sub_job_id)
            return send_file(output_path, as_attachment=True, download_name=f"{display_name}_hours.pdf")
        
        elif report_type == 'quantities_pdf':
            output_path = os.path.join(output_dir, f"{base_name}_quantities_{timestamp}.pdf")
            report_generator.generate_quantities_pdf(project_id, output_path, sub_job_id)
            return send_file(output_path, as_attachment=True, download_name=f"{display_name}_quantities.pdf")
        
        elif report_type == 'excel':
            output_path = os.path.join(output_dir, f"{base_name}_data_{timestamp}.xlsx")
            report_generator.generate_excel_export(project_id, output_path, sub_job_id)
            return send_file(output_path, as_attachment=True, download_name=f"{display_name}_data.xlsx")
        
        elif report_type == 'all':
            reports = report_generator.generate_reports(project_id, output_dir, sub_job_id)
            
            # Return the first report (hours PDF) and include paths to all reports in the response
            response = send_file(reports['hours_pdf'], as_attachment=True, download_name=f"{display_name}_hours.pdf")
            response.headers['X-Reports'] = ','.join([
                reports['hours_pdf'],
                reports['quantities_pdf'],
                reports['excel']
            ])
            return response
        
        else:
            return jsonify({'error': f'Invalid report type: {report_type}'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
