from models import db, Project
from app import create_app

app = create_app()
with app.app_context():
    projects = Project.query.all()
    print(f'Number of projects: {len(projects)}')
    for p in projects:
        print(f'Project ID: {p.id}, Name: {p.name}')
