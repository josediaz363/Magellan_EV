from flask import Flask, render_template, render_template_string

app = Flask(__name__)

@app.route('/')
def index():
    try:
        # Start with a very basic template to test if Flask is working correctly
        basic_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Magellan EV Tracker</title>
        </head>
        <body>
            <h1>Magellan EV Tracker</h1>
            <p>Basic template working! We'll incrementally add more features.</p>
        </body>
        </html>
        """
        return render_template_string(basic_template)
    except Exception as e:
        # Return the error message for debugging
        return f"An error occurred: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
