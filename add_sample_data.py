from simple_app import create_app, db
from models import Project, SubJob, CostCode, RuleOfCredit, WorkItem
import json
from datetime import datetime, timedelta

app = create_app()
with app.app_context():
    # Create a project
    project = Project(
        name='Demo Project',
        project_id_str='PRJ-001',
        description='Demo project for testing'
    )
    db.session.add(project)
    db.session.commit()
    
    # Create sub jobs
    sub_job1 = SubJob(
        name='Foundation Work',
        description='All foundation related activities',
        area='Area A',
        sub_job_id_str='SJ-001',
        project_id=project.id
    )
    
    sub_job2 = SubJob(
        name='Structural Work',
        description='All structural related activities',
        area='Area B',
        sub_job_id_str='SJ-002',
        project_id=project.id
    )
    
    db.session.add_all([sub_job1, sub_job2])
    db.session.commit()
    
    # Create rules of credit
    roc1 = RuleOfCredit(
        name='Concrete FREP',
        description='Rule of credit for concrete work',
        steps_json=json.dumps([
            {"name": "Form", "weight": 15},
            {"name": "Rebar", "weight": 20},
            {"name": "Embeds", "weight": 20},
            {"name": "Pour", "weight": 40},
            {"name": "QC", "weight": 5}
        ])
    )
    
    roc2 = RuleOfCredit(
        name='Structural Steel',
        description='Rule of credit for structural steel work',
        steps_json=json.dumps([
            {"name": "Layout", "weight": 10},
            {"name": "Erection", "weight": 40},
            {"name": "Plumb & Align", "weight": 20},
            {"name": "Bolt-up", "weight": 20},
            {"name": "QC", "weight": 10}
        ])
    )
    
    db.session.add_all([roc1, roc2])
    db.session.commit()
    
    # Create cost codes
    cc1 = CostCode(
        cost_code_id_str='CC-001',
        description='Concrete Foundation',
        discipline='Civil',
        project_id=project.id,
        rule_of_credit_id=roc1.id
    )
    
    cc2 = CostCode(
        cost_code_id_str='CC-002',
        description='Steel Columns',
        discipline='Structural',
        project_id=project.id,
        rule_of_credit_id=roc2.id
    )
    
    db.session.add_all([cc1, cc2])
    db.session.commit()
    
    # Create work items with various statuses and progress
    today = datetime.now().date()
    
    # Work item 1 - Not started
    wi1 = WorkItem(
        work_item_id_str='WI-001',
        description='Column Foundation F1',
        budgeted_quantity=100,
        earned_quantity=0,
        unit_of_measure='CY',
        budgeted_man_hours=200,
        earned_man_hours=0,
        status='not_started',
        planned_start_date=today + timedelta(days=5),
        planned_end_date=today + timedelta(days=15),
        planned_percent_complete=0,
        project_id=project.id,
        sub_job_id=sub_job1.id,
        cost_code_id=cc1.id
    )
    
    # Work item 2 - In progress
    wi2 = WorkItem(
        work_item_id_str='WI-002',
        description='Column Foundation F2',
        budgeted_quantity=120,
        earned_quantity=60,
        unit_of_measure='CY',
        budgeted_man_hours=240,
        earned_man_hours=120,
        status='in_progress',
        planned_start_date=today - timedelta(days=10),
        planned_end_date=today + timedelta(days=5),
        actual_start_date=today - timedelta(days=10),
        planned_percent_complete=60,
        project_id=project.id,
        sub_job_id=sub_job1.id,
        cost_code_id=cc1.id,
        progress_json=json.dumps({
            "Form": 100,
            "Rebar": 100,
            "Embeds": 75,
            "Pour": 0,
            "QC": 0
        })
    )
    
    # Work item 3 - Completed
    wi3 = WorkItem(
        work_item_id_str='WI-003',
        description='Steel Column C1',
        budgeted_quantity=50,
        earned_quantity=50,
        unit_of_measure='EA',
        budgeted_man_hours=150,
        earned_man_hours=150,
        status='completed',
        planned_start_date=today - timedelta(days=20),
        planned_end_date=today - timedelta(days=5),
        actual_start_date=today - timedelta(days=20),
        actual_end_date=today - timedelta(days=5),
        planned_percent_complete=100,
        project_id=project.id,
        sub_job_id=sub_job2.id,
        cost_code_id=cc2.id,
        progress_json=json.dumps({
            "Layout": 100,
            "Erection": 100,
            "Plumb & Align": 100,
            "Bolt-up": 100,
            "QC": 100
        })
    )
    
    # Work item 4 - Behind schedule
    wi4 = WorkItem(
        work_item_id_str='WI-004',
        description='Steel Column C2',
        budgeted_quantity=50,
        earned_quantity=15,
        unit_of_measure='EA',
        budgeted_man_hours=150,
        earned_man_hours=45,
        status='in_progress',
        planned_start_date=today - timedelta(days=15),
        planned_end_date=today + timedelta(days=5),
        actual_start_date=today - timedelta(days=10),
        planned_percent_complete=60,
        project_id=project.id,
        sub_job_id=sub_job2.id,
        cost_code_id=cc2.id,
        progress_json=json.dumps({
            "Layout": 100,
            "Erection": 30,
            "Plumb & Align": 0,
            "Bolt-up": 0,
            "QC": 0
        })
    )
    
    # Work item 5 - On hold
    wi5 = WorkItem(
        work_item_id_str='WI-005',
        description='Column Foundation F3',
        budgeted_quantity=80,
        earned_quantity=40,
        unit_of_measure='CY',
        budgeted_man_hours=160,
        earned_man_hours=80,
        status='on_hold',
        planned_start_date=today - timedelta(days=5),
        planned_end_date=today + timedelta(days=10),
        actual_start_date=today - timedelta(days=5),
        planned_percent_complete=50,
        project_id=project.id,
        sub_job_id=sub_job1.id,
        cost_code_id=cc1.id,
        progress_json=json.dumps({
            "Form": 100,
            "Rebar": 100,
            "Embeds": 0,
            "Pour": 0,
            "QC": 0
        })
    )
    
    db.session.add_all([wi1, wi2, wi3, wi4, wi5])
    db.session.commit()
    
    print('Sample data added successfully.')
