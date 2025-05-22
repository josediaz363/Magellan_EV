from flask import Flask
from routes import main_bp
from models import db
import os

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configure the SQLite database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///magellan_ev.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'magellan-ev-secret-key'  # Required for flash messages
    
    # Initialize the database with the app
    db.init_app(app)
    
    # Register the blueprint
    app.register_blueprint(main_bp)
    
    # Create database tables and add seed data if needed
    with app.app_context():
        db.create_all()
        
        # Check if we need to add seed data
        from models import Project
        if Project.query.count() == 0:
            # Add seed data for testing
            from datetime import datetime
            from models import Project, SubJob, CostCode, RuleOfCredit, RuleOfCreditStep, WorkItem
            
            # Create a sample project
            project = Project(
                project_id_str="PRJ-001",
                name="Sample Project",
                description="This is a sample project for testing",
                start_date=datetime.now(),
                end_date=datetime.now()
            )
            db.session.add(project)
            db.session.commit()
            
            # Create a sample sub job
            sub_job = SubJob(
                name="Phase 1",
                description="Initial phase of the project",
                project_id=project.id
            )
            db.session.add(sub_job)
            db.session.commit()
            
            # Create a sample rule of credit
            rule = RuleOfCredit(
                name="Standard Engineering",
                description="Standard rule of credit for engineering tasks"
            )
            db.session.add(rule)
            db.session.commit()
            
            # Add steps to the rule of credit
            steps = [
                RuleOfCreditStep(name="Planning", weight=15, rule_of_credit_id=rule.id),
                RuleOfCreditStep(name="Design", weight=25, rule_of_credit_id=rule.id),
                RuleOfCreditStep(name="Implementation", weight=40, rule_of_credit_id=rule.id),
                RuleOfCreditStep(name="Testing", weight=15, rule_of_credit_id=rule.id),
                RuleOfCreditStep(name="Documentation", weight=5, rule_of_credit_id=rule.id)
            ]
            for step in steps:
                db.session.add(step)
            db.session.commit()
            
            # Create a sample cost code
            cost_code = CostCode(
                code="ENG-001",
                description="Engineering Tasks",
                discipline="Engineering",
                rule_of_credit_id=rule.id
            )
            db.session.add(cost_code)
            db.session.commit()
            
            # Create a sample work item
            work_item = WorkItem(
                work_item_id="WI-001",
                description="Initial system design",
                uom="Hours",
                budgeted_quantity=100,
                earned_quantity=25,
                budgeted_hours=100,
                earned_hours=25,
                project_id=project.id,
                sub_job_id=sub_job.id,
                cost_code_id=cost_code.id
            )
            db.session.add(work_item)
            db.session.commit()
    
    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
