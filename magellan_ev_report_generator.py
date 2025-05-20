import os
import sys
import json
from datetime import datetime
import pandas as pd
from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader
import sqlite3
import base64

# Data model classes
class Project:
    def __init__(self, id, project_id_str, name):
        self.id = id
        self.project_id_str = project_id_str
        self.name = name

class SubJob:
    def __init__(self, id, project_id, sub_job_id_str, name):
        self.id = id
        self.project_id = project_id
        self.sub_job_id_str = sub_job_id_str
        self.name = name

class CostCode:
    def __init__(self, id, project_id, cost_code_id_str, description, discipline, rule_of_credit_id):
        self.id = id
        self.project_id = project_id
        self.cost_code_id_str = cost_code_id_str
        self.description = description
        self.discipline = discipline
        self.rule_of_credit_id = rule_of_credit_id

class RuleOfCredit:
    def __init__(self, id, name, steps_json):
        self.id = id
        self.name = name
        self.steps_json = steps_json
        try:
            self.steps = json.loads(steps_json) if steps_json else []
        except json.JSONDecodeError:
            self.steps = []

class WorkItem:
    def __init__(self, id, project_id, sub_job_id, cost_code_id, work_item_id_str, description, 
                 budgeted_quantity, earned_quantity, percent_complete_quantity, 
                 budgeted_man_hours, earned_man_hours, percent_complete_hours, 
                 unit_of_measure, progress_json):
        self.id = id
        self.project_id = project_id
        self.sub_job_id = sub_job_id
        self.cost_code_id = cost_code_id
        self.work_item_id_str = work_item_id_str
        self.description = description
        self.budgeted_quantity = budgeted_quantity
        self.earned_quantity = earned_quantity
        self.percent_complete_quantity = percent_complete_quantity
        self.budgeted_man_hours = budgeted_man_hours
        self.earned_man_hours = earned_man_hours
        self.percent_complete_hours = percent_complete_hours
        self.unit_of_measure = unit_of_measure
        self.progress_json = progress_json
        self.roc_steps_progress = {}
        if self.progress_json:
            try:
                progress_data = json.loads(self.progress_json)
                # Ensure progress_data is a list of dictionaries with "step_name" and "current_complete_percentage"
                if isinstance(progress_data, list):
                    for step_progress in progress_data:
                        if isinstance(step_progress, dict) and "step_name" in step_progress and "current_complete_percentage" in step_progress:
                            self.roc_steps_progress[step_progress["step_name"]] = float(step_progress["current_complete_percentage"])
                        elif isinstance(step_progress, dict) and "name" in step_progress and "percentage" in step_progress: # Legacy format
                             self.roc_steps_progress[step_progress["name"]] = float(step_progress["percentage"])
                elif isinstance(progress_data, dict): # Older format where keys are step names
                    for step_name, percentage in progress_data.items():
                        self.roc_steps_progress[step_name] = float(percentage)

            except (json.JSONDecodeError, TypeError, ValueError) as e:
                print(f"Error parsing progress data for work item {self.id}: {e}")

