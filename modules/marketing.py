"""
WhatsApp Marketing module for campaign management, scheduling, and tracking
"""

from datetime import datetime, timedelta
from modules.database import Campaign, Contact, get_db, Analytics
import schedule
import threading

class MarketingCampaign:
    """Manage WhatsApp marketing campaigns"""
    
    @staticmethod
    def create_campaign(campaign_name, message_template):
        """Create new marketing campaign"""
        return Campaign.create(campaign_name, message_template)
    
    @staticmethod
    def add_contacts_to_campaign(campaign_id, contact_ids):
        """Add contacts to campaign"""
        conn = get_db()
        cursor = conn.cursor()
        
        count = 0
        for contact_id in contact_ids:
            try:
                cursor.execute(
                    'INSERT INTO campaign_messages (campaign_id, contact_id, message, status) SELECT ?, ?, message_template, ? FROM campaigns WHERE id = ?',
                    (campaign_id, contact_id, 'pending', campaign_id)
                )
                count += 1
            except:
                pass
        
        # Update campaign contacts count
        cursor.execute('UPDATE campaigns SET contacts_count = ? WHERE id = ?', (count, campaign_id))
        conn.commit()
        conn.close()
        
        return {'status': 'success', 'contacts_added': count}
    
    @staticmethod
    def schedule_campaign(campaign_id, scheduled_time, contact_ids):
        """Schedule campaign to send at specific time"""
        Campaign.schedule(campaign_id, scheduled_time, contact_ids)
        
        # Add scheduler job
        scheduler = CampaignScheduler()
        scheduler.schedule_send(campaign_id, scheduled_time)
        
        analyticsDetails = Analytics.record('campaign_scheduled', campaign_id=campaign_id)
        
        return {'status': 'success', 'scheduled_time': scheduled_time}
    
    @staticmethod
    def send_campaign_now(campaign_id):
        """Send campaign immediately"""
        conn = get_db()
        cursor = conn.cursor()
        
        # Get campaign and pending messages
        cursor.execute('SELECT * FROM campaigns WHERE id = ?', (campaign_id,))
        campaign = dict(cursor.fetchone())
        
        cursor.execute('SELECT * FROM campaign_messages WHERE campaign_id = ? AND status = ?',
                      (campaign_id, 'pending'))
        messages = [dict(row) for row in cursor.fetchall()]
        
        # Simulate sending messages
        success_count = len(messages)
        failed_count = 0
        
        for msg in messages:
            # Here you would integrate actual WhatsApp API
            # For now, we'll just mark as sent
            cursor.execute('UPDATE campaign_messages SET status = ?, sent_time = ? WHERE id = ?',
                          ('sent', datetime.now(), msg['id']))
            Analytics.record('message_sent', campaign_id=campaign_id)
        
        # Update campaign stats
        cursor.execute('UPDATE campaigns SET status = ?, success_count = ?, failed_count = ?, sent_time = ? WHERE id = ?',
                      ('sent', success_count, failed_count, datetime.now(), campaign_id))
        
        conn.commit()
        conn.close()
        
        return {
            'status': 'success',
            'success_count': success_count,
            'failed_count': failed_count,
            'campaign_id': campaign_id
        }
    
    @staticmethod
    def get_campaign_stats(campaign_id):
        """Get campaign statistics"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM campaigns WHERE id = ?', (campaign_id,))
        campaign = dict(cursor.fetchone())
        
        cursor.execute('SELECT status, COUNT(*) as count FROM campaign_messages WHERE campaign_id = ? GROUP BY status',
                      (campaign_id,))
        stats = {row['status']: row['count'] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            'campaign_name': campaign['campaign_name'],
            'total_contacts': campaign['contacts_count'],
            'success_count': campaign['success_count'],
            'failed_count': campaign['failed_count'],
            'status': campaign['status'],
            'message_breakdown': stats,
            'created_date': campaign['created_date'],
            'sent_time': campaign['sent_time']
        }
    
    @staticmethod
    def preview_message(campaign_id, contact_id):
        """Get preview of message for specific contact"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT message_template FROM campaigns WHERE id = ?', (campaign_id,))
        template = dict(cursor.fetchone())['message_template']
        
        cursor.execute('SELECT name, phone_number FROM contacts WHERE id = ?', (contact_id,))
        contact = dict(cursor.fetchone())
        
        # Replace variables in template
        preview = template.replace('{name}', contact['name']).replace('{phone}', contact['phone_number'])
        
        conn.close()
        
        return {'preview': preview, 'contact': contact}

