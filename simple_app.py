from flask import Flask, render_template, render_template_string

app = Flask(__name__)

@app.route('/')
def index():
    try:
        # Enhanced template with basic styling and navigation
        enhanced_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Magellan EV Tracker</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f3f3f3;
                }
                .header {
                    background-color: #0078D4;
                    color: white;
                    padding: 15px;
                    text-align: center;
                }
                .container {
                    padding: 20px;
                }
                .nav {
                    background-color: #f8f8f8;
                    padding: 10px;
                    border-bottom: 1px solid #ddd;
                }
                .nav a {
                    margin-right: 15px;
                    text-decoration: none;
                    color: #0078D4;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Magellan EV Tracker</h1>
            </div>
            <div class="nav">
                <a href="/">Dashboard</a>
                <a href="/projects">Projects</a>
                <a href="/reports">Reports</a>
            </div>
            <div class="container">
                <h2>Welcome to Magellan EV Tracker</h2>
                <p>This is the enhanced template with basic styling. We'll continue adding more features incrementally.</p>
            </div>
        </body>
        </html>
        """
        return render_template_string(enhanced_template)
    except Exception as e:
        # Return the error message for debugging
        return f"An error occurred: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
