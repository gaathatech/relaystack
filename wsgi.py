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
    app.run()
