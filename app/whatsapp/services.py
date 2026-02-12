import os
import requests
import hmac
import hashlib
import json
from datetime import datetime, timedelta
from app.models import db, WhatsAppMessage, WhatsAppSession, WhatsAppLead, InvestmentProgram

class WhatsAppService:
    """Main service for handling WhatsApp messages and business logic"""
    
    WHATSAPP_API_URL = "https://graph.facebook.com/v18.0"
    PHONE_NUMBER_ID = os.environ.get('PHONE_NUMBER_ID')
    ACCESS_TOKEN = os.environ.get('WHATSAPP_TOKEN')
    VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')
    
    # Menu responses
    MAIN_MENU = """👋 Welcome to Nexora Investments!

Please choose an option:

1️⃣ Explore Residency Programs
2️⃣ Check Eligibility
3️⃣ Talk to Consultant
4️⃣ Job Search Assistance
5️⃣ Book Consultation
6️⃣ Download Brochure

Reply with a number."""

    RESIDENCY_CATEGORIES = """🌍 Top Residency Categories:
A. Europe Golden Visa
B. Caribbean Citizenship
C. USA EB-5
D. UAE Residency
Reply with A, B, C, or D"""

    BUDGET_QUESTION = """💰 What is your investment budget in USD?
Reply with amount (example: 150000)"""

    CONSULTANT_REQUEST = """Our consultant will contact you shortly.
Please share your full name."""

    JOB_COUNTRY_QUESTION = """Which country are you looking for jobs in?
Reply with country name (example: Canada, USA, UK)"""

    BOOKING_LINK = """📅 Book your consultation here:
https://nexorainvestments.com/book

Or text 'back' to return to main menu."""

    BROCHURE_LINK = """📄 Download our brochure:
https://nexorainvestments.com/brochure.pdf

Or text 'back' to return to main menu."""

    INVALID_INPUT = """Sorry, I didn't understand that. Please reply with a valid option, or type 'menu' to return to the main menu."""

    @staticmethod
    def verify_webhook_token(token):
        """Verify webhook token"""
        return token == os.environ.get('VERIFY_TOKEN')

    @staticmethod
    def verify_webhook_signature(body, signature):
        """Verify webhook signature from WhatsApp"""
        expected_signature = hmac.new(
            bytes(os.environ.get('WHATSAPP_TOKEN', ''), 'utf-8'),
            msg=body,
            digestmod=hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected_signature)

    @staticmethod
    def send_message(phone: str, message: str) -> dict:
        """
        Send outgoing WhatsApp message
        
        Args:
            phone: Recipient phone number (with country code)
            message: Message text to send
            
        Returns:
            dict: Response from WhatsApp API
        """
        url = f"{WhatsAppService.WHATSAPP_API_URL}/{WhatsAppService.PHONE_NUMBER_ID}/messages"
        
        headers = {
            "Authorization": f"Bearer {WhatsAppService.ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {
                "body": message
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Store outgoing message in database
            msg_data = response.json()
            msg_id = msg_data.get('messages', [{}])[0].get('id')
            
            db_message = WhatsAppMessage(
                phone=phone,
                message=message,
                direction='outgoing',
                message_id=msg_id,
                timestamp=datetime.utcnow()
            )
            db.session.add(db_message)
            db.session.commit()
            
            return {"success": True, "message_id": msg_id}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_or_create_session(phone: str) -> WhatsAppSession:
        """Get existing session or create new one"""
        session = WhatsAppSession.query.filter_by(phone=phone).first()
        
        if not session:
            session = WhatsAppSession(phone=phone)
            db.session.add(session)
            db.session.commit()
        else:
            # Update last activity
            session.last_activity = datetime.utcnow()
            db.session.commit()
        
        return session

    @staticmethod
    def check_session_timeout(session: WhatsAppSession, timeout_minutes: int = 30) -> bool:
        """Check if session has timed out"""
        if not session.last_activity:
            return False
        
        timeout_threshold = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        return session.last_activity < timeout_threshold

    @staticmethod
    def reset_session(phone: str):
        """Reset session to main menu"""
        session = WhatsAppSession.query.filter_by(phone=phone).first()
        if session:
            session.current_step = 'main_menu'
            session.session_metadata = {}
            session.last_activity = datetime.utcnow()
            db.session.commit()

    @staticmethod
    def process_message(phone: str, message_text: str, message_id: str = None) -> str:
        """
        Process incoming message and return response
        
        Args:
            phone: Sender phone number
            message_text: Message content
            message_id: WhatsApp message ID
            
        Returns:
            str: Response message to send
        """
        # Store incoming message
        db_message = WhatsAppMessage(
            phone=phone,
            message=message_text,
            direction='incoming',
            message_id=message_id,
            timestamp=datetime.utcnow()
        )
        db.session.add(db_message)
        db.session.commit()
        
        # Get or create session
        session = WhatsAppService.get_or_create_session(phone)
        
        # Check for timeout
        if WhatsAppService.check_session_timeout(session):
            WhatsAppService.reset_session(phone)
            session = WhatsAppService.get_or_create_session(phone)
        
        # Normalize input
        user_input = message_text.strip().lower()
        
        # Keywords to start/reset menu
        if user_input in ['hi', 'hello', 'start', 'menu', 'back']:
            session.current_step = 'main_menu'
            session.session_metadata = {}
            db.session.commit()
            return WhatsAppService.MAIN_MENU
        
        # Route based on current step
        if session.current_step == 'main_menu':
            return WhatsAppService.handle_main_menu(phone, session, user_input)
        
        elif session.current_step == 'residency_categories':
            return WhatsAppService.handle_residency_category(phone, session, user_input)
        
        elif session.current_step == 'budget_input':
            return WhatsAppService.handle_budget_input(phone, session, user_input)
        
        elif session.current_step == 'consultant_name':
            return WhatsAppService.handle_consultant_name(phone, session, user_input)
        
        elif session.current_step == 'consultant_email':
            return WhatsAppService.handle_consultant_email(phone, session, user_input)
        
        elif session.current_step == 'job_country':
            return WhatsAppService.handle_job_country(phone, session, user_input)
        
        else:
            return WhatsAppService.INVALID_INPUT

    @staticmethod
    def handle_main_menu(phone: str, session: WhatsAppSession, user_input: str) -> str:
        """Handle main menu selection"""
        if user_input == '1':
            session.current_step = 'residency_categories'
            session.session_metadata = {'selected_option': '1'}
            db.session.commit()
            return WhatsAppService.RESIDENCY_CATEGORIES
        
        elif user_input == '2':
            session.current_step = 'budget_input'
            session.session_metadata = {'selected_option': '2'}
            db.session.commit()
            return WhatsAppService.BUDGET_QUESTION
        
        elif user_input == '3':
            session.current_step = 'consultant_name'
            session.session_metadata = {'selected_option': '3'}
            db.session.commit()
            return WhatsAppService.CONSULTANT_REQUEST
        
        elif user_input == '4':
            session.current_step = 'job_country'
            session.session_metadata = {'selected_option': '4'}
            db.session.commit()
            return WhatsAppService.JOB_COUNTRY_QUESTION
        
        elif user_input == '5':
            # Send booking link, stay in main menu
            return WhatsAppService.BOOKING_LINK
        
        elif user_input == '6':
            # Send brochure link, stay in main menu
            return WhatsAppService.BROCHURE_LINK
        
        else:
            return WhatsAppService.INVALID_INPUT

    @staticmethod
    def handle_residency_category(phone: str, session: WhatsAppSession, user_input: str) -> str:
        """Handle residency category selection"""
        category_map = {
            'a': 'Europe Golden Visa',
            'b': 'Caribbean Citizenship',
            'c': 'USA EB-5',
            'd': 'UAE Residency'
        }
        
        if user_input not in category_map:
            return WhatsAppService.RESIDENCY_CATEGORIES
        
        category = category_map[user_input]
        session.session_metadata['selected_category'] = category
        db.session.commit()
        
        # Get top 3 programs for this category
        programs = InvestmentProgram.query.filter_by(
            category=category
        ).order_by(InvestmentProgram.rank).limit(3).all()
        
        if not programs:
            response = f"Sorry, no programs available for {category} at the moment."
        else:
            response = f"🏆 Top 3 {category} Programs:\n\n"
            for i, prog in enumerate(programs, 1):
                response += f"{i}. {prog.name}\n"
                response += f"   Investment: ${prog.minimum_investment:,}\n"
                response += f"   Link: {prog.link}\n\n"
            response += "Reply 'back' to return to main menu."
        
        session.current_step = 'main_menu'
        db.session.commit()
        return response

    @staticmethod
    def handle_budget_input(phone: str, session: WhatsAppSession, user_input: str) -> str:
        """Handle budget input"""
        try:
            budget = int(user_input.replace(',', '').replace('$', ''))
            
            if budget <= 0:
                return "Please enter a valid amount. " + WhatsAppService.BUDGET_QUESTION
            session.session_metadata['budget'] = budget
            db.session.commit()
            
            # Run eligibility check
            eligibility_response = WhatsAppService.check_eligibility(budget)
            session.current_step = 'main_menu'
            db.session.commit()
            
            return eligibility_response + "\n\nReply 'back' for main menu."
        
        except ValueError:
            return "Please enter a valid amount. " + WhatsAppService.BUDGET_QUESTION

    @staticmethod
    def check_eligibility(budget: int) -> str:
        """Check eligibility based on budget"""
        programs = InvestmentProgram.query.filter(
            InvestmentProgram.minimum_investment <= budget
        ).order_by(InvestmentProgram.rank).all()
        
        if not programs:
            return f"💳 With a budget of ${budget:,}, no programs are currently available. Contact a consultant for custom solutions."
        
        response = f"✅ Great! With ${budget:,} investment, you're eligible for:\n\n"
        for prog in programs[:5]:  # Show top 5
            response += f"• {prog.name} ({prog.country})\n"
            response += f"  Link: {prog.link}\n\n"
        
        response += "Would you like to talk to a consultant? Reply '3' from the main menu."
        return response

    @staticmethod
    def handle_consultant_name(phone: str, session: WhatsAppSession, user_input: str) -> str:
        """Handle consultant name input"""
        if len(user_input.strip()) < 2:
            return "Please provide a valid name."
        session.session_metadata['name'] = user_input.strip()
        session.current_step = 'consultant_email'
        db.session.commit()
        
        return "📧 What is your email address?"

    @staticmethod
    def handle_consultant_email(phone: str, session: WhatsAppSession, user_input: str) -> str:
        """Handle consultant email input"""
        # Basic email validation
        if '@' not in user_input or '.' not in user_input:
            return "Please provide a valid email address."
        name = session.session_metadata.get('name', 'Unknown')
        email = user_input.strip()
        
        # Create or update lead
        lead = WhatsAppLead.query.filter_by(phone=phone).first()
        if not lead:
            lead = WhatsAppLead(phone=phone, name=name, email=email)
            db.session.add(lead)
        else:
            lead.name = name
            lead.email = email
            lead.updated_at = datetime.utcnow()
        
        lead.interest = 'Talk to Consultant'
        db.session.commit()
        
        # Send admin notification
        WhatsAppService.notify_admin(name, phone, email)
        
        # Reset session
        session.current_step = 'main_menu'
        session.session_metadata = {}
        db.session.commit()
        
        return """✅ Thank you! A consultant will contact you shortly.

Is there anything else I can help with? Reply 'back' for main menu."""

    @staticmethod
    def handle_job_country(phone: str, session: WhatsAppSession, user_input: str) -> str:
        """Handle job search country input"""
        country = user_input.strip()
        
        # Store in session metadata
        session.session_metadata['job_country'] = country
        db.session.commit()
        
        # Placeholder for CareerJet API integration
        response = f"""🔍 Searching for jobs in {country}...

Based on your interest in jobs in {country}, a consultant will help you find opportunities.

Would you like a consultant to help? Reply '3' from the main menu, or 'back' to return."""
        
        session.current_step = 'main_menu'
        db.session.commit()
        
        return response

    @staticmethod
    def notify_admin(name: str, phone: str, email: str):
        """
        Send email notification to admin
        
        Note: Requires email service integration (SendGrid, SMTP, etc.)
        """
        try:
            # Placeholder for email integration
            # In production, use SendGrid, SMTP, or similar service
            admin_email = "gaatha.aidni@gmail.com"
            
            # For now, log to system
            print(f"\n[ADMIN NOTIFICATION]\nNew lead from WhatsApp:\nName: {name}\nPhone: {phone}\nEmail: {email}\n")
            
            # TODO: Integrate with email service
            # send_email(
            #     to=admin_email,
            #     subject=f"New Lead: {name}",
            #     body=f"Phone: {phone}\nEmail: {email}"
            # )
        except Exception as e:
            print(f"Error notifying admin: {e}")

    @staticmethod
    def get_user_stats(phone: str) -> dict:
        """Get conversation statistics for a user"""
        messages = WhatsAppMessage.query.filter_by(phone=phone).all()
        incoming = len([m for m in messages if m.direction == 'incoming'])
        outgoing = len([m for m in messages if m.direction == 'outgoing'])
        
        lead = WhatsAppLead.query.filter_by(phone=phone).first()
        
        return {
            'phone': phone,
            'total_messages': len(messages),
            'incoming_messages': incoming,
            'outgoing_messages': outgoing,
            'is_lead': lead is not None,
            'lead_info': lead.to_dict() if lead else None
        }
