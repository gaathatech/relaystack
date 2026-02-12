"""
WSGI entry point for production deployment
Use with gunicorn: gunicorn wsgi:app
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app import create_app

# Create application
app = create_app(os.environ.get('FLASK_ENV', 'production'))

if __name__ == "__main__":
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 8000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    app.run(host=host, port=port, debug=debug)
