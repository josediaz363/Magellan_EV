import os
from . import create_app
app = create_app()
if __name__ == '__main__':
    # This is for local execution if needed, though the deployment service will use its own server.
    # Ensure debug is False for anything resembling production.
    port = int(os.environ.get("PORT", 5002)) # Changed default to 5002 to avoid common conflicts
    app.run(host='0.0.0.0', port=port, debug=False)

