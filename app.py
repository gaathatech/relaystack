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

@app.route('/', methods=['GET'])
def index():
    """Health check endpoint"""
    return {
        'status': 'running',
        'service': 'Nexora WhatsApp Chatbot',
        'version': '1.0.0',
        'endpoints': {
            'webhook': '/webhook',
            'health': '/webhook/health',
            'stats': '/webhook/stats/<phone>'
        }
    }, 200

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'service': 'Nexora WhatsApp Chatbot'
    }, 200

if __name__ == '__main__':
    # Get debug mode from environment
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