class ReportGenerator:
    """
    A class to generate PDF and Excel reports for the Magellan EV Tracker.
    This class handles both project-wide and sub-job specific reports.
    """
    
    def __init__(self, db_path, logo_path):
        self.db_path = db_path
        self.logo_path = logo_path
        self.conn = None
        self.logo_base64 = None
        self.template_dir = None
        self._connect_db()
        self._load_logo()
        self.template_dir = self._create_report_templates()
    
    def _connect_db(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
    
    def _load_logo(self):
        try:
            with open(self.logo_path, "rb") as logo_file:
                self.logo_base64 = base64.b64encode(logo_file.read()).decode("utf-8")
        except Exception as e:
            print(f"Warning: Could not load logo from {self.logo_path}: {e}")
            self.logo_base64 = ""
    
    def _create_report_templates(self):
        template_dir = "/home/ubuntu/report_templates"
        os.makedirs(template_dir, exist_ok=True)
        
        hours_template_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ project.name }} - Hours Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
                table { width: 100%; border-collapse: collapse; margin-bottom: 15px; }
                th, td { border: 1px solid #000; padding: 4px; text-align: center; font-size: 8pt; vertical-align: middle; word-wrap: break-word; }
                th { background-color: #f2f2f2; font-weight: bold; }
                .header-container { display: flex; border: 2px solid #000; margin-bottom: 10px; }
                .header-left { flex: 1; padding: 5px; display: flex; align-items: center; }
                .header-center { flex: 2; padding: 5px; text-align: center; border-left: 2px solid #000; border-right: 2px solid #000; }
                .header-right { flex: 1; padding: 5px; text-align: right; }
                .logo { height: 50px; margin-right: 10px; }
                .project-info { text-align: center; margin-top: 5px; }
                .project-title { font-size: 12pt; font-weight: bold; margin: 0; }
                .project-id { font-size: 10pt; margin: 3px 0; }
                .report-title { font-size: 14pt; font-weight: bold; margin: 0; }
                .report-subtitle { font-size: 12pt; margin: 3px 0; }
                .page-info { font-size: 9pt; margin: 3px 0; }
                .discipline-header { background-color: #d9d9d9; font-weight: bold; text-align: left; padding-left: 5px; }
                .cost-code-main-header { background-color: #e6e6e6; font-weight: bold; text-align: left; padding-left: 5px; }
                .cost-code-roc-header { background-color: #e6e6e6; font-weight: bold; text-align: center; font-size: 6pt; }
                .subtotal-row { background-color: #e6f2ff; font-weight: bold; }
                .total-row { background-color: #cce5ff; font-weight: bold; }
                .numeric { text-align: right; }
                .roc-data-cell { text-align: right; font-size: 6pt;}
                .roc-main-header-row th { background-color: #f2f2f2; font-weight: bold; text-align: center; }
                .work-item-description {text-align: left; padding-left: 5px;}
                .work-item-id { width: 10%; }
                .description-col { width: 20%; }
                .numeric-col { width: 8%; }
                .roc-col { width: 7%; }
            </style>
        </head>
        <body>
            <div class="header-container">
                <div class="header-left">
                    <img src="data:image/png;base64,{{ logo_base64 }}" class="logo" alt="Logo">
                </div>
                <div class="header-center">
                    <p class="report-title">PROGRESS DETAIL</p>
                    <p class="report-subtitle">{% if sub_job %}Sub Job by Hours{% else %}Total Project by Hours{% endif %}</p>
                    <div class="project-info">
                        <p class="project-title">{{ project.name }}</p>
                        <p class="project-id">{{ project.project_id_str }}</p>
                    </div>
                </div>
                <div class="header-right"><p class="page-info">Page @page of @topage</p><p class="page-info">Progress Thru:</p><p class="page-info">{{ report_date }}</p></div>
            </div>
            {% if sub_job %}<h3>{{ sub_job.sub_job_id_str }} - {{ sub_job.name }}</h3>{% endif %}
            <table>
                <thead>
                    <tr class="roc-main-header-row">
                        <th class="work-item-id">Work Item</th>
                        <th class="description-col">Description</th>
                        <th class="numeric-col">Budgeted Hours</th>
                        <th class="numeric-col">Earned Hours</th>
                        <th class="numeric-col">% Complete</th>
                        <th colspan="7">Rules of Credit Steps</th>
                    </tr>
                </thead>
                <tbody>
                    {% for discipline, discipline_data in grouped_work_items.items() %}
                        <tr><td colspan="12" class="discipline-header">{{ discipline }}</td></tr>
                        {% for cost_code, cost_code_data in discipline_data.cost_codes.items() %}
                            <tr>
                                <td class="cost-code-main-header" colspan="1">{{ cost_code }}</td>
                                <td class="cost-code-main-header" colspan="4">&nbsp;</td> {# Empty cells for Desc, Budgeted, Earned, % Comp on CC row #}
                                {% for step_header_name in cost_code_data.roc_step_headers %}
                                <th class="cost-code-roc-header roc-col">{{ step_header_name }}</th>
                                {% endfor %}
                            </tr>
                            {% for work_item in cost_code_data.work_items %}
                                <tr>
                                    <td class="work-item-id">{{ work_item.work_item_id_str }}</td>
                                    <td class="work-item-description description-col">{{ work_item.description }}</td>
                                    <td class="numeric numeric-col">{{ "%.2f"|format(work_item.budgeted_man_hours or 0) }}</td>
                                    <td class="numeric numeric-col">{{ "%.2f"|format(work_item.earned_man_hours or 0) }}</td>
                                    <td class="numeric numeric-col">{{ "%.1f%%"|format(work_item.percent_complete_hours or 0) }}</td>
                                    {% for step_name_key in cost_code_data.roc_step_headers %}
                                    <td class="roc-data-cell roc-col">
                                        {% if step_name_key and step_name_key in work_item.roc_steps_progress %}
                                        {{ "%.1f%%"|format(work_item.roc_steps_progress[step_name_key] or 0) }}
                                        {% elif step_name_key %}
                                        0.0%
                                        {% else %}
                                        &nbsp;
                                        {% endif %}
                                    </td>
                                    {% endfor %}
                                </tr>
                            {% endfor %}
                            <tr class="subtotal-row">
                                <td colspan="2">Cost Code Subtotal</td>
                                <td class="numeric">{{ "%.2f"|format(cost_code_data.subtotals.budgeted_hours) }}</td>
                                <td class="numeric">{{ "%.2f"|format(cost_code_data.subtotals.earned_hours) }}</td>
                                <td class="numeric">{{ "%.1f%%"|format(cost_code_data.subtotals.percent_complete_hours) }}</td>
                                <td colspan="7">&nbsp;</td>
                            </tr>
                        {% endfor %}
                        <tr class="subtotal-row">
                            <td colspan="2">Discipline Subtotal</td>
                            <td class="numeric">{{ "%.2f"|format(discipline_data.subtotals.budgeted_hours) }}</td>
                            <td class="numeric">{{ "%.2f"|format(discipline_data.subtotals.earned_hours) }}</td>
                            <td class="numeric">{{ "%.1f%%"|format(discipline_data.subtotals.percent_complete_hours) }}</td>
                            <td colspan="7">&nbsp;</td>
                        </tr>
                    {% endfor %}
                    <tr class="total-row">
                        <td colspan="2">Total</td>
                        <td class="numeric">{{ "%.2f"|format(project_totals.budgeted_hours) }}</td>
                        <td class="numeric">{{ "%.2f"|format(project_totals.earned_hours) }}</td>
                        <td class="numeric">{{ "%.1f%%"|format(project_totals.percent_complete_hours) }}</td>
                        <td colspan="7">&nbsp;</td>
                    </tr>
                </tbody>
            </table>
        </body>
        </html>
        """
        with open(os.path.join(template_dir, "hours_report_template.html"), "w") as f:
            f.write(hours_template_content)

        quantities_template_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ project.name }} - Quantities Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
                table { width: 100%; border-collapse: collapse; margin-bottom: 15px; }
                th, td { border: 1px solid #000; padding: 4px; text-align: center; font-size: 8pt; vertical-align: middle; word-wrap: break-word; }
                th { background-color: #f2f2f2; font-weight: bold; }
                .header-container { display: flex; border: 2px solid #000; margin-bottom: 10px; }
                .header-left { flex: 1; padding: 5px; display: flex; align-items: center; }
                .header-center { flex: 2; padding: 5px; text-align: center; border-left: 2px solid #000; border-right: 2px solid #000; }
                .header-right { flex: 1; padding: 5px; text-align: right; }
                .logo { height: 50px; margin-right: 10px; }
                .project-info { text-align: center; margin-top: 5px; }
                .project-title { font-size: 12pt; font-weight: bold; margin: 0; }
                .project-id { font-size: 10pt; margin: 3px 0; }
                .report-title { font-size: 14pt; font-weight: bold; margin: 0; }
                .report-subtitle { font-size: 12pt; margin: 3px 0; }
                .page-info { font-size: 9pt; margin: 3px 0; }
                .discipline-header { background-color: #d9d9d9; font-weight: bold; text-align: left; padding-left: 5px; }
                .cost-code-main-header { background-color: #e6e6e6; font-weight: bold; text-align: left; padding-left: 5px; }
                .cost-code-roc-header { background-color: #e6e6e6; font-weight: bold; text-align: center; font-size: 6pt; }
                .subtotal-row { background-color: #e6f2ff; font-weight: bold; }
                .total-row { background-color: #cce5ff; font-weight: bold; }
                .numeric { text-align: right; }
                .roc-data-cell { text-align: right; font-size: 6pt;}
                .roc-main-header-row th { background-color: #f2f2f2; font-weight: bold; text-align: center; }
                .work-item-description {text-align: left; padding-left: 5px;}
                .work-item-id { width: 10%; }
                .description-col { width: 20%; }
                .uom-col { width: 5%; }
                .numeric-col { width: 8%; }
                .roc-col { width: 7%; }
            </style>
        </head>
        <body>
            <div class="header-container">
                <div class="header-left">
                    <img src="data:image/png;base64,{{ logo_base64 }}" class="logo" alt="Logo">
                </div>
                <div class="header-center">
                    <p class="report-title">QUANTITY DETAIL</p>
                    <p class="report-subtitle">{% if sub_job %}Sub Job by Quantities{% else %}Total Project by Quantities{% endif %}</p>
                    <div class="project-info">
                        <p class="project-title">{{ project.name }}</p>
                        <p class="project-id">{{ project.project_id_str }}</p>
                    </div>
                </div>
                <div class="header-right"><p class="page-info">Page @page of @topage</p><p class="page-info">Progress Thru:</p><p class="page-info">{{ report_date }}</p></div>
            </div>
            {% if sub_job %}<h3>{{ sub_job.sub_job_id_str }} - {{ sub_job.name }}</h3>{% endif %}
            <table>
                <thead>
                    <tr class="roc-main-header-row">
                        <th class="work-item-id">Work Item</th>
                        <th class="description-col">Description</th>
                        <th class="uom-col">UOM</th>
                        <th class="numeric-col">Budgeted Quantity</th>
                        <th class="numeric-col">Earned Quantity</th>
                        <th class="numeric-col">% Complete</th>
                        <th colspan="7">Rules of Credit Steps</th>
                    </tr>
                </thead>
                <tbody>
                    {% for discipline, discipline_data in grouped_work_items.items() %}
                        <tr><td colspan="13" class="discipline-header">{{ discipline }}</td></tr>
                        {% for cost_code, cost_code_data in discipline_data.cost_codes.items() %}
                            <tr>
                                <td class="cost-code-main-header" colspan="1">{{ cost_code }}</td>
                                <td class="cost-code-main-header" colspan="5">&nbsp;</td> {# Empty cells for Desc, UOM, Budgeted, Earned, % Comp on CC row #}
                                {% for step_header_name in cost_code_data.roc_step_headers %}
                                <th class="cost-code-roc-header roc-col">{{ step_header_name }}</th>
                                {% endfor %}
                            </tr>
                            {% for work_item in cost_code_data.work_items %}
                                <tr>
                                    <td class="work-item-id">{{ work_item.work_item_id_str }}</td>
                                    <td class="work-item-description description-col">{{ work_item.description }}</td>
                                    <td class="uom-col">{{ work_item.unit_of_measure }}</td>
                                    <td class="numeric numeric-col">{{ "%.2f"|format(work_item.budgeted_quantity or 0) }}</td>
                                    <td class="numeric numeric-col">{{ "%.2f"|format(work_item.earned_quantity or 0) }}</td>
                                    <td class="numeric numeric-col">{{ "%.1f%%"|format(work_item.percent_complete_quantity or 0) }}</td>
                                    {% for step_name_key in cost_code_data.roc_step_headers %}
                                    <td class="roc-data-cell roc-col">
                                        {% if step_name_key and step_name_key in work_item.roc_steps_progress %}
                                        {{ "%.1f%%"|format(work_item.roc_steps_progress[step_name_key] or 0) }}
                                        {% elif step_name_key %}
                                        0.0%
                                        {% else %}
                                        &nbsp;
                                        {% endif %}
                                    </td>
                                    {% endfor %}
                                </tr>
                            {% endfor %}
                            <tr class="subtotal-row">
                                <td colspan="2">Cost Code Subtotal</td>
                                <td>&nbsp;</td>
                                <td class="numeric">{{ "%.2f"|format(cost_code_data.subtotals.budgeted_quantity) }}</td>
                                <td class="numeric">{{ "%.2f"|format(cost_code_data.subtotals.earned_quantity) }}</td>
                                <td class="numeric">{{ "%.1f%%"|format(cost_code_data.subtotals.percent_complete_quantity) }}</td>
                                <td colspan="7">&nbsp;</td>
                            </tr>
                        {% endfor %}
                        <tr class="subtotal-row">
                            <td colspan="3">Discipline Subtotal</td>
                            <td class="numeric">{{ "%.2f"|format(discipline_data.subtotals.budgeted_quantity) }}</td>
                            <td class="numeric">{{ "%.2f"|format(discipline_data.subtotals.earned_quantity) }}</td>
                            <td class="numeric">{{ "%.1f%%"|format(discipline_data.subtotals.percent_complete_quantity) }}</td>
                            <td colspan="7">&nbsp;</td>
                        </tr>
                    {% endfor %}
                    <tr class="total-row">
                        <td colspan="3">Total</td>
                        <td class="numeric">{{ "%.2f"|format(project_totals.budgeted_quantity) }}</td>
                        <td class="numeric">{{ "%.2f"|format(project_totals.earned_quantity) }}</td>
                        <td class="numeric">{{ "%.1f%%"|format(project_totals.percent_complete_quantity) }}</td>
                        <td colspan="7">&nbsp;</td>
                    </tr>
                </tbody>
            </table>
        </body>
        </html>
        """
        with open(os.path.join(template_dir, "quantities_report_template.html"), "w") as f:
            f.write(quantities_template_content)
        
        return template_dir

    def get_project_data(self, project_id_str, sub_job_id_str=None):
        cursor = self.conn.cursor()
        
        # Query the project
        cursor.execute("SELECT * FROM projects WHERE project_id_str = ?", (project_id_str,))
        project_row = cursor.fetchone()
        if not project_row:
            return None, f"Project with ID {project_id_str} not found."
        project = Project(**project_row)
        
        sub_job = None
        if sub_job_id_str:
            cursor.execute("SELECT * FROM sub_jobs WHERE project_id = ? AND sub_job_id_str = ?", (project.id, sub_job_id_str))
            sub_job_row = cursor.fetchone()
            if not sub_job_row:
                return None, f"Sub-Job with ID {sub_job_id_str} for Project {project_id_str} not found."
            sub_job = SubJob(**sub_job_row)
        
        # Query cost codes
        if sub_job:
            cursor.execute("SELECT DISTINCT cc.* FROM cost_codes cc JOIN work_items wi ON cc.id = wi.cost_code_id WHERE wi.project_id = ? AND wi.sub_job_id = ? ORDER BY cc.discipline, cc.cost_code_id_str", (project.id, sub_job.id))
        else:
            cursor.execute("SELECT * FROM cost_codes WHERE project_id = ? ORDER BY discipline, cost_code_id_str", (project.id,))
        cost_code_rows = cursor.fetchall()
        cost_codes = {cc_row["id"]: CostCode(**cc_row) for cc_row in cost_code_rows}

        # Query rules of credit
        roc_ids = [cc.rule_of_credit_id for cc in cost_codes.values() if cc.rule_of_credit_id is not None]
        rules_of_credit = {}
        if roc_ids:
            placeholders = ",".join("?" for _ in roc_ids)
            cursor.execute(f"SELECT * FROM rules_of_credit WHERE id IN ({placeholders})", roc_ids)
            roc_rows = cursor.fetchall()
            rules_of_credit = {roc_row["id"]: RuleOfCredit(**roc_row) for roc_row in roc_rows}

        # Query work items
        if sub_job:
            cursor.execute("SELECT * FROM work_items WHERE project_id = ? AND sub_job_id = ? ORDER BY cost_code_id, work_item_id_str", (project.id, sub_job.id))
        else:
            cursor.execute("SELECT * FROM work_items WHERE project_id = ? ORDER BY cost_code_id, work_item_id_str", (project.id,))
        work_item_rows = cursor.fetchall()
        all_work_items = []
        for wi_row_dict in work_item_rows:
            # Convert sqlite3.Row to a standard dictionary before passing to WorkItem constructor
            wi_row = dict(wi_row_dict)
            all_work_items.append(WorkItem(**wi_row))

        # Group work items by discipline and then by cost code
        grouped_work_items = {}
        project_totals = {"budgeted_quantity": 0, "earned_quantity": 0, "budgeted_hours": 0, "earned_hours": 0}

        for cc_id, cost_code_obj in cost_codes.items():
            discipline_name = cost_code_obj.discipline if cost_code_obj.discipline else "Unassigned Discipline"
            cost_code_str = cost_code_obj.cost_code_id_str
            
            if discipline_name not in grouped_work_items:
                grouped_work_items[discipline_name] = {
                    "cost_codes": {},
                    "subtotals": {"budgeted_quantity": 0, "earned_quantity": 0, "budgeted_hours": 0, "earned_hours": 0}
                }
            
            if cost_code_str not in grouped_work_items[discipline_name]["cost_codes"]:
                # Determine RoC step headers for this specific cost code
                current_roc_step_names = []
                if cost_code_obj.rule_of_credit_id and cost_code_obj.rule_of_credit_id in rules_of_credit:
                    roc = rules_of_credit[cost_code_obj.rule_of_credit_id]
                    # Fix: roc.steps is a list of strings, not dictionaries
                    current_roc_step_names = roc.steps
                
                # Ensure exactly 7 headers, padding with empty strings if fewer than 7 steps
                padded_roc_step_names = (current_roc_step_names + ["" for _ in range(7)])[:7]

                grouped_work_items[discipline_name]["cost_codes"][cost_code_str] = {
                    "work_items": [],
                    "roc_step_headers": padded_roc_step_names, # Cost-code specific RoC headers
                    "subtotals": {"budgeted_quantity": 0, "earned_quantity": 0, "budgeted_hours": 0, "earned_hours": 0}
                }

            cost_code_group = grouped_work_items[discipline_name]["cost_codes"][cost_code_str]
            discipline_group_subtotals = grouped_work_items[discipline_name]["subtotals"]

            for item in all_work_items:
                if item.cost_code_id == cc_id:
                    cost_code_group["work_items"].append(item)
                    # Accumulate subtotals for cost code
                    cost_code_group["subtotals"]["budgeted_quantity"] += item.budgeted_quantity or 0
                    cost_code_group["subtotals"]["earned_quantity"] += item.earned_quantity or 0
                    cost_code_group["subtotals"]["budgeted_hours"] += item.budgeted_man_hours or 0
                    cost_code_group["subtotals"]["earned_hours"] += item.earned_man_hours or 0
            
            # Calculate percent complete for cost code subtotals
            if cost_code_group["subtotals"]["budgeted_quantity"] > 0:
                cost_code_group["subtotals"]["percent_complete_quantity"] = (cost_code_group["subtotals"]["earned_quantity"] / cost_code_group["subtotals"]["budgeted_quantity"]) * 100
            else:
                cost_code_group["subtotals"]["percent_complete_quantity"] = 0
            
            if cost_code_group["subtotals"]["budgeted_hours"] > 0:
                cost_code_group["subtotals"]["percent_complete_hours"] = (cost_code_group["subtotals"]["earned_hours"] / cost_code_group["subtotals"]["budgeted_hours"]) * 100
            else:
                cost_code_group["subtotals"]["percent_complete_hours"] = 0

            # Accumulate subtotals for discipline
            discipline_group_subtotals["budgeted_quantity"] += cost_code_group["subtotals"]["budgeted_quantity"]
            discipline_group_subtotals["earned_quantity"] += cost_code_group["subtotals"]["earned_quantity"]
            discipline_group_subtotals["budgeted_hours"] += cost_code_group["subtotals"]["budgeted_hours"]
            discipline_group_subtotals["earned_hours"] += cost_code_group["subtotals"]["earned_hours"]

        # Calculate percent complete for discipline subtotals and project totals
        for discipline_name in grouped_work_items:
            discipline_group_subtotals = grouped_work_items[discipline_name]["subtotals"]
            if discipline_group_subtotals["budgeted_quantity"] > 0:
                discipline_group_subtotals["percent_complete_quantity"] = (discipline_group_subtotals["earned_quantity"] / discipline_group_subtotals["budgeted_quantity"]) * 100
            else:
                discipline_group_subtotals["percent_complete_quantity"] = 0
            if discipline_group_subtotals["budgeted_hours"] > 0:
                discipline_group_subtotals["percent_complete_hours"] = (discipline_group_subtotals["earned_hours"] / discipline_group_subtotals["budgeted_hours"]) * 100
            else:
                discipline_group_subtotals["percent_complete_hours"] = 0
            
            project_totals["budgeted_quantity"] += discipline_group_subtotals["budgeted_quantity"]
            project_totals["earned_quantity"] += discipline_group_subtotals["earned_quantity"]
            project_totals["budgeted_hours"] += discipline_group_subtotals["budgeted_hours"]
            project_totals["earned_hours"] += discipline_group_subtotals["earned_hours"]

        if project_totals["budgeted_quantity"] > 0:
            project_totals["percent_complete_quantity"] = (project_totals["earned_quantity"] / project_totals["budgeted_quantity"]) * 100
        else:
            project_totals["percent_complete_quantity"] = 0
        if project_totals["budgeted_hours"] > 0:
            project_totals["percent_complete_hours"] = (project_totals["earned_hours"] / project_totals["budgeted_hours"]) * 100
        else:
            project_totals["percent_complete_hours"] = 0

        report_data = {
            "project": project,
            "sub_job": sub_job,
            "grouped_work_items": grouped_work_items,
            "project_totals": project_totals,
            "report_date": datetime.now().strftime("%d-%b-%y"),
            "logo_base64": self.logo_base64
        }
        
        return report_data, None

    def generate_pdf_report(self, report_data, template_name, output_path):
        env = Environment(loader=FileSystemLoader(self.template_dir))
        template = env.get_template(template_name)
        html_out = template.render(report_data)
        
        # Add page numbers using WeasyPrint CSS features
        css_string = """
        @page {
            size: letter landscape;
            margin: 0.5in;
            @bottom-right {
                content: "Page " counter(page) " of " counter(pages);
                font-size: 9pt;
            }
        }
        """
        
        HTML(string=html_out).write_pdf(output_path, stylesheets=[CSS(string=css_string)])
        print(f"Generated PDF report: {output_path}")

    def _get_report_data(self, project_id_str, sub_job_id_str=None):
        """
        Get report data for a project or sub-job.
        
        Args:
            project_id_str (str): Project ID string
            sub_job_id_str (str, optional): Sub-job ID string. Defaults to None.
            
        Returns:
            tuple: (report_data, error) where report_data is a dict and error is a string or None
        """
        try:
            cursor = self.conn.cursor()
            
            # Get project
            cursor.execute("SELECT * FROM projects WHERE project_id_str = ?", (project_id_str,))
            project_row = cursor.fetchone()
            if not project_row:
                return None, f"Project with ID {project_id_str} not found"
            
            project = Project(
                id=project_row["id"],
                project_id_str=project_row["project_id_str"],
                name=project_row["name"]
            )
            
            # Get sub-job if specified
            sub_job = None
            if sub_job_id_str:
                cursor.execute("SELECT * FROM sub_jobs WHERE sub_job_id_str = ? AND project_id = ?", 
                              (sub_job_id_str, project.id))
                sub_job_row = cursor.fetchone()
                if not sub_job_row:
                    return None, f"Sub-job with ID {sub_job_id_str} not found in project {project_id_str}"
                
                sub_job = SubJob(
                    id=sub_job_row["id"],
                    project_id=sub_job_row["project_id"],
                    sub_job_id_str=sub_job_row["sub_job_id_str"],
                    name=sub_job_row["name"]
                )
            
            # Get all work items
            all_work_items = []
            if sub_job:
                cursor.execute("SELECT * FROM work_items WHERE sub_job_id = ?", (sub_job.id,))
            else:
                cursor.execute("""
                    SELECT wi.* FROM work_items wi
                    JOIN sub_jobs sj ON wi.sub_job_id = sj.id
                    WHERE sj.project_id = ?
                """, (project.id,))
            
            work_item_rows = cursor.fetchall()
            for row in work_item_rows:
                work_item = WorkItem(
                    id=row["id"],
                    project_id=row["project_id"] if "project_id" in row else project.id,
                    sub_job_id=row["sub_job_id"],
                    cost_code_id=row["cost_code_id"],
                    work_item_id_str=row["work_item_id_str"],
                    description=row["description"],
                    budgeted_quantity=row["budgeted_quantity"],
                    earned_quantity=row["earned_quantity"],
                    percent_complete_quantity=row["percent_complete_quantity"],
                    budgeted_man_hours=row["budgeted_man_hours"],
                    earned_man_hours=row["earned_man_hours"],
                    percent_complete_hours=row["percent_complete_hours"],
                    unit_of_measure=row["unit_of_measure"],
                    progress_json=row["progress_json"]
                )
                all_work_items.append(work_item)
            
            # Get all cost codes and rules of credit
            # Get cost codes used in this project's work items
            if sub_job:
                cursor.execute("""
                    SELECT DISTINCT cc.* 
                    FROM cost_codes cc
                    JOIN work_items wi ON wi.cost_code_id = cc.id
                    WHERE wi.sub_job_id = ?
                """, (sub_job.id,))
            else:
                cursor.execute("""
                    SELECT DISTINCT cc.* 
                    FROM cost_codes cc
                    JOIN work_items wi ON wi.cost_code_id = cc.id
                    JOIN sub_jobs sj ON wi.sub_job_id = sj.id
                    WHERE sj.project_id = ?
                """, (project.id,))
            
            cost_code_rows = cursor.fetchall()
            cost_codes = {}
            for row in cost_code_rows:
                # Check if rule_of_credit_id exists in the row
                rule_of_credit_id = None
                if "rule_of_credit_id" in row.keys():
                    rule_of_credit_id = row["rule_of_credit_id"]
                
                cost_codes[row["id"]] = CostCode(
                    id=row["id"],
                    project_id=project.id,  # Associate with current project
                    cost_code_id_str=row["cost_code_id_str"],
                    description=row["description"],
                    discipline=row["discipline"],
                    rule_of_credit_id=rule_of_credit_id
                )
            
            cursor.execute("SELECT * FROM rules_of_credit")
            roc_rows = cursor.fetchall()
            rules_of_credit = {}
            for row in roc_rows:
                rules_of_credit[row["id"]] = RuleOfCredit(
                    id=row["id"],
                    name=row["name"],
                    steps_json=row["steps_json"]
                )
            
            # Group work items by discipline and cost code
            grouped_work_items = {}
            project_totals = {
                "budgeted_quantity": 0,
                "earned_quantity": 0,
                "budgeted_hours": 0,
                "earned_hours": 0,
                "percent_complete_quantity": 0,
                "percent_complete_hours": 0
            }
            
            # Group by discipline and cost code
            for discipline_name in set(cc.discipline for cc in cost_codes.values() if cc.discipline):
                grouped_work_items[discipline_name] = {
                    "subtotals": {
                        "budgeted_quantity": 0,
                        "earned_quantity": 0,
                        "budgeted_hours": 0,
                        "earned_hours": 0,
                        "percent_complete_quantity": 0,
                        "percent_complete_hours": 0
                    },
                    "cost_codes": {}
                }
            
            # Add "Unassigned" discipline if needed
            if "Unassigned" not in grouped_work_items:
                grouped_work_items["Unassigned"] = {
                    "subtotals": {
                        "budgeted_quantity": 0,
                        "earned_quantity": 0,
                        "budgeted_hours": 0,
                        "earned_hours": 0,
                        "percent_complete_quantity": 0,
                        "percent_complete_hours": 0
                    },
                    "cost_codes": {}
                }
            
            # Process cost codes
            for cc_id, cost_code_obj in cost_codes.items():
                discipline_name = cost_code_obj.discipline if cost_code_obj.discipline else "Unassigned"
                cost_code_str = cost_code_obj.cost_code_id_str
                
                if discipline_name not in grouped_work_items:
                    grouped_work_items[discipline_name] = {
                        "subtotals": {
                            "budgeted_quantity": 0,
                            "earned_quantity": 0,
                            "budgeted_hours": 0,
                            "earned_hours": 0,
                            "percent_complete_quantity": 0,
                            "percent_complete_hours": 0
                        },
                        "cost_codes": {}
                    }
                
                if cost_code_str not in grouped_work_items[discipline_name]["cost_codes"]:
                    # Determine RoC step headers for this specific cost code
                    current_roc_step_names = []
                    if cost_code_obj.rule_of_credit_id and cost_code_obj.rule_of_credit_id in rules_of_credit:
                        roc = rules_of_credit[cost_code_obj.rule_of_credit_id]
                        try:
                            roc_data = json.loads(roc.steps_json)
                            if isinstance(roc_data, dict) and "steps" in roc_data:
                                current_roc_step_names = [step.get("name", f"Step {i+1}") for i, step in enumerate(roc_data["steps"])]
                        except (json.JSONDecodeError, TypeError, KeyError) as e:
                            print(f"Error parsing RoC steps for cost code {cost_code_obj.id}: {e}")
                    
                    # Ensure exactly 7 headers, padding with empty strings if fewer than 7 steps
                    padded_roc_step_names = (current_roc_step_names + ["" for _ in range(7)])[:7]

                    grouped_work_items[discipline_name]["cost_codes"][cost_code_str] = {
                        "work_items": [],
                        "roc_step_headers": padded_roc_step_names, # Cost-code specific RoC headers
                        "subtotals": {
                            "budgeted_quantity": 0,
                            "earned_quantity": 0,
                            "budgeted_hours": 0,
                            "earned_hours": 0,
                            "percent_complete_quantity": 0,
                            "percent_complete_hours": 0
                        }
                    }

                cost_code_group = grouped_work_items[discipline_name]["cost_codes"][cost_code_str]
                discipline_group_subtotals = grouped_work_items[discipline_name]["subtotals"]

                for item in all_work_items:
                    if item.cost_code_id == cc_id:
                        cost_code_group["work_items"].append(item)
                        # Accumulate subtotals for cost code
                        cost_code_group["subtotals"]["budgeted_quantity"] += item.budgeted_quantity or 0
                        cost_code_group["subtotals"]["earned_quantity"] += item.earned_quantity or 0
                        cost_code_group["subtotals"]["budgeted_hours"] += item.budgeted_man_hours or 0
                        cost_code_group["subtotals"]["earned_hours"] += item.earned_man_hours or 0
                
                # Calculate percent complete for cost code subtotals
                if cost_code_group["subtotals"]["budgeted_quantity"] > 0:
                    cost_code_group["subtotals"]["percent_complete_quantity"] = (cost_code_group["subtotals"]["earned_quantity"] / cost_code_group["subtotals"]["budgeted_quantity"]) * 100
                else:
                    cost_code_group["subtotals"]["percent_complete_quantity"] = 0
                
                if cost_code_group["subtotals"]["budgeted_hours"] > 0:
                    cost_code_group["subtotals"]["percent_complete_hours"] = (cost_code_group["subtotals"]["earned_hours"] / cost_code_group["subtotals"]["budgeted_hours"]) * 100
                else:
                    cost_code_group["subtotals"]["percent_complete_hours"] = 0

                # Accumulate subtotals for discipline
                discipline_group_subtotals["budgeted_quantity"] += cost_code_group["subtotals"]["budgeted_quantity"]
                discipline_group_subtotals["earned_quantity"] += cost_code_group["subtotals"]["earned_quantity"]
                discipline_group_subtotals["budgeted_hours"] += cost_code_group["subtotals"]["budgeted_hours"]
                discipline_group_subtotals["earned_hours"] += cost_code_group["subtotals"]["earned_hours"]

            # Calculate percent complete for discipline subtotals and project totals
            for discipline_name in grouped_work_items:
                discipline_group_subtotals = grouped_work_items[discipline_name]["subtotals"]
                if discipline_group_subtotals["budgeted_quantity"] > 0:
                    discipline_group_subtotals["percent_complete_quantity"] = (discipline_group_subtotals["earned_quantity"] / discipline_group_subtotals["budgeted_quantity"]) * 100
                else:
                    discipline_group_subtotals["percent_complete_quantity"] = 0
                if discipline_group_subtotals["budgeted_hours"] > 0:
                    discipline_group_subtotals["percent_complete_hours"] = (discipline_group_subtotals["earned_hours"] / discipline_group_subtotals["budgeted_hours"]) * 100
                else:
                    discipline_group_subtotals["percent_complete_hours"] = 0
                
                project_totals["budgeted_quantity"] += discipline_group_subtotals["budgeted_quantity"]
                project_totals["earned_quantity"] += discipline_group_subtotals["earned_quantity"]
                project_totals["budgeted_hours"] += discipline_group_subtotals["budgeted_hours"]
                project_totals["earned_hours"] += discipline_group_subtotals["earned_hours"]

            if project_totals["budgeted_quantity"] > 0:
                project_totals["percent_complete_quantity"] = (project_totals["earned_quantity"] / project_totals["budgeted_quantity"]) * 100
            else:
                project_totals["percent_complete_quantity"] = 0
            if project_totals["budgeted_hours"] > 0:
                project_totals["percent_complete_hours"] = (project_totals["earned_hours"] / project_totals["budgeted_hours"]) * 100
            else:
                project_totals["percent_complete_hours"] = 0

            report_data = {
                "project": project,
                "sub_job": sub_job,
                "grouped_work_items": grouped_work_items,
                "project_totals": project_totals,
                "report_date": datetime.now().strftime("%d-%b-%y"),
                "logo_base64": self.logo_base64
            }
            
            return report_data, None
        except Exception as e:
            import traceback
            return None, f"Error getting report data: {str(e)}\n{traceback.format_exc()}"
            
    def generate_reports(self, project_id_str, sub_job_id_str, hours_pdf_path, quantities_pdf_path, excel_path):
        """
        Generate all reports (hours PDF, quantities PDF, and Excel) for a project or sub-job.
        
        Args:
            project_id_str (str): Project ID string
            sub_job_id_str (str): Sub-job ID string (optional, pass None for project-wide reports)
            hours_pdf_path (str): Path to save the hours PDF report
            quantities_pdf_path (str): Path to save the quantities PDF report
            excel_path (str): Path to save the Excel report
            
        Returns:
            tuple: (success, message) where success is a boolean and message is a string
        """
        try:
            # Get report data
            report_data, error = self._get_report_data(project_id_str, sub_job_id_str)
            if error:
                return False, error
                
            # Generate hours PDF report
            self.generate_pdf_report(report_data, "hours_report_template.html", hours_pdf_path)
            
            # Generate quantities PDF report
            self.generate_pdf_report(report_data, "quantities_report_template.html", quantities_pdf_path)
            
            # Generate Excel report
            self.generate_excel_report(report_data, excel_path)
            
            return True, "Reports generated successfully"
        except Exception as e:
            import traceback
            return False, f"Error generating reports: {str(e)}\n{traceback.format_exc()}"
    
    def generate_excel_report(self, report_data, output_path):
        all_items_for_excel = []
        for discipline, discipline_data in report_data["grouped_work_items"].items():
            for cost_code, cost_code_data in discipline_data["cost_codes"].items():
                roc_headers = cost_code_data["roc_step_headers"] # Cost-code specific RoC headers
                for item in cost_code_data["work_items"]:
                    excel_row = {
                        "Discipline": discipline,
                        "Cost Code": cost_code,
                        "Work Item ID": item.work_item_id_str,
                        "Description": item.description,
                        "UOM": item.unit_of_measure,
                        "Budgeted Quantity": item.budgeted_quantity or 0,
                        "Earned Quantity": item.earned_quantity or 0,
                        "% Comp (Qty)": item.percent_complete_quantity or 0,
                        "Budgeted Hours": item.budgeted_man_hours or 0,
                        "Earned Hours": item.earned_man_hours or 0,
                        "% Comp (Hrs)": item.percent_complete_hours or 0,
                    }
                    for i, step_header in enumerate(roc_headers):
                        step_key = f"RoC Step {i+1}: {step_header}" if step_header else f"RoC Step {i+1}"
                        excel_row[step_key] = item.roc_steps_progress.get(step_header, 0.0) if step_header else None 
                    all_items_for_excel.append(excel_row)

        df = pd.DataFrame(all_items_for_excel)
        
        # Reorder columns to have RoC steps at the end
        fixed_cols = ["Discipline", "Cost Code", "Work Item ID", "Description", "UOM", 
                      "Budgeted Quantity", "Earned Quantity", "% Comp (Qty)", 
                      "Budgeted Hours", "Earned Hours", "% Comp (Hrs)"]
        
        roc_cols_ordered = [] # Will store the actual RoC column names in order
        # Determine the maximum number of RoC steps present in the data to create headers
        max_roc_steps = 0 
        if df.empty:
            # if dataframe is empty, create 7 roc step columns
                roc_cols_ordered = [f"RoC Step {i+1}" for i in range(7)]
        else:
            # find existing RoC columns
            existing_roc_cols = [col for col in df.columns if col.startswith("RoC Step")]
            max_roc_steps = 0
            if existing_roc_cols:
                # Extract step numbers and find the max
                step_numbers = []
                for col_name in existing_roc_cols:
                    try:
                        # Attempt to extract number like "RoC Step 1: Step Name"
                        step_num = int(col_name.split(":")[0].replace("RoC Step ", "").strip())
                        step_numbers.append(step_num)
                    except Exception:
                        pass # Catch all exceptions for now
                
                if step_numbers:
                    max_roc_steps = max(step_numbers)
                    roc_cols_ordered = [f"RoC Step {i+1}" for i in range(max_roc_steps)]
                else:
                    roc_cols_ordered = [f"RoC Step {i+1}" for i in range(7)]
            else:
                roc_cols_ordered = [f"RoC Step {i+1}" for i in range(7)]
                
        # Reorder columns with fixed columns first, then RoC step columns
        all_cols = []
        for col in fixed_cols:
            if col in df.columns:
                all_cols.append(col)
                
        # Add RoC step columns in order
        for col in df.columns:
            if col.startswith("RoC Step"):
                all_cols.append(col)
                
        # Reorder DataFrame columns
        if not df.empty and all_cols:
            df = df[all_cols]
            
        # Write DataFrame to Excel file
        df.to_excel(output_path, index=False)
        print(f"Generated Excel report: {output_path}")