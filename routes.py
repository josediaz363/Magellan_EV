from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from models import db, Project, SubJob, RuleOfCredit, CostCode, WorkItem, DISCIPLINE_CHOICES
import json
import uuid
import traceback
import os
import datetime
import io

# Create a blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page route"""
    try:
        projects = Project.query.all()
        work_items = WorkItem.query.order_by(WorkItem.id.desc()).limit(10).all()
        
        # Calculate overall progress for dashboard
        overall_progress = 0
        total_budgeted_hours = 0
        total_earned_hours = 0
        
        # Get all work items to calculate overall progress
        all_work_items = WorkItem.query.all()
        
        # Calculate totals
        for item in all_work_items:
            if item.budgeted_man_hours:
                total_budgeted_hours += item.budgeted_man_hours
                # Calculate earned hours based on percent complete
                earned_hours = item.budgeted_man_hours * (item.percent_complete_hours / 100) if item.percent_complete_hours else 0
                total_earned_hours += earned_hours
        
        # Calculate overall progress percentage
        if total_budgeted_hours > 0:
            overall_progress = (total_earned_hours / total_budgeted_hours) * 100
            overall_progress = round(overall_progress, 1)  # Round to 1 decimal place
        
        return render_template('index.html', 
                              projects=projects, 
                              work_items=work_items, 
                              overall_progress=overall_progress)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('index.html', projects=[], work_items=[], overall_progress=0)

# ===== PROJECT ROUTES =====

@main_bp.route('/projects')
def projects():
    """List all projects"""
    try:
        all_projects = Project.query.all()
        
        # Create a list to hold projects with their calculated values
        projects_with_data = []
        
        # Calculate project-level totals for each project
        for project in all_projects:
            # Get all work items for this project
            work_items = WorkItem.query.filter_by(project_id=project.id).all()
            
            # Calculate totals using local variables instead of setting properties directly
            total_budgeted_hours = sum(item.budgeted_man_hours or 0 for item in work_items)
            total_earned_hours = sum(item.earned_man_hours or 0 for item in work_items)
            total_budgeted_quantity = sum(item.budgeted_quantity or 0 for item in work_items)
            total_earned_quantity = sum(item.earned_quantity or 0 for item in work_items)
            
            # Calculate overall progress percentage
            overall_progress = 0
            if total_budgeted_hours > 0:
                overall_progress = (total_earned_hours / total_budgeted_hours) * 100
                
            # Add project with calculated data to the list
            projects_with_data.append({
                'project': project,
                'total_budgeted_hours': total_budgeted_hours,
                'total_earned_hours': total_earned_hours,
                'total_budgeted_quantity': total_budgeted_quantity,
                'total_earned_quantity': total_earned_quantity,
                'overall_progress': overall_progress
            })
        
        return render_template('projects.html', projects=projects_with_data)
    except Exception as e:
        flash(f'Error loading projects: {str(e)}', 'danger')
        traceback.print_exc()
        return render_template('projects.html', projects=[])
