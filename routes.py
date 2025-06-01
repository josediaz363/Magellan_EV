"""
Updated routes.py for Magellan EV Tracker v3.0
- Adds dashboard route to serve as the default landing page
- Maintains all existing functionality
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, session
from models import db, Project, SubJob, WorkItem, RuleOfCredit
from services.project_service import ProjectService
from services.sub_job_service import SubJobService
from services.work_item_service import WorkItemService
from services.rule_of_credit_service import RuleOfCreditService
from services.url_service import UrlService
import json
from datetime import datetime

# Create blueprint
main_bp = Blueprint('main', __name__)

# Dashboard route
@main_bp.route('/dashboard')
def dashboard():
    # In a full implementation, you would fetch actual data here
    # For now, we're just rendering the template
    return render_template('dashboard.html')

# Rules of Credit routes
@main_bp.route('/rules_of_credit')
def rules_of_credit():
    try:
        # Get action from query parameters
        action = request.args.get('action')
        view_id = request.args.get('view')
        edit_id = request.args.get('edit')
        delete_id = request.args.get('delete')
        
        # Handle different actions based on query parameters
        if action == 'add':
            return render_template('add_rule_of_credit.html')
        elif view_id:
            rule = RuleOfCreditService.get_rule_of_credit_by_id(view_id)
            if rule:
                return render_template('view_rule_of_credit.html', rule=rule)
            else:
                flash('Rule of Credit not found', 'danger')
        elif edit_id:
            rule = RuleOfCreditService.get_rule_of_credit_by_id(edit_id)
            if rule:
                return render_template('edit_rule_of_credit.html', rule=rule)
            else:
                flash('Rule of Credit not found', 'danger')
        elif delete_id:
            rule = RuleOfCreditService.get_rule_of_credit_by_id(delete_id)
            if rule:
                RuleOfCreditService.delete_rule_of_credit(rule)
                flash(f'Rule of Credit {rule.name} deleted successfully', 'success')
            else:
                flash('Rule of Credit not found', 'danger')
        
        # Default: list all rules of credit
        rules = RuleOfCreditService.get_all_rules_of_credit()
        return render_template('rules_of_credit.html', rules=rules)
    except Exception as e:
        flash(f'Error loading rules of credit: {str(e)}', 'danger')
        return render_template('rules_of_credit.html', rules=[])

# Keep all other existing routes below
# ...

# The rest of your routes.py file continues here
