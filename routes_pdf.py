from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
import traceback
import io
import json
from datetime import datetime
from models import db, Project, SubJob, WorkItem, CostCode, RuleOfCredit, RuleOfCreditStep

main_bp = Blueprint('main', __name__)

# ===== PDF EXPORT ROUTES =====

@main_bp.route('/export/quantities/pdf/<int:project_id>')
def export_quantities_pdf_project(project_id):
    """Export quantities report as PDF for a project"""
    try:
        # Import the PDF generation function
        from reports.pdf_export import generate_quantities_report_pdf
        
        # Generate PDF - now returns BytesIO object directly
        buffer = generate_quantities_report_pdf(project_id=project_id)
        
        # Create a filename
        project = Project.query.get_or_404(project_id)
        filename = f"{project.project_id_str}_quantities_report.pdf"
        
        # Return the PDF file - send the BytesIO buffer directly
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.reports_index'))

@main_bp.route('/export/quantities/pdf/<int:project_id>/<int:sub_job_id>')
def export_quantities_pdf_subjob(project_id, sub_job_id):
    """Export quantities report as PDF for a sub job"""
    try:
        # Import the PDF generation function
        from reports.pdf_export import generate_quantities_report_pdf
        
        # Generate PDF - now returns BytesIO object directly
        buffer = generate_quantities_report_pdf(project_id=project_id, sub_job_id=sub_job_id)
        
        # Create a filename
        project = Project.query.get_or_404(project_id)
        sub_job = SubJob.query.get_or_404(sub_job_id)
        filename = f"{project.project_id_str}_{sub_job.sub_job_id_str}_quantities_report.pdf"
        
        # Return the PDF file - send the BytesIO buffer directly
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'danger')
        traceback.print_exc()
        return redirect(url_for('main.reports_index'))
