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
    work_items = db.relationship("WorkItem", backref="project", lazy=True)
    
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
    
    @property
    def all_work_items(self):
        """Get all work items for this project across all sub jobs"""
        items = []
        for sub_job in self.sub_jobs:
            items.extend(sub_job.work_items)
        return items
    
    @property
    def total_budgeted_hours(self):
        """Calculate total budgeted hours for all work items in this project"""
        return sum(item.budgeted_man_hours or 0 for item in self.work_items)
    
    @property
    def total_earned_hours(self):
        """Calculate total earned hours for all work items in this project"""
        return sum(item.earned_man_hours or 0 for item in self.work_items)
    
    @property
    def total_budgeted_quantity(self):
        """Calculate total budgeted quantity for all work items in this project"""
        # Note: This is a simplified approach as quantities might have different units
        return sum(item.budgeted_quantity or 0 for item in self.work_items)
    
    @property
    def total_earned_quantity(self):
        """Calculate total earned quantity for all work items in this project"""
        # Note: This is a simplified approach as quantities might have different units
        return sum(item.earned_quantity or 0 for item in self.work_items)
    
    @property
    def percent_complete(self):
        """Calculate overall percent complete for the project based on earned vs budgeted hours"""
        if self.total_budgeted_hours == 0:
            return 0
        return (self.total_earned_hours / self.total_budgeted_hours) * 100

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
    
    @property
    def total_budgeted_hours(self):
        """Calculate total budgeted hours for all work items in this sub job"""
        return sum(item.budgeted_man_hours or 0 for item in self.work_items)
    
    @property
    def total_earned_hours(self):
        """Calculate total earned hours for all work items in this sub job"""
        return sum(item.earned_man_hours or 0 for item in self.work_items)
    
    @property
    def total_budgeted_quantity(self):
        """Calculate total budgeted quantity for all work items in this sub job"""
        return sum(item.budgeted_quantity or 0 for item in self.work_items)
    
    @property
    def total_earned_quantity(self):
        """Calculate total earned quantity for all work items in this sub job"""
        return sum(item.earned_quantity or 0 for item in self.work_items)
    
    @property
    def percent_complete(self):
        """Calculate overall percent complete for the sub job based on earned vs budgeted hours"""
        if self.total_budgeted_hours == 0:
            return 0
        return (self.total_earned_hours / self.total_budgeted_hours) * 100

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
    rule_of_credit_id = db.Column(db.Integer, db.ForeignKey("rule_of_credit.id"), nullable=True)
    work_items = db.relationship("WorkItem", backref="cost_code", lazy=True)
    
    def serialize(self):
        return {
            "id": self.id,
            "cost_code_id_str": self.cost_code_id_str,
            "description": self.description,
            "discipline": self.discipline,
            "rule_of_credit_id": self.rule_of_credit_id
        }

class RuleOfCreditStep(db.Model):
    __tablename__ = "rule_of_credit_step"
    id = db.Column(db.Integer, primary_key=True)
    rule_of_credit_id = db.Column(db.Integer, db.ForeignKey("rule_of_credit.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    percentage = db.Column(db.Float, nullable=False)
    order = db.Column(db.Integer, nullable=False)
    
    def serialize(self):
        return {
            "id": self.id,
            "rule_of_credit_id": self.rule_of_credit_id,
            "name": self.name,
            "percentage": self.percentage,
            "order": self.order
        }

class WorkItem(db.Model):
    __tablename__ = "work_item"
    id = db.Column(db.Integer, primary_key=True)
    work_item_id_str = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
    sub_job_id = db.Column(db.Integer, db.ForeignKey("sub_job.id"), nullable=False)
    cost_code_id = db.Column(db.Integer, db.ForeignKey("cost_code.id"), nullable=True)
    budgeted_quantity = db.Column(db.Float)
    earned_quantity = db.Column(db.Float, default=0.0)
    unit_of_measure = db.Column(db.String(20))
    budgeted_hours = db.Column(db.Float)
    earned_hours = db.Column(db.Float, default=0.0)
    progress_data = db.Column(db.Text, default="{}")  # JSON string to store progress data
    
    def get_steps_progress(self):
        """Return progress data as a Python dictionary"""
        try:
            return json.loads(self.progress_data or "{}")
        except:
            return {}
    
    def set_progress_data(self, progress_dict):
        """Set progress data from a dictionary"""
        self.progress_data = json.dumps(progress_dict)
    
    def serialize(self):
        return {
            "id": self.id,
            "work_item_id_str": self.work_item_id_str,
            "description": self.description,
            "project_id": self.project_id,
            "sub_job_id": self.sub_job_id,
            "cost_code_id": self.cost_code_id,
            "budgeted_quantity": self.budgeted_quantity,
            "earned_quantity": self.earned_quantity,
            "unit_of_measure": self.unit_of_measure,
            "budgeted_hours": self.budgeted_hours,
            "earned_hours": self.earned_hours,
            "progress_data": self.get_steps_progress()
        }
