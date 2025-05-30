# Magellan EV Tracker v2.0 - Fixed Version

This package contains the fixed version of the Magellan EV Tracker application with the following issues resolved:

## Issues Fixed

1. **Parameter Naming Standardization**
   - Standardized on `sub_job_id` naming convention throughout the application
   - Updated all routes, services, and templates to use consistent parameter naming
   - Added backward compatibility aliases where needed

2. **Cost Code Service Fixes**
   - Improved session management with proper refresh and rollback
   - Enhanced relationship loading with joinedload for better performance
   - Fixed template variable names to match what's passed from routes
   - Added explicit error handling and transaction management

3. **Sub Job Dropdown Fixes**
   - Ensured sub jobs appear correctly in work item dropdown menus
   - Updated project_service.py with joinedload for better performance
   - Fixed filtering logic in add_work_item.html template

4. **Rule of Credit Functionality**
   - Fixed parameter naming in rule of credit routes
   - Updated edit_rule_of_credit.html template to use correct variable names
   - Ensured proper steps loading and saving

## Installation and Setup

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Initialize the database:
   ```
   python init_db.py
   ```

4. Run the application:
   ```
   python simple_app.py
   ```

## Directory Structure

- `services/`: Service layer for database operations
- `templates/`: HTML templates for the web interface
- `static/`: CSS, JavaScript, and image files
- `reports/`: Generated reports (created at runtime)
- `instance/`: Database files (created at runtime)
- `simple_app.py`: Main application entry point
- `models.py`: Database models
- `init_db.py`: Database initialization script
- `Procfile`: For deployment to Heroku or similar platforms

## Notes

- The application uses SQLite by default, stored in the `instance` directory
- The `reports` directory is created automatically when generating reports
- All fixes maintain backward compatibility with existing data

## Contact

For any issues or questions, please contact the Magellan EV Tracker development team.
