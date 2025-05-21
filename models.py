from flask_sqlalchemy import SQLAlchemy
import json

# Initialize SQLAlchemy
db = SQLAlchemy()

# Allowed discipline values
DISCIPLINE_CHOICES = [
    ("Mechanical", "Mechanical"), 
    ("Electrical", "Electrical"), 
    ("Civil", "Civil"), 
    ("Steel", "Steel"), 
    ("Concrete", "Concrete"), 
    ("Piping", "Piping"), 
    ("Plumbing", "Plumbing"), 
    ("Fire", "Fire"), 
    ("Painting", "Painting"), 
    ("Roofing", "Roofing"), 
    ("Staff", "Staff"), 
    ("GC", "GC"), 
    ("Misc.", "Misc.")
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
    uom = db.Column(db.String(20))  # Unit of Measure
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
    rule_of_credit_id = db.Column(db.Integer, db.ForeignKey("rule_of_credit.id"), nullable=True)
    work_items = db.relationship("WorkItem", backref="cost_code", lazy=True)
    
    def get_discipline_display(self):
        """Return the display name for the discipline"""
        for value, display in DISCIPLINE_CHOICES:
            if value == self.discipline:
                return display
        return self.discipline
    
    def serialize(self):
        return {
            "id": self.id,
            "cost_code_id_str": self.cost_code_id_str,
            "description": self.description,
            "discipline": self.discipline,
            "uom": self.uom,
            "project_id": self.project_id,
            "rule_of_credit_id": self.rule_of_credit_id
        }

class WorkItem(db.Model):
    __tablename__ = "work_item"
    id = db.Column(db.Integer, primary_key=True)
    work_item_id_str = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    sub_job_id = db.Column(db.Integer, db.ForeignKey("sub_job.id"), nullable=False)
    cost_code_id = db.Column(db.Integer, db.ForeignKey("cost_code.id"), nullable=False)
    uom = db.Column(db.String(20))  # Unit of Measure
    budgeted_quantity = db.Column(db.Float, default=0.0)
    budgeted_hours = db.Column(db.Float, default=0.0)
    drawing_number = db.Column(db.String(100))
    activity_id = db.Column(db.String(100))
    deliverable = db.Column(db.String(200))
    notes = db.Column(db.Text)
    percent_complete = db.Column(db.Integer, default=0)
    earned_quantity = db.Column(db.Float, default=0.0)
    earned_hours = db.Column(db.Float, default=0.0)
    progress_json = db.Column(db.Text, default="[]")  # JSON string to store progress steps
    
    def get_progress_steps(self):
        """Return progress steps as a Python list of dictionaries"""
        try:
            return json.loads(self.progress_json or "[]")
        except:
            return []
    
    def set_progress_steps(self, steps_list):
        """Set progress steps from a list of dictionaries"""
        self.progress_json = json.dumps(steps_list)
    
    def serialize(self):
        return {
            "id": self.id,
            "work_item_id_str": self.work_item_id_str,
            "description": self.description,
            "sub_job_id": self.sub_job_id,
            "cost_code_id": self.cost_code_id,
            "uom": self.uom,
            "budgeted_quantity": self.budgeted_quantity,
            "budgeted_hours": self.budgeted_hours,
            "drawing_number": self.drawing_number,
            "activity_id": self.activity_id,
            "deliverable": self.deliverable,
            "notes": self.notes,
            "percent_complete": self.percent_complete,
            "earned_quantity": self.earned_quantity,
            "earned_hours": self.earned_hours,
            "progress_steps": self.get_progress_steps()
        }
