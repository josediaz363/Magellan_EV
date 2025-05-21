from flask_sqlalchemy import SQLAlchemy
import json

# Initialize SQLAlchemy
db = SQLAlchemy()

# Allowed discipline values
DISCIPLINE_CHOICES = [
    "Mechanical", "Electrical", "Civil", "Steel", "Concrete", 
    "Piping", "Plumbing", "Fire", "Painting", "Roofing", 
    "Staff", "GC", "Misc."
]

# Define database models
class Project(db.Model):
    __tablename__ = "project"
    id = db.Column(db.Integer, primary_key=True)
    project_id_str = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    sub_jobs = db.relationship("SubJob", backref="project", lazy=True, cascade="all, delete-orphan")
    
    def serialize(self):
        return {
            "id": self.id,
            "project_id_str": self.project_id_str,
            "name": self.name,
            "description": self.description
        }
    
    def serialize_with_subjobs_and_workitems(self):
        return {
            "id": self.id,
            "project_id_str": self.project_id_str,
            "name": self.name,
            "description": self.description,
            "sub_jobs": [sj.serialize_with_workitems() for sj in self.sub_jobs]
        }

class SubJob(db.Model):
    __tablename__ = "sub_job"
    id = db.Column(db.Integer, primary_key=True)
    sub_job_id_str = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
    work_items = db.relationship("WorkItem", backref="sub_job", lazy=True, cascade="all, delete-orphan")
    area = db.Column(db.String(100))

    def serialize(self):
        return {
            "id": self.id,
            "sub_job_id_str": self.sub_job_id_str,
            "name": self.name,
            "description": self.description,
            "project_id": self.project_id,
            "area": self.area
        }

    def serialize_with_workitems(self):
        return {
            "id": self.id,
            "sub_job_id_str": self.sub_job_id_str,
            "name": self.name,
            "description": self.description,
            "project_id": self.project_id,
            "area": self.area,
            "work_items": [wi.serialize() for wi in self.work_items]
        }

class RuleOfCredit(db.Model):
    __tablename__ = "rule_of_credit"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    steps_json = db.Column(db.Text, default="[]")  # JSON string to store steps and weights
    cost_codes = db.relationship("CostCode", backref="rule_of_credit", lazy=True)
    
    def get_steps(self):
        """Return steps as a Python list of dictionaries"""
        try:
            rule_data = json.loads(self.steps_json or "[]")
            if isinstance(rule_data, dict) and "steps" in rule_data:
                return rule_data["steps"]
            elif isinstance(rule_data, list):
                return rule_data
            return []
        except:
            return []
    
    def set_steps(self, steps_list):
        """Set steps from a list of dictionaries with name and weight"""
        self.steps_json = json.dumps(steps_list)
    
    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "steps": self.get_steps()
        }

