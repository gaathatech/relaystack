"""
Nexora Investments - WhatsApp Business Chatbot
Entry point for Flask application
"""

import os
from dotenv import load_dotenv
from app import create_app

# Load environment variables from .env file
load_dotenv()

# Create Flask application
app = create_app()

if __name__ == '__main__':
    # Get debug mode from environment
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 8000))
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
