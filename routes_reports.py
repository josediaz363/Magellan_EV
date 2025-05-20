import os
from datetime import datetime
from flask import Blueprint, render_template, request, send_file, current_app, jsonify
from models import Project, SubJob
from alternative_report_generator import AlternativeReportGenerator

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
def reports():
    """Render the reports page"""
    projects = Project.query.all()
    return render_template('reports.html', projects=projects)

@reports_bp.route('/api/get_subjobs/<int:project_id>')
def get_subjobs(project_id):
    """Get sub-jobs for a project"""
    subjobs = SubJob.query.filter_by(project_id=project_id).all()
    return jsonify([{'id': sj.id, 'name': sj.name, 'sub_job_id_str': sj.sub_job_id_str} for sj in subjobs])

@reports_bp.route('/api/generate_report', methods=['POST'])
def generate_report():
    """Generate a report"""
    try:
        data = request.json
        project_id = data.get('project_id')
        sub_job_id = data.get('sub_job_id')
        report_type = data.get('report_type')
        
        if not project_id or not report_type:
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Create reports directory if it doesn't exist
        reports_dir = os.path.join(current_app.root_path, 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        # Initialize report generator
        logo_path = os.path.join(current_app.root_path, 'static', 'logo.png')
        db_path = os.path.join(current_app.root_path, 'ev_data.db')
        report_generator = AlternativeReportGenerator(db_path, logo_path)
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Get project and sub-job info
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': f'Project with ID {project_id} not found'}), 404
        
        sub_job = None
        if sub_job_id:
            sub_job = SubJob.query.get(sub_job_id)
            if not sub_job:
                return jsonify({'error': f'Sub-job with ID {sub_job_id} not found'}), 404
            
            base_name = f"{project.project_id_str}_{sub_job.sub_job_id_str}"
        else:
            base_name = project.project_id_str
        
        # Generate report based on type
        if report_type == 'hours':
            output_path = os.path.join(reports_dir, f"{base_name}_hours_{timestamp}.pdf")
            report_generator.generate_hours_pdf(project_id, output_path, sub_job_id)
            return send_file(output_path, as_attachment=True)
        
        elif report_type == 'quantities':
            output_path = os.path.join(reports_dir, f"{base_name}_quantities_{timestamp}.pdf")
            report_generator.generate_quantities_pdf(project_id, output_path, sub_job_id)
            return send_file(output_path, as_attachment=True)
        
        elif report_type == 'excel':
            output_path = os.path.join(reports_dir, f"{base_name}_data_{timestamp}.xlsx")
            report_generator.generate_excel_export(project_id, output_path, sub_job_id)
            return send_file(output_path, as_attachment=True)
        
        else:
            return jsonify({'error': f'Invalid report type: {report_type}'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
