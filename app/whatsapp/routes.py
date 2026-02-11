from flask import Blueprint, request, jsonify
import os
from datetime import datetime
from app.whatsapp.services import WhatsAppService
from app.models import db, WhatsAppMessage

# Create WhatsApp Blueprint
whatsapp_bp = Blueprint('whatsapp', __name__, url_prefix='/webhook')

@whatsapp_bp.route('', methods=['GET'])
def verify_webhook():
    """
    Webhook verification endpoint for WhatsApp
    
    WhatsApp sends a GET request with:
    - hub.mode: always 'subscribe'
    - hub.verify_token: token to verify
    - hub.challenge: challenge string to return
    """
    mode = request.args.get('hub.mode')
    verify_token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    # Verify the request
    if mode == 'subscribe' and WhatsAppService.verify_webhook_token(verify_token):
        return challenge, 200
    else:
        return jsonify({'error': 'Invalid verification token'}), 403


@whatsapp_bp.route('', methods=['POST'])
def receive_message():
    """
    Webhook endpoint to receive incoming WhatsApp messages
    
    Facebook sends a POST request with message data in format:
    {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "phone_number",
                                    "id": "message_id",
                                    "text": {"body": "message_text"},
                                    "timestamp": "unix_timestamp"
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
    """
    try:
        data = request.get_json()
        
        # Validate webhook
        if not _validate_webhook_request(request):
            return jsonify({'error': 'Invalid signature'}), 403
        
        # Check if this is a valid message entry
        if not data or 'entry' not in data or len(data['entry']) == 0:
            return jsonify({'status': 'received'}), 200
        
        entry = data['entry'][0]
        
        # Check if there are changes
        if 'changes' not in entry or len(entry['changes']) == 0:
            return jsonify({'status': 'received'}), 200
        
        change = entry['changes'][0]
        value = change.get('value', {})
        
        # Handle messages
        if 'messages' in value and len(value['messages']) > 0:
            for message in value['messages']:
                _handle_incoming_message(message)
        
        # Handle status updates (delivery, read, etc.)
        if 'statuses' in value and len(value['statuses']) > 0:
            for status in value['statuses']:
                _handle_message_status(status)
        
        return jsonify({'status': 'received'}), 200
    
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return jsonify({'error': str(e)}), 500


def _validate_webhook_request(req):
    """
    Validate webhook request signature
    
    Optional: Uncomment to enable signature verification
    This requires additional setup with WhatsApp
    """
    # signature = req.headers.get('X-Hub-Signature-256', '')
    # if signature:
    #     return WhatsAppService.verify_webhook_signature(
    #         req.get_data(),
    #         signature.replace('sha256=', '')
    #     )
    return True


def _handle_incoming_message(message: dict):
    """Process incoming message and send response"""
    try:
        # Extract message data
        sender_phone = message.get('from')
        message_id = message.get('id')
        timestamp = int(message.get('timestamp', 0))
        
        # Extract message text
        message_text = ''
        if 'text' in message:
            message_text = message['text'].get('body', '')
        elif 'audio' in message:
            message_text = '[Audio Message]'
        elif 'image' in message:
            message_text = '[Image Message]'
        elif 'document' in message:
            message_text = '[Document Message]'
        else:
            message_text = '[Unsupported Message Type]'
        
        if not message_text:
            return
        
        # Process message and get response
        response_message = WhatsAppService.process_message(
            phone=sender_phone,
            message_text=message_text,
            message_id=message_id
        )
        
        # Send response
        if response_message:
            WhatsAppService.send_message(
                phone=sender_phone,
                message=response_message
            )
    
    except Exception as e:
        print(f"Error handling incoming message: {e}")


def _handle_message_status(status: dict):
    """Handle message status updates (delivered, read, failed)"""
    try:
        message_id = status.get('id')
        status_type = status.get('status')  # delivered, read, failed, sent
        phone = status.get('recipient_id')
        
        # Update message status in database
        message = WhatsAppMessage.query.filter_by(message_id=message_id).first()
        if message:
            message.status = status_type
            db.session.commit()
    
    except Exception as e:
        print(f"Error handling status update: {e}")


# Additional API endpoints for admin/analytics

@whatsapp_bp.route('/stats/<phone>', methods=['GET'])
def get_user_stats(phone):
    """Get conversation statistics for a user"""
    try:
        stats = WhatsAppService.get_user_stats(phone)
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@whatsapp_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'WhatsApp Chatbot'
    }), 200
