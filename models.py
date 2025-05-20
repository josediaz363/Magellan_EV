from flask_sqlalchemy import SQLAlchemy
import json

# Initialize SQLAlchemy
db = SQLAlchemy()

# Define database models
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description
        }

class RuleOfCredit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    steps_json = db.Column(db.Text, default="[]")  # JSON string to store steps and weights
    
    def get_steps(self):
        """Return steps as a Python list of dictionaries"""
        try:
            return json.loads(self.steps_json)
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
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False, unique=True)
    description = db.Column(db.String(200))
    
    def serialize(self):
        return {
            "id": self.id,
            "code": self.code,
            "description": self.description
        }

class WorkItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    cost_code_id = db.Column(db.Integer, db.ForeignKey('cost_code.id'), nullable=True)
    description = db.Column(db.Text)
    manhours = db.Column(db.Float, default=0)
    quantity = db.Column(db.Float, default=0)
    unit_of_measure = db.Column(db.String(50))
    percent_complete = db.Column(db.Float, default=0)
    rule_of_credit_id = db.Column(db.Integer, db.ForeignKey('rule_of_credit.id'), nullable=True)
    steps_progress_json = db.Column(db.Text, default="{}")  # JSON string to store step progress
    
    # Define relationships
    project = db.relationship('Project', backref=db.backref('work_items', lazy=True))
    cost_code = db.relationship('CostCode', backref=db.backref('work_items', lazy=True))
    rule_of_credit = db.relationship('RuleOfCredit', backref=db.backref('work_items', lazy=True))
    
    def get_steps_progress(self):
        """Return steps progress as a Python dictionary"""
        try:
            return json.loads(self.steps_progress_json)
        except:
            return {}
    
    def set_steps_progress(self, progress_dict):
        """Set steps progress from a dictionary"""
        self.steps_progress_json = json.dumps(progress_dict)
    
    def update_percent_complete(self):
        """Calculate percent complete based on rule of credit steps and their weights"""
        if not self.rule_of_credit:
            return
            
        steps = self.rule_of_credit.get_steps()
        progress = self.get_steps_progress()
        
        total_weighted_progress = 0
        for step in steps:
            step_name = step.get('name')
            step_weight = float(step.get('weight', 0))
            step_progress = float(progress.get(step_name, 0))
            total_weighted_progress += (step_weight * step_progress / 100)
        
        self.percent_complete = total_weighted_progress
    
    def serialize(self):
        return {
            "id": self.id,
            "description": self.description,
            "project_id": self.project_id,
            "cost_code_id": self.cost_code_id,
            "manhours": self.manhours,
            "quantity": self.quantity,
            "unit_of_measure": self.unit_of_measure,
            "percent_complete": self.percent_complete,
            "rule_of_credit_id": self.rule_of_credit_id,
            "steps_progress": self.get_steps_progress()
        }
