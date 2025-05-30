# Magellan EV Tracker v2.0 - Fixed Version

This package contains the Magellan EV Tracker v2.0 application with all fixes implemented for the parameter naming inconsistencies, cost code display issues, and template-route endpoint mismatches.

## Fixed Issues

1. **Parameter Naming Standardization**:
   - Consistently uses `sub_job` with underscores throughout the application
   - Updated routes.py to use `sub_job_service` instead of `subjob_service`
   - Standardized all parameter names to use `sub_job_id` consistently
   - Fixed URL generation for all sub job related routes

2. **Cost Code Display Issue**:
   - Modified the `list_cost_codes` route to pass `cost_codes` to the template instead of `costcodes_with_projects`
   - Ensures cost codes appear in the list view after creation

3. **Template-Route Endpoint Mismatch Fix**:
   - Added an alias route for `work_items` to match the template reference
   - Fixed the internal server error caused by URL building failure
   - Ensures all navigation links work correctly

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

For deployment to Railway.app:

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

To verify the fixes, please test:

1. Creating and viewing projects
2. Creating and viewing sub jobs
3. Creating cost codes and verifying they appear in the list
4. Navigating to the Work Items page via the sidebar
5. Creating work items for sub jobs

All workflows should function correctly with the implemented fixes.
