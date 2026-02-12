"""Flask application factory and initialization"""

from flask import Flask
from config import config
from app.models import db
import os

def create_app(config_name=None):
    """
    Application factory function
    
    Args:
        config_name: Configuration environment (development, production, testing)
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize database
    db.init_app(app)
    
    # Register blueprints
    from app.whatsapp import whatsapp_bp
    app.register_blueprint(whatsapp_bp)

    # Basic root endpoints (useful for tests and health checks)
    @app.route('/', methods=['GET'])
    def index():
        return {
            'status': 'running',
            'service': 'Nexora WhatsApp Chatbot'
        }, 200

    @app.route('/status', methods=['GET'])
    def status():
        return {'status': 'running'}, 200
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register CLI commands
    register_cli_commands(app)
    
    return app


def register_error_handlers(app):
    """Register error handlers for the application"""
    
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal server error'}, 500
    
    @app.errorhandler(403)
    def forbidden(error):
        return {'error': 'Forbidden'}, 403


def register_cli_commands(app):
    """Register CLI commands for database operations"""
    
    @app.cli.command()
    def init_db():
        """Initialize the database."""
        db.create_all()
        print('Database initialized.')
    
    @app.cli.command()
    def seed_programs():
        """Seed investment programs database."""
        from app.models import InvestmentProgram
        
        programs = [
            # Europe Golden Visa
            InvestmentProgram(
                country='Portugal',
                category='Europe Golden Visa',
                name='Portugal Golden Residency Program',
                description='Golden Visa through real estate investment',
                minimum_investment=280000,
                processing_time='3-4 months',
                link='https://nexorainvestments.com/portugal-golden-visa',
                rank=1
            ),
            InvestmentProgram(
                country='Greece',
                category='Europe Golden Visa',
                name='Greece Golden Visa - Real Estate',
                description='Residency visa through property purchase',
                minimum_investment=250000,
                processing_time='2-3 months',
                link='https://nexorainvestments.com/greece-golden-visa',
                rank=2
            ),
            InvestmentProgram(
                country='Spain',
                category='Europe Golden Visa',
                name='Spain Golden Visa Program',
                description='Investor visa program for Spain',
                minimum_investment=500000,
                processing_time='4-6 months',
                link='https://nexorainvestments.com/spain-golden-visa',
                rank=3
            ),
            
            # Caribbean Citizenship
            InvestmentProgram(
                country='Dominica',
                category='Caribbean Citizenship',
                name='Dominica Citizenship by Investment',
                description='Citizenship through economic contribution',
                minimum_investment=100000,
                processing_time='2-3 months',
                link='https://nexorainvestments.com/dominica-citizenship',
                rank=1
            ),
            InvestmentProgram(
                country='St Kitts and Nevis',
                category='Caribbean Citizenship',
                name='St Kitts & Nevis Citizenship',
                description='Fast-track citizenship program',
                minimum_investment=150000,
                processing_time='1-2 months',
                link='https://nexorainvestments.com/st-kitts-citizenship',
                rank=2
            ),
            
            # USA EB-5
            InvestmentProgram(
                country='USA',
                category='USA EB-5',
                name='EB-5 Immigrant Investor Program',
                description='Green card through investment',
                minimum_investment=1050000,
                processing_time='18-30 months',
                link='https://nexorainvestments.com/eb5-program',
                rank=1
            ),
            
            # UAE Residency
            InvestmentProgram(
                country='UAE',
                category='UAE Residency',
                name='UAE Golden Visa - Real Estate',
                description='Long-term Dubai residency visa',
                minimum_investment=750000,
                processing_time='2-4 weeks',
                link='https://nexorainvestments.com/dubai-golden-visa',
                rank=1
            ),
        ]
        
        # Clear existing programs
        InvestmentProgram.query.delete()
        
        # Add new programs
        for program in programs:
            db.session.add(program)
        
        db.session.commit()
        print(f'Seeded {len(programs)} investment programs.')
    
    @app.cli.command()
    def reset_db():
        """Clear all data and reinitialize database."""
        db.drop_all()
        db.create_all()
        print('Database reset complete.')
