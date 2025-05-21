from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import uuid

db = SQLAlchemy()

# Discipline choices for cost codes
DISCIPLINE_CHOICES = [
    'Civil',
    'Structural',
    'Mechanical',
    'Electrical',
    'Instrumentation',
    'Piping',
    'HVAC',
    'Architectural',
    'Other'
]

# Status choices for work items
STATUS_CHOICES = [
    'not_started',
    'in_progress',
    'completed',
    'on_hold'
]

class Project(db.Model):
    """Project model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    project_id_str = db.Column(db.String(20), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sub_jobs = db.relationship('SubJob', backref='project', lazy=True)
    cost_codes = db.relationship('CostCode', backref='project', lazy=True)
    work_items = db.relationship('WorkItem', backref='project', lazy=True)

class SubJob(db.Model):
    """Sub Job model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    area = db.Column(db.String(100), nullable=True)
    sub_job_id_str = db.Column(db.String(20), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    
    # Relationships
    work_items = db.relationship('WorkItem', backref='sub_job', lazy=True)

class RuleOfCredit(db.Model):
    """Rule of Credit model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    steps_json = db.Column(db.Text, nullable=False, default='[]')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    cost_codes = db.relationship('CostCode', backref='rule_of_credit', lazy=True)
    
    def get_steps(self):
        """Get steps as a list of dictionaries"""
        try:
            return json.loads(self.steps_json)
        except:
            return []
    
    def set_steps(self, steps):
        """Set steps from a list of dictionaries"""
        self.steps_json = json.dumps(steps)

class CostCode(db.Model):
    """Cost Code model"""
    id = db.Column(db.Integer, primary_key=True)
    cost_code_id_str = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    discipline = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    rule_of_credit_id = db.Column(db.Integer, db.ForeignKey('rule_of_credit.id'), nullable=True)
    
    # Relationships
    work_items = db.relationship('WorkItem', backref='cost_code', lazy=True)

class WorkItem(db.Model):
    """Work Item model"""
    id = db.Column(db.Integer, primary_key=True)
    work_item_id_str = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    budgeted_quantity = db.Column(db.Float, default=0)
    earned_quantity = db.Column(db.Float, default=0)
    unit_of_measure = db.Column(db.String(20), nullable=True)
    budgeted_man_hours = db.Column(db.Float, default=0)
    earned_man_hours = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='not_started')
    progress_json = db.Column(db.Text, nullable=False, default='{}')
    
    # Planned completion tracking fields
    planned_start_date = db.Column(db.Date, nullable=True)
    planned_end_date = db.Column(db.Date, nullable=True)
    actual_start_date = db.Column(db.Date, nullable=True)
    actual_end_date = db.Column(db.Date, nullable=True)
    planned_percent_complete = db.Column(db.Float, default=0)  # Planned % complete as of today
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    sub_job_id = db.Column(db.Integer, db.ForeignKey('sub_job.id'), nullable=False)
    cost_code_id = db.Column(db.Integer, db.ForeignKey('cost_code.id'), nullable=False)
    
    @property
    def percent_complete_quantity(self):
        """Calculate percent complete based on quantity"""
        if self.budgeted_quantity == 0:
            return 0
        return min(100, (self.earned_quantity / self.budgeted_quantity) * 100)
    
    @property
    def percent_complete_hours(self):
        """Calculate percent complete based on hours"""
        if self.budgeted_man_hours == 0:
            return 0
        return min(100, (self.earned_man_hours / self.budgeted_man_hours) * 100)
    
    @property
    def variance_percent(self):
        """Calculate variance between actual and planned percent complete"""
        actual = self.percent_complete_hours  # Using hours as the primary metric
        return actual - self.planned_percent_complete
    
    @property
    def is_behind_schedule(self):
        """Check if work item is behind schedule"""
        return self.variance_percent < -5  # More than 5% behind is considered behind schedule
    
    @property
    def is_on_schedule(self):
        """Check if work item is on schedule"""
        return abs(self.variance_percent) <= 5  # Within 5% is considered on schedule
    
    @property
    def is_ahead_schedule(self):
        """Check if work item is ahead of schedule"""
        return self.variance_percent > 5  # More than 5% ahead is considered ahead of schedule
    
    def get_steps_progress(self):
        """Get progress for each step as a dictionary"""
        try:
            return json.loads(self.progress_json)
        except:
            return {}
    
    def update_progress_step(self, step_name, progress_value):
        """Update progress for a specific step"""
        progress_data = self.get_steps_progress()
        progress_data[step_name] = progress_value
        self.progress_json = json.dumps(progress_data)
        
        # Recalculate earned values
        self.calculate_earned_values()
    
    def calculate_earned_values(self):
        """Calculate earned values based on progress and rule of credit"""
        if not self.cost_code or not self.cost_code.rule_of_credit:
            return
        
        steps = self.cost_code.rule_of_credit.get_steps()
        progress_data = self.get_steps_progress()
        
        total_weighted_progress = 0
        total_weight = 0
        
        for step in steps:
            step_name = step.get('name')
            step_weight = step.get('weight', 0)
            
            if step_name in progress_data:
                step_progress = progress_data[step_name]
                total_weighted_progress += (step_progress * step_weight)
                total_weight += step_weight
        
        if total_weight > 0:
            overall_progress = total_weighted_progress / total_weight
            overall_progress_decimal = overall_progress / 100  # Convert to decimal
            
            # Update earned values
            self.earned_quantity = self.budgeted_quantity * overall_progress_decimal
            self.earned_man_hours = self.budgeted_man_hours * overall_progress_decimal
            
            # Update status if needed
            if overall_progress >= 100 and self.status != 'completed':
                self.status = 'completed'
                self.actual_end_date = datetime.utcnow().date()
            elif overall_progress > 0 and self.status == 'not_started':
                self.status = 'in_progress'
                if not self.actual_start_date:
                    self.actual_start_date = datetime.utcnow().date()
