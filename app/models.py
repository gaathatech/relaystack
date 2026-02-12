from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class WhatsAppMessage(db.Model):
    """Store incoming and outgoing WhatsApp messages"""
    __tablename__ = 'whatsapp_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    direction = db.Column(db.String(20), nullable=False)  # 'incoming' or 'outgoing'
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    message_id = db.Column(db.String(100), unique=True)  # WhatsApp message ID
    status = db.Column(db.String(20), default='delivered')  # delivered, read, failed
    
    def __repr__(self):
        return f'<WhatsAppMessage id={self.id} phone={self.phone}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'phone': self.phone,
            'message': self.message,
            'direction': self.direction,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status
        }


class WhatsAppLead(db.Model):
    """Store WhatsApp leads from conversions"""
    __tablename__ = 'whatsapp_leads'
    
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), nullable=False, unique=True, index=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255))
    interest = db.Column(db.String(100))  # Which option they selected
    budget = db.Column(db.Integer)  # Investment budget in USD
    country_of_interest = db.Column(db.String(100))  # For job search
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<WhatsAppLead id={self.id} phone={self.phone} name={self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'phone': self.phone,
            'name': self.name,
            'email': self.email,
            'interest': self.interest,
            'budget': self.budget,
            'country_of_interest': self.country_of_interest,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class WhatsAppSession(db.Model):
    """Maintain user conversation state and session memory"""
    __tablename__ = 'whatsapp_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), nullable=False, unique=True, index=True)
    current_step = db.Column(db.String(100), default='main_menu')  # Current conversation step
    session_metadata = db.Column(db.JSON, default={})  # Store conversation context
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<WhatsAppSession phone={self.phone} step={self.current_step}>'
    
    def update_metadata(self, key, value):
        """Update session metadata"""
        if not self.session_metadata:
            self.session_metadata = {}
        self.session_metadata[key] = value
        self.updated_at = datetime.utcnow()
    
    def get_metadata(self, key, default=None):
        """Get value from session metadata"""
        if not self.session_metadata:
            return default
        return self.session_metadata.get(key, default)
    
    def to_dict(self):
        return {
            'phone': self.phone,
            'current_step': self.current_step,
            'metadata': self.session_metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class InvestmentProgram(db.Model):
    """European Investment Programs Database"""
    __tablename__ = 'investment_programs'
    
    id = db.Column(db.Integer, primary_key=True)
    country = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))  # Europe, Caribbean, USA, UAE
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    minimum_investment = db.Column(db.Integer)  # USD
    processing_time = db.Column(db.String(100))
    link = db.Column(db.String(500))
    rank = db.Column(db.Integer)  # Display order
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<InvestmentProgram {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'country': self.country,
            'category': self.category,
            'name': self.name,
            'description': self.description,
            'minimum_investment': self.minimum_investment,
            'processing_time': self.processing_time,
            'link': self.link
        }
