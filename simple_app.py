from flask import Flask, render_template, Blueprint

# Create a blueprint
main_bp = Blueprint('main', __name__)

# Define routes on the blueprint
@main_bp.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

@main_bp.route('/projects')
def projects():
    try:
        return render_template('view_project.html')
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

@main_bp.route('/reports')
def reports():
    try:
        return render_template('reports.html')
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

# Add the missing route
@main_bp.route('/list_cost_codes')
def list_cost_codes():
    try:
        return render_template('list_cost_codes.html')
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

# Create the Flask app
app = Flask(__name__)

# Register the blueprint
app.register_blueprint(main_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
