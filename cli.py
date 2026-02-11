"""
CLI utilities for WhatsApp chatbot administration
Usage: python cli.py <command> [args]
"""

import click
from datetime import datetime, timedelta
from app import create_app
from app.models import db, WhatsAppMessage, WhatsAppLead, WhatsAppSession, InvestmentProgram

app = create_app()

@click.group()
def cli():
    """Nexora WhatsApp Chatbot CLI"""
    pass

# Database Commands

@cli.command()
def init_db():
    """Initialize database"""
    with app.app_context():
        db.create_all()
        click.echo("✅ Database initialized")

@cli.command()
def reset_db():
    """Reset database (WARNING: deletes all data)"""
    if click.confirm('Are you sure? This will DELETE ALL data!'):
        with app.app_context():
            db.drop_all()
            db.create_all()
            click.echo("✅ Database reset complete")

@cli.command()
def seed_programs():
    """Seed investment programs"""
    with app.app_context():
        programs = [
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
        
        InvestmentProgram.query.delete()
        for program in programs:
            db.session.add(program)
        db.session.commit()
        click.echo(f"✅ Seeded {len(programs)} programs")

# Reporting Commands

@cli.command()
@click.option('--days', default=7, help='Number of days to report')
def stats(days):
    """Show activity statistics"""
    with app.app_context():
        since = datetime.utcnow() - timedelta(days=days)
        
        total_messages = WhatsAppMessage.query.count()
        recent_messages = WhatsAppMessage.query.filter(
            WhatsAppMessage.timestamp >= since
        ).count()
        
        incoming = WhatsAppMessage.query.filter_by(direction='incoming').count()
        outgoing = WhatsAppMessage.query.filter_by(direction='outgoing').count()
        
        total_leads = WhatsAppLead.query.count()
        recent_leads = WhatsAppLead.query.filter(
            WhatsAppLead.created_at >= since
        ).count()
        
        active_sessions = WhatsAppSession.query.filter_by(is_active=True).count()
        
        click.echo("\n📊 CHATBOT STATISTICS")
        click.echo("=" * 50)
        click.echo(f"Total Messages: {total_messages}")
        click.echo(f"Messages (last {days} days): {recent_messages}")
        click.echo(f"Incoming: {incoming} | Outgoing: {outgoing}")
        click.echo(f"\nTotal Leads: {total_leads}")
        click.echo(f"New Leads (last {days} days): {recent_leads}")
        click.echo(f"Active Sessions: {active_sessions}")
        click.echo("=" * 50 + "\n")

@cli.command()
def list_leads():
    """List all leads"""
    with app.app_context():
        leads = WhatsAppLead.query.order_by(WhatsAppLead.created_at.desc()).all()
        
        if not leads:
            click.echo("No leads found")
            return
        
        click.echo("\n👤 LEADS LIST")
        click.echo("=" * 80)
        
        for lead in leads:
            click.echo(f"\nName: {lead.name}")
            click.echo(f"Phone: {lead.phone}")
            click.echo(f"Email: {lead.email}")
            click.echo(f"Interest: {lead.interest}")
            if lead.budget:
                click.echo(f"Budget: ${lead.budget:,}")
            click.echo(f"Created: {lead.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            click.echo("-" * 80)

@cli.command()
@click.argument('phone')
def user_info(phone):
    """Get user conversation history"""
    with app.app_context():
        session = WhatsAppSession.query.filter_by(phone=phone).first()
        lead = WhatsAppLead.query.filter_by(phone=phone).first()
        messages = WhatsAppMessage.query.filter_by(phone=phone).all()
        
        click.echo(f"\n🔍 USER: {phone}")
        click.echo("=" * 80)
        
        # Session info
        if session:
            click.echo("\nSession:")
            click.echo(f"  Status: {'Active' if session.is_active else 'Inactive'}")
            click.echo(f"  Current Step: {session.current_step}")
            click.echo(f"  Created: {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            click.echo(f"  Last Activity: {session.last_activity.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Lead info
        if lead:
            click.echo("\nLead Info:")
            click.echo(f"  Name: {lead.name}")
            click.echo(f"  Email: {lead.email}")
            click.echo(f"  Interest: {lead.interest}")
            click.echo(f"  Status: Converted ✅")
        
        # Messages
        click.echo(f"\nMessages: {len(messages)} total")
        for msg in messages[-10:]:  # Last 10 messages
            direction = "→" if msg.direction == "outgoing" else "←"
            click.echo(f"  {msg.timestamp.strftime('%H:%M:%S')} {direction} {msg.message[:50]}")

@cli.command()
@click.argument('phone')
def delete_user(phone):
    """Delete user data"""
    with app.app_context():
        if click.confirm(f'Delete all data for {phone}?'):
            WhatsAppMessage.query.filter_by(phone=phone).delete()
            WhatsAppSession.query.filter_by(phone=phone).delete()
            WhatsAppLead.query.filter_by(phone=phone).delete()
            db.session.commit()
            click.echo(f"✅ Deleted user {phone}")

# Testing Commands

@cli.command()
@click.argument('phone')
def test_message(phone):
    """Send test message to user"""
    from app.whatsapp.services import WhatsAppService
    
    with app.app_context():
        result = WhatsAppService.send_message(
            phone=phone,
            message="👋 Welcome to Nexora Investments!\n\nThis is a test message."
        )
        
        if result['success']:
            click.echo(f"✅ Message sent to {phone}")
            click.echo(f"Message ID: {result['message_id']}")
        else:
            click.echo(f"❌ Failed to send message: {result['error']}")

@cli.command()
def cleanup_sessions():
    """Remove inactive sessions older than 24 hours"""
    with app.app_context():
        threshold = datetime.utcnow() - timedelta(hours=24)
        
        deleted = WhatsAppSession.query.filter(
            WhatsAppSession.last_activity < threshold,
            WhatsAppSession.is_active == False
        ).delete()
        
        db.session.commit()
        click.echo(f"✅ Removed {deleted} inactive sessions")

if __name__ == '__main__':
    cli()