class ContactManager:
    """Manage contact lists for marketing"""
    
    @staticmethod
    def add_contact(name, phone_number, email=None, company=None, tags=None):
        """Add single contact"""
        return Contact.add(name, phone_number, email, company, tags)
    
    @staticmethod
    def import_contacts_csv(csv_file):
        """Import contacts from CSV file"""
        import csv
        added = 0
        errors = []
        
        try:
            for row in csv.DictReader(csv_file.stream.read().decode('utf-8').splitlines()):
                result = Contact.add(
                    name=row.get('name', ''),
                    phone_number=row.get('phone_number', row.get('phone', '')),
                    email=row.get('email'),
                    company=row.get('company'),
                    tags=row.get('tags')
                )
                if result['status'] == 'success':
                    added += 1
                else:
                    errors.append(row['phone_number'])
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
        
        return {'status': 'success', 'added': added, 'errors': errors}
    
    @staticmethod
    def import_contacts_text(text_data):
        """Import contacts from text (one phone per line or comma-separated)"""
        added = 0
        errors = []
        
        # Parse phone numbers from text
        lines = text_data.strip().split('\n')
        for line in lines:
            phones = [p.strip() for p in line.split(',')]
            for phone in phones:
                if phone:
                    # Use phone number as name, can be updated later
                    result = Contact.add(name=phone, phone_number=phone)
                    if result['status'] == 'success':
                        added += 1
                    else:
                        errors.append(phone)
        
        return {'status': 'success', 'added': added, 'errors': errors}
    
    @staticmethod
    def get_all_contacts():
        """Get all contacts"""
        return Contact.get_all()
    
    @staticmethod
    def list_contacts_for_campaign(campaign_id):
        """Get contacts associated with a campaign"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT c.* FROM contacts c
            JOIN campaign_messages cm ON c.id = cm.contact_id
            WHERE cm.campaign_id = ?
        ''', (campaign_id,))
        contacts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return contacts
    
    @staticmethod
    def search_contacts(query):
        """Search contacts"""
        return Contact.search(query)
    
    @staticmethod
    def delete_contact(contact_id):
        """Delete contact"""
        return Contact.delete(contact_id)
    
    @staticmethod
    def get_contacts_by_tag(tag):
        """Get contacts by tag"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM contacts WHERE tags LIKE ?', (f'%{tag}%',))
        contacts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return contacts

class CampaignScheduler:
    """Scheduler for sending campaigns at specified times"""
    
    def __init__(self):
        self.scheduler_thread = None
    
    def schedule_send(self, campaign_id, scheduled_time):
        """Schedule campaign send"""
        # Calculate delay
        delay = (scheduled_time - datetime.now()).total_seconds()
        
        if delay > 0:
            # Schedule the send
            def send_delayed():
                import time
                time.sleep(delay)
                MarketingCampaign.send_campaign_now(campaign_id)
            
            thread = threading.Thread(target=send_delayed, daemon=True)
            thread.start()
            
            return {'status': 'scheduled', 'campaign_id': campaign_id, 'send_time': scheduled_time}
        else:
            # Send immediately if time is in past
            return MarketingCampaign.send_campaign_now(campaign_id)
    
    def get_scheduled_campaigns(self):
        """Get list of scheduled campaigns"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM campaigns WHERE status = ? ORDER BY scheduled_time',
                      ('scheduled',))
        campaigns = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return campaigns

class MessageTemplate:
    """Message template builder and variable replacement"""
    
    VARIABLES = {
        'name': 'Contact name',
        'phone': 'Phone number',
        'company': 'Company name',
        'date': 'Current date',
        'time': 'Current time'
    }
    
    @staticmethod
    def get_available_variables():
        """Get list of available template variables"""
        return MessageTemplate.VARIABLES
    
    @staticmethod
    def create_template(text):
        """Create template with variables like {name}, {phone}, etc."""
        # Validate template
        import re
        variables = re.findall(r'\{(\w+)\}', text)
        invalid = [v for v in variables if v not in MessageTemplate.VARIABLES]
        
        if invalid:
            return {'status': 'error', 'invalid_variables': invalid}
        
        return {'status': 'success', 'template': text, 'variables': variables}
    
    @staticmethod
    def render_template(template, contact_data):
        """Render template with actual contact data"""
        rendered = template
        rendered = rendered.replace('{name}', contact_data.get('name', 'Friend'))
        rendered = rendered.replace('{phone}', contact_data.get('phone', ''))
        rendered = rendered.replace('{company}', contact_data.get('company', ''))
        rendered = rendered.replace('{date}', datetime.now().strftime('%Y-%m-%d'))
        rendered = rendered.replace('{time}', datetime.now().strftime('%H:%M'))
        return rendered

# Helper function: Quick campaign setup
def create_quick_campaign(campaign_name, message_template, contact_phone_list, send_time=None):
    """Create and setup campaign in one call"""
    
    # Create campaign
    campaign_result = MarketingCampaign.create_campaign(campaign_name, message_template)
    if campaign_result['status'] != 'success':
        return campaign_result
    
    campaign_id = campaign_result['id']
    
    # Add contacts
    contact_ids = []
    for phone in contact_phone_list:
        result = Contact.add(name=phone, phone_number=phone)
        if result['status'] == 'success':
            contact_ids.append(result['id'])
    
    MarketingCampaign.add_contacts_to_campaign(campaign_id, contact_ids)
    
    # Schedule or send
    if send_time:
        MarketingCampaign.schedule_campaign(campaign_id, send_time, contact_ids)
        status = "scheduled"
    else:
        MarketingCampaign.send_campaign_now(campaign_id)
        status = "sent"
    
    return {
        'status': 'success',
        'campaign_id': campaign_id,
        'campaign_name': campaign_name,
        'contacts': len(contact_ids),
        'send_status': status
    }
