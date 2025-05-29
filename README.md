# Magellan EV Tracker v2.0 - Complete Package

This package contains the complete Magellan EV Tracker v2.0 application with all fixes implemented. The application allows tracking of projects, sub jobs, work items, and cost codes for construction project management.

## Implemented Fixes

This package includes three critical fixes:

1. **Parameter Naming Standardization**:
   - Consistently uses `sub_job` with underscores throughout the application
   - Updated service files, routes, and templates to use consistent naming

2. **Work Item URL Generation Fix**:
   - Fixed the URL generation in add_work_item.html to properly include the sub_job_id parameter
   - Resolves the error: "Could not build url for endpoint 'main.add_work_item'. Did you forget to specify values ['sub_job_id']?"

3. **Cost Code Relationship Loading Fix**:
   - Modified the `get_all_costcodes()` method to use SQLAlchemy's joinedload for proper relationship loading
   - Ensures cost codes appear in the list view after creation with proper project and rule of credit relationships

## Installation Instructions

1. Extract the contents of this package to your deployment directory
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python simple_app.py
   ```
   or
   ```
   flask run --host=0.0.0.0
   ```

## Deployment

For deployment to platforms like Railway.app:

1. Ensure the Procfile is included (it is in this package)
2. Deploy the entire package as is
3. Set any required environment variables on your deployment platform

## File Structure

- `app.py` - Main Flask application
- `simple_app.py` - Simplified entry point for running the application
- `models.py` - Database models
- `routes.py` - Application routes
- `services/` - Service layer for business logic
- `templates/` - HTML templates
- `static/` - Static assets (CSS, JS, images)
- `reports/` - Report generation
- `instance/` - Instance-specific configuration

## Testing

To test the application:

1. Create a project
2. Create a sub job within the project
3. Create a cost code and assign a rule of credit
4. Create a work item for the sub job
5. Update work item progress

All workflows should function correctly with the implemented fixes.
