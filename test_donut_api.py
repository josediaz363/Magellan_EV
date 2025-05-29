from models import db, Project
from app import create_app
import json

app = create_app()
with app.app_context():
    with app.test_client() as client:
        response = client.get('/api/visualizations/donut/1')
        print('Status code:', response.status_code)
        print('Response data:', response.data.decode('utf-8'))
