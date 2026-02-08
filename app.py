"""
Nexora WhatsApp Marketing & AI Chatbot Platform
All-in-one system for WhatsApp bulk messaging, AI customer support, and analytics
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from datetime import datetime, timedelta
import os
import json
from io import BytesIO

# Import modules
from modules.database import init_db, Contact, Campaign, ChatHistory, Analytics, KnowledgeBase
from modules.knowledge_base import init_knowledge_base, init_ivr_flows
from modules.chatbot import chatbot, conversation_manager, IVRHandler
from modules.marketing import MarketingCampaign, ContactManager, CampaignScheduler, MessageTemplate
from modules.analytics import MarketingAnalytics, ChatbotAnalytics, AnalyticsReport, get_quick_stats
from modules.pdf_export import PDFExporter, generate_pdf_from_html

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'change-me-please')

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

@app.before_request
def initialize_app():
    """Initialize database on first request"""
    if not hasattr(app, 'initialized'):
        init_db()
        init_knowledge_base()
        init_ivr_flows()
        app.initialized = True


# ============== DASHBOARD ==============
@app.route('/')
def dashboard():
    """Main dashboard"""
    return render_template('dashboard.html')

# ============== CHATBOT ROUTES ==============
@app.route('/chatbot')
def chatbot_page():
    """Chatbot interface"""
    return render_template('chatbot.html')

@app.route('/api/chat', methods=['POST'])
def chat_api():
    """Handle chat messages"""
    data = request.json
    user_message = data.get('message', '').strip()
    contact_phone = data.get('phone', 'anonymous')
    
    if not user_message:
        return jsonify({'error': 'Empty message'}), 400
    
    try:
        response = chatbot.get_response(user_message, contact_phone)
        return jsonify({
            'success': True,
            'response': response
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/history/<contact_phone>')
def get_chat_history(contact_phone):
    """Get chat history for contact"""
    try:
        limit = request.args.get('limit', 50, type=int)
        messages = ChatHistory.get_by_phone(contact_phone, limit)
        return jsonify({
            'success': True,
            'contact_phone': contact_phone,
            'message_count': len(messages),
            'messages': messages
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ivr/<app_type>/<option>')
def handle_ivr(app_type, option):
    """Handle IVR menu"""
    handler = IVRHandler()
    try:
        result = handler.handle_ivr_flow(app_type, option)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============== CONTACT MANAGEMENT ==============
@app.route('/contacts')
def contacts_page():
    """Contacts management page"""
    return render_template('contacts.html')

@app.route('/api/contacts', methods=['GET', 'POST'])
def contacts_api():
    """Manage contacts via API"""
    if request.method == 'POST':
        data = request.json
        result = ContactManager.add_contact(
            name=data.get('name'),
            phone_number=data.get('phone_number'),
            email=data.get('email'),
            company=data.get('company'),
            tags=data.get('tags')
        )
        return jsonify(result)
    else:
        contacts = ContactManager.get_all_contacts()
        return jsonify({
            'success': True,
            'count': len(contacts),
            'contacts': contacts
        })

@app.route('/api/contacts/search', methods=['GET'])
def search_contacts():
    """Search contacts"""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Empty search query'}), 400
    
    results = ContactManager.search_contacts(query)
    return jsonify({
        'success': True,
        'query': query,
        'count': len(results),
        'results': results
    })

@app.route('/api/contacts/import-csv', methods=['POST'])
def import_csv():
    """Import contacts from CSV file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    result = ContactManager.import_contacts_csv(file)
    return jsonify(result)

@app.route('/api/contacts/import-text', methods=['POST'])
def import_text():
    """Import contacts from text"""
    data = request.json
    text_data = data.get('text', '').strip()
    
    if not text_data:
        return jsonify({'error': 'No text provided'}), 400
    
    result = ContactManager.import_contacts_text(text_data)
    return jsonify(result)

@app.route('/api/contacts/<int:contact_id>', methods=['DELETE'])
def delete_contact(contact_id):
    """Delete contact"""
    result = ContactManager.delete_contact(contact_id)
    return jsonify(result)

# ============== MARKETING CAMPAIGNS ==============
@app.route('/campaigns')
def campaigns_page():
    """Campaigns management page"""
    return render_template('campaigns.html')

@app.route('/api/campaigns', methods=['GET', 'POST'])
def campaigns_api():
    """Manage campaigns via API"""
    if request.method == 'POST':
        data = request.json
        result = MarketingCampaign.create_campaign(
            campaign_name=data.get('campaign_name'),
            message_template=data.get('message_template')
        )
        return jsonify(result)
    else:
        campaigns = Campaign.get_all()
        return jsonify({
            'success': True,
            'count': len(campaigns),
            'campaigns': campaigns
        })

@app.route('/api/campaigns/<int:campaign_id>', methods=['GET'])
def get_campaign(campaign_id):
    """Get campaign details"""
    stats = MarketingCampaign.get_campaign_stats(campaign_id)
    return jsonify({
        'success': True,
        'stats': stats
    })

@app.route('/api/campaigns/<int:campaign_id>/contacts', methods=['POST'])
def add_campaign_contacts(campaign_id):
    """Add contacts to campaign"""
    data = request.json
    contact_ids = data.get('contact_ids', [])
    
    result = MarketingCampaign.add_contacts_to_campaign(campaign_id, contact_ids)
    return jsonify(result)

