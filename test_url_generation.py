from flask import url_for
from simple_app import create_app

app = create_app()

with app.test_request_context():
    print("=== URL Generation Test ===")
    print("Normal URL (no parameters):", url_for('main.add_work_item'))
    
    try:
        print("With sub_job_id as URL parameter:", url_for('main.add_work_item', sub_job_id=1))
    except Exception as e:
        print("Error with URL parameter:", str(e))
    
    # Test the correct way (query parameter)
    correct_url = url_for('main.add_work_item') + "?sub_job_id=1"
    print("With sub_job_id as query parameter:", correct_url)
    
    print("\n=== Route Definition Check ===")
    for rule in app.url_map.iter_rules():
        if "add_work_item" in rule.endpoint:
            print(f"Route: {rule}")
            print(f"Endpoint: {rule.endpoint}")
            print(f"Arguments: {list(rule.arguments)}")
            print(f"Defaults: {rule.defaults}")
