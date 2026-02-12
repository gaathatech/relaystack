"""
Unit tests for WhatsApp services and routes
Run with: pytest tests/
"""

import pytest
import json
from datetime import datetime
from app import create_app
from app.models import db, WhatsAppMessage, WhatsAppSession, WhatsAppLead
from app.whatsapp.services import WhatsAppService

@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def app_context(app):
    """Create app context"""
    with app.app_context():
        yield

# Webhook Tests

def test_webhook_verification(client):
    """Test webhook verification endpoint"""
    response = client.get(
        '/webhook?hub.mode=subscribe&hub.verify_token=test_token&hub.challenge=test_challenge',
        headers={'Content-Type': 'application/json'}
    )
    assert response.status_code in [200, 403]  # Depends on VERIFY_TOKEN

def test_webhook_post_message(client):
    """Test webhook receives post messages"""
    payload = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "1234567890",
                        "id": "msg_123",
                        "text": {"body": "hello"},
                        "timestamp": "1234567890"
                    }]
                }
            }]
        }]
    }
    
    response = client.post(
        '/webhook',
        data=json.dumps(payload),
        content_type='application/json'
    )
    assert response.status_code == 200
    assert response.get_json()['status'] == 'received'

def test_webhook_empty_entry(client):
    """Test webhook with empty entry"""
    response = client.post(
        '/webhook',
        data=json.dumps({}),
        content_type='application/json'
    )
    assert response.status_code == 200

# Service Tests

def test_session_creation(app_context):
    """Test WhatsApp session creation"""
    phone = "1234567890"
    session = WhatsAppService.get_or_create_session(phone)
    
    assert session.phone == phone
    assert session.current_step == 'main_menu'
    assert session.session_metadata == {}

def test_session_retrieval(app_context):
    """Test retrieving existing session"""
    phone = "1234567890"
    
    # Create session
    session1 = WhatsAppService.get_or_create_session(phone)
    session1.session_metadata = {'test': 'data'}
    db.session.commit()
    
    # Retrieve session
    session2 = WhatsAppService.get_or_create_session(phone)
    
    assert session1.id == session2.id
    assert session2.session_metadata.get('test') == 'data'

def test_process_message_main_menu(app_context):
    """Test main menu message processing"""
    response = WhatsAppService.process_message(
        phone="1234567890",
        message_text="hi",
        message_id="msg_123"
    )
    
    assert "Welcome to Nexora Investments" in response
    assert "1️⃣ Explore Residency Programs" in response

def test_process_message_invalid_input(app_context):
    """Test invalid input handling"""
    # First send 'hi' to get main menu
    WhatsAppService.process_message(
        phone="1234567890",
        message_text="hi"
    )
    
    # Then send invalid option
    response = WhatsAppService.process_message(
        phone="1234567890",
        message_text="invalid",
        message_id="msg_124"
    )
    
    assert "didn't understand" in response

def test_process_message_option_1(app_context):
    """Test residency programs option"""
    # Get main menu
    WhatsAppService.process_message(
        phone="1234567890",
        message_text="hi"
    )
    
    # Select option 1
    response = WhatsAppService.process_message(
        phone="1234567890",
        message_text="1",
        message_id="msg_124"
    )
    
    assert "Top Residency Categories" in response

def test_process_message_option_2(app_context):
    """Test eligibility check option"""
    WhatsAppService.process_message(
        phone="1234567890",
        message_text="hi"
    )
    
    response = WhatsAppService.process_message(
        phone="1234567890",
        message_text="2"
    )
    
    assert "investment budget" in response

def test_process_message_budget_input(app_context):
    """Test budget input processing"""
    WhatsAppService.process_message(
        phone="1234567890",
        message_text="hi"
    )
    
    WhatsAppService.process_message(
        phone="1234567890",
        message_text="2"
    )
    
    response = WhatsAppService.process_message(
        phone="1234567890",
        message_text="250000"
    )
    
    assert "eligible" in response or "budget" in response

def test_message_storage(app_context):
    """Test incoming message storage"""
    phone = "1234567890"
    message_text = "Test message"
    message_id = "msg_123"
    
    WhatsAppService.process_message(
        phone=phone,
        message_text=message_text,
        message_id=message_id
    )
    
    stored = WhatsAppMessage.query.filter_by(
        phone=phone,
        message_id=message_id
    ).first()
    
    assert stored is not None
    assert stored.message == message_text
    assert stored.direction == 'incoming'

def test_user_stats(app_context):
    """Test user statistics retrieval"""
    phone = "1234567890"
    
    # Send some messages
    WhatsAppService.process_message(phone=phone, message_text="hi")
    WhatsAppService.process_message(phone=phone, message_text="1")
    
    stats = WhatsAppService.get_user_stats(phone)
    
    assert stats['phone'] == phone
    assert stats['total_messages'] > 0
    assert stats['incoming_messages'] > 0

# API Tests

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/webhook/health')
    assert response.status_code == 200
    assert response.get_json()['status'] == 'healthy'

def test_service_status(client):
    """Test main service status endpoint"""
    response = client.get('/')
    assert response.status_code == 200
    assert response.get_json()['status'] == 'running'

# Error Handling Tests

def test_404_error(client):
    """Test 404 error handling"""
    response = client.get('/nonexistent')
    assert response.status_code == 404

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
