import os
from __init__ import create_app  # Changed from relative to absolute import
app = create_app()
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5002))
    app.run(host='0.0.0.0', port=port, debug=False)
