"""
Updated routes.py for Magellan EV Tracker v3.0
- Fixes rules_of_credit route to ensure proper session refresh
- Adds explicit session refresh before retrieving rules
- Ensures newly created rules appear in the listing
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
import traceback
from models import db
from services.project_service import ProjectService
from services.sub_job_service import SubJobService
from services.cost_code_service import CostCodeService
from services.work_item_service import WorkItemService
from services.rule_of_credit_service import RuleOfCreditService
from utils.url_service import UrlService

# Define blueprint
main_bp = Blueprint('main', __name__)

# Rule of Credit routes
@main_bp.route('/rules_of_credit')
def rules_of_credit():
    try:
        # Explicitly refresh the session to ensure we get the latest data
        db.session.commit()  # Commit any pending transactions
        
        # Get all rules with a fresh query
        rules = RuleOfCreditService.get_all_rules_of_credit()
        
        return render_template('rules_of_credit.html', rules=rules)
    except Exception as e:
        flash(f"Error loading rules of credit: {str(e)}", "error")
        return render_template('rules_of_credit.html', rules=[])