class CostCode(db.Model):
    __tablename__ = "cost_code"
    id = db.Column(db.Integer, primary_key=True)
    cost_code_id_str = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    discipline = db.Column(db.String(100), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
    rule_of_credit_id = db.Column(db.Integer, db.ForeignKey("rule_of_credit.id"), nullable=True)
    work_items = db.relationship("WorkItem", backref="cost_code", lazy=True)
    
    def serialize(self):
        return {
            "id": self.id,
            "cost_code_id_str": self.cost_code_id_str,
            "description": self.description,
            "discipline": self.discipline,
            "project_id": self.project_id,
            "rule_of_credit_id": self.rule_of_credit_id
        }

class WorkItem(db.Model):
    __tablename__ = "work_item"
    id = db.Column(db.Integer, primary_key=True)
    work_item_id_str = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
    sub_job_id = db.Column(db.Integer, db.ForeignKey("sub_job.id"), nullable=False)
    cost_code_id = db.Column(db.Integer, db.ForeignKey("cost_code.id"), nullable=False)
    budgeted_quantity = db.Column(db.Float)
    unit_of_measure = db.Column(db.String(20))
    budgeted_man_hours = db.Column(db.Float)
    progress_json = db.Column(db.Text, default="[]") # JSON string of step name and its % completion
    earned_man_hours = db.Column(db.Float, default=0.0)
    earned_quantity = db.Column(db.Float, default=0.0)
    percent_complete_hours = db.Column(db.Float, default=0.0)
    percent_complete_quantity = db.Column(db.Float, default=0.0)
    
    def get_steps_progress(self):
        """Return steps progress as a Python dictionary"""
        try:
            progress_data = {}
            current_progress_data = json.loads(self.progress_json or "[]")
            
            if isinstance(current_progress_data, list):
                for step_progress in current_progress_data:
                    if isinstance(step_progress, dict):
                        if "step_name" in step_progress and "current_complete_percentage" in step_progress:
                            progress_data[step_progress["step_name"]] = float(step_progress["current_complete_percentage"])
                        elif "name" in step_progress and "percentage" in step_progress:
                            progress_data[step_progress["name"]] = float(step_progress["percentage"])
            elif isinstance(current_progress_data, dict):
                progress_data = current_progress_data
            
            return progress_data
        except:
            return {}
    
    def set_steps_progress(self, progress_dict):
        """Set steps progress from a dictionary"""
        progress_list = []
        for step_name, percentage in progress_dict.items():
            progress_list.append({
                "step_name": step_name,
                "current_complete_percentage": float(percentage)
            })
        self.progress_json = json.dumps(progress_list)
    
    def update_progress_step(self, step_name_to_update, completion_percentage):
        """Update progress for a specific step"""
        try:
            progress_data = json.loads(self.progress_json or "[]")
            
            # Handle different progress_json formats
            if isinstance(progress_data, list):
                # Find and update the step if it exists
                step_found = False
                for step in progress_data:
                    if isinstance(step, dict):
                        if "step_name" in step and step["step_name"] == step_name_to_update:
                            step["current_complete_percentage"] = float(completion_percentage)
                            step_found = True
                            break
                        elif "name" in step and step["name"] == step_name_to_update:
                            step["percentage"] = float(completion_percentage)
                            step_found = True
                            break
                
                # If step not found, add it
                if not step_found:
                    progress_data.append({
                        "step_name": step_name_to_update,
                        "current_complete_percentage": float(completion_percentage)
                    })
            elif isinstance(progress_data, dict):
                # Legacy dictionary format
                progress_data[step_name_to_update] = float(completion_percentage)
            else:
                # Initialize as new format
                progress_data = [{
                    "step_name": step_name_to_update,
                    "current_complete_percentage": float(completion_percentage)
                }]
            
            self.progress_json = json.dumps(progress_data)
            self.calculate_earned_values()
        except Exception as e:
            print(f"Error updating progress step: {e}")
    
    def calculate_earned_values(self):
        """Calculate earned values based on rule of credit steps and their weights"""
        try:
            # Get the cost code and rule of credit
            cost_code = CostCode.query.get(self.cost_code_id)
            if not cost_code or not cost_code.rule_of_credit_id:
                self.earned_man_hours = 0
                self.percent_complete_hours = 0
                self.earned_quantity = 0
                self.percent_complete_quantity = 0
                return
            
            rule = RuleOfCredit.query.get(cost_code.rule_of_credit_id)
            if not rule:
                self.earned_man_hours = 0
                self.percent_complete_hours = 0
                self.earned_quantity = 0
                self.percent_complete_quantity = 0
                return

            # Parse rule steps
            parsed_rule_steps = []
            try:
                rule_data = json.loads(rule.steps_json)
                if isinstance(rule_data, dict) and "steps" in rule_data and isinstance(rule_data["steps"], list):
                    steps_list_from_json = rule_data["steps"]
                    for step_entry in steps_list_from_json:
                        if isinstance(step_entry, dict) and "name" in step_entry and "weight" in step_entry:
                            parsed_rule_steps.append({
                                "name": str(step_entry["name"]),
                                "weight": float(step_entry["weight"])
                            })
                elif isinstance(rule_data, list):  # Legacy format support
                    for step_entry in rule_data:
                        if isinstance(step_entry, dict) and "weight" in step_entry:
                            step_name_val = None
                            if "name" in step_entry:  # Legacy might have 'name'
                                step_name_val = str(step_entry["name"])
                            elif "step_name" in step_entry:  # Or 'step_name'
                                step_name_val = str(step_entry["step_name"])
                            
                            if step_name_val:
                                parsed_rule_steps.append({
                                    "name": step_name_val,
                                    "weight": float(step_entry["weight"])
                                })
            except json.JSONDecodeError:
                pass
            except Exception:
                pass

            # Get progress data
            progress_data = self.get_steps_progress()

            # Calculate weighted percentage
            total_weighted_percentage = 0
            for step_def in parsed_rule_steps:
                step_name_key = step_def.get("name")
                if not step_name_key:
                    continue
                
                step_weight = float(step_def.get("weight", 0.0))
                step_completion = float(progress_data.get(step_name_key, 0.0))
                
                total_weighted_percentage += (step_completion / 100.0) * step_weight

            # Calculate earned values
            if self.budgeted_man_hours and self.budgeted_man_hours > 0:
                self.earned_man_hours = (total_weighted_percentage / 100.0) * self.budgeted_man_hours
                self.percent_complete_hours = (self.earned_man_hours / self.budgeted_man_hours) * 100 if self.budgeted_man_hours != 0 else 0
            else:
                self.earned_man_hours = 0
                self.percent_complete_hours = 0

            if self.budgeted_quantity and self.budgeted_quantity > 0:
                self.earned_quantity = (total_weighted_percentage / 100.0) * self.budgeted_quantity
                self.percent_complete_quantity = (self.earned_quantity / self.budgeted_quantity) * 100 if self.budgeted_quantity != 0 else 0
            else:
                self.earned_quantity = 0
                self.percent_complete_quantity = 0
        except Exception as e:
            print(f"Error calculating earned values: {e}")
            self.earned_man_hours = 0
            self.percent_complete_hours = 0
            self.earned_quantity = 0
            self.percent_complete_quantity = 0
    
    def serialize(self):
        return {
            "id": self.id,
            "work_item_id_str": self.work_item_id_str,
            "description": self.description,
            "project_id": self.project_id,
            "sub_job_id": self.sub_job_id,
            "cost_code_id": self.cost_code_id,
            "budgeted_quantity": self.budgeted_quantity,
            "unit_of_measure": self.unit_of_measure,
            "budgeted_man_hours": self.budgeted_man_hours,
            "progress": json.loads(self.progress_json or "[]"),
            "earned_man_hours": self.earned_man_hours,
            "earned_quantity": self.earned_quantity,
            "percent_complete_hours": self.percent_complete_hours,
            "percent_complete_quantity": self.percent_complete_quantity
        }
