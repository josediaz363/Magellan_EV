from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    try:
        # Use your existing index.html template
        return render_template('index.html')
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

@app.route('/projects')
def projects():
    try:
        # Use your existing projects template
        return render_template('view_project.html')
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

@app.route('/reports')
def reports():
    try:
        # Use your existing reports template
        return render_template('reports.html')
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