@app.route('/api/campaigns/<int:campaign_id>/send', methods=['POST'])
def send_campaign(campaign_id):
    """Send campaign immediately"""
    result = MarketingCampaign.send_campaign_now(campaign_id)
    return jsonify(result)

@app.route('/api/campaigns/<int:campaign_id>/schedule', methods=['POST'])
def schedule_campaign(campaign_id):
    """Schedule campaign"""
    data = request.json
    scheduled_time = datetime.fromisoformat(data.get('scheduled_time'))
    contact_ids = data.get('contact_ids', [])
    
    result = MarketingCampaign.schedule_campaign(campaign_id, scheduled_time, contact_ids)
    return jsonify(result)

@app.route('/api/campaigns/<int:campaign_id>/preview', methods=['GET'])
def preview_campaign(campaign_id):
    """Preview campaign message"""
    contact_id = request.args.get('contact_id', 1, type=int)
    preview = MarketingCampaign.preview_message(campaign_id, contact_id)
    return jsonify({
        'success': True,
        'preview': preview
    })

# ============== ANALYTICS ==============
@app.route('/analytics')
def analytics_page():
    """Analytics dashboard"""
    return render_template('analytics.html')

@app.route('/api/analytics/summary')
def analytics_summary():
    """Get analytics summary"""
    days = request.args.get('days', 30, type=int)
    summary = AnalyticsReport.generate_executive_summary(days)
    return jsonify(summary)

@app.route('/api/analytics/detailed')
def analytics_detailed():
    """Get detailed analytics"""
    days = request.args.get('days', 30, type=int)
    report = AnalyticsReport.generate_detailed_report(days)
    return jsonify(report)

@app.route('/api/analytics/export-json')
def export_analytics_json():
    """Export analytics as JSON"""
    days = request.args.get('days', 30, type=int)
    json_data = AnalyticsReport.export_report_json(days)
    return jsonify({
        'success': True,
        'data': json.loads(json_data)
    })

@app.route('/api/analytics/export-html')
def export_analytics_html():
    """Export analytics as HTML"""
    days = request.args.get('days', 30, type=int)
    html = AnalyticsReport.export_report_html(days)
    
    return send_file(
        BytesIO(html.encode('utf-8')),
        mimetype='text/html',
        as_attachment=True,
        download_name=f'nexora_analytics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
    )

# ============== KNOWLEDGE BASE ==============
@app.route('/knowledge-base')
def knowledge_base_page():
    """Knowledge base management"""
    return render_template('knowledge_base.html')

@app.route('/api/knowledge-base', methods=['GET', 'POST'])
def knowledge_base_api():
    """Manage knowledge base"""
    if request.method == 'POST':
        data = request.json
        result = KnowledgeBase.add_qa(
            question=data.get('question'),
            answer=data.get('answer'),
            category=data.get('category'),
            app_source=data.get('app_source'),
            keywords=data.get('keywords')
        )
        return jsonify(result)
    else:
        qa_items = KnowledgeBase.get_all()
        return jsonify({
            'success': True,
            'count': len(qa_items),
            'items': qa_items
        })

@app.route('/api/knowledge-base/search')
def knowledge_base_search():
    """Search knowledge base"""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Empty search'}), 400
    
    results = KnowledgeBase.search(query)
    return jsonify({
        'success': True,
        'query': query,
        'count': len(results),
        'results': results
    })

# ============== PDF EXPORT ==============
@app.route('/api/export/chat-history/<contact_phone>')
def export_chat_history(contact_phone):
    """Export chat history as PDF"""
    limit = request.args.get('limit', 100, type=int)
    
    html = PDFExporter.export_chat_history_html(contact_phone, limit)
    pdf_bytes = generate_pdf_from_html(html)
    
    return send_file(
        BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'chat_history_{contact_phone}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    )

@app.route('/api/export/campaign-report/<int:campaign_id>')
def export_campaign_report(campaign_id):
    """Export campaign report as PDF"""
    html = PDFExporter.export_campaign_report_html(campaign_id)
    pdf_bytes = generate_pdf_from_html(html)
    
    return send_file(
        BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'campaign_report_{campaign_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    )

# ============== TEMPLATES ROUTES ==============
@app.route('/api/templates/variables')
def get_template_variables():
    """Get available template variables"""
    return jsonify({
        'success': True,
        'variables': MessageTemplate.get_available_variables()
    })

@app.route('/api/templates/validate', methods=['POST'])
def validate_template():
    """Validate message template"""
    data = request.json
    result = MessageTemplate.create_template(data.get('template', ''))
    return jsonify(result)

@app.route('/api/templates/render', methods=['POST'])
def template_render_api():
    """Render template with contact data"""
    data = request.json
    rendered = MessageTemplate.render_template(
        data.get('template', ''),
        {
            'name': data.get('name', 'Friend'),
            'phone': data.get('phone', ''),
            'company': data.get('company', '')
        }
    )
    return jsonify({
        'success': True,
        'rendered': rendered
    })

# ============== HEALTH CHECK ==============
@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Nexora WhatsApp Marketing & AI Chatbot'
    })

# ============== ERROR HANDLERS ==============
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
