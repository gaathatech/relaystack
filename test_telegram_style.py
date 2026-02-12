#!/usr/bin/env python3
"""
Quick test to verify WhatsApp bot is working
Run this while the app is running to test message processing
"""

import sqlite3
import json
from datetime import datetime
from app import create_app
from app.whatsapp.services import WhatsAppService

# Initialize app
app = create_app()

def check_messages_status():
    """Check incoming and outgoing messages in database"""
    try:
        with app.app_context():
            from app.models import WhatsAppMessage
            
            # Get all messages
            messages = WhatsAppMessage.query.order_by(
                WhatsAppMessage.timestamp.desc()
            ).limit(20).all()
            
            if not messages:
                print("❌ No messages in database yet. Send a WhatsApp message first!")
                return False
            
            print("\n📊 Last 20 Messages:\n")
            print(f"{'Time':<20} {'Direction':<10} {'Phone':<15} {'Message':<40}")
            print("=" * 90)
            
            has_incoming = False
            has_outgoing = False
            
            for msg in messages:
                time_str = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S") if msg.timestamp else "N/A"
                direction = msg.direction.upper()
                phone = msg.phone or "Unknown"
                message_text = msg.message[:37] + "..." if len(msg.message) > 40 else msg.message
                
                if direction == "INCOMING":
                    has_incoming = True
                    print(f"✉️  {time_str} | {direction:<10} | {phone:<15} | {message_text}")
                else:
                    has_outgoing = True
                    print(f"📤 {time_str} | {direction:<10} | {phone:<15} | {message_text}")
            
            print("\n" + "=" * 90)
            
            # Summary
            incoming_count = WhatsAppMessage.query.filter_by(direction='incoming').count()
            outgoing_count = WhatsAppMessage.query.filter_by(direction='outgoing').count()
            
            print(f"\n📈 Summary:")
            print(f"   Total Incoming (messages you sent): {incoming_count}")
            print(f"   Total Outgoing (bot replies): {outgoing_count}")
            
            if has_incoming and has_outgoing:
                print(f"\n✅ SUCCESS! Bot is receiving AND replying to messages!")
                return True
            elif has_incoming and not has_outgoing:
                print(f"\n⚠️  WARNING! Bot received messages but NO replies sent!")
                print(f"   Check: WhatsApp token, Phone Number ID, or webhook URL")
                return False
            else:
                print(f"\n❌ ERROR! No messages received yet.")
                return False
                
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False


def test_message_processing():
    """Test if message processing works"""
    print("\n🧪 Testing Message Processing...\n")
    
    test_cases = [
        ("11234567890", "hello"),       # Should get main menu
        ("11234567890", "1"),           # Should get residency options
        ("11234567890", "xyz"),         # Should get "invalid input" response
        ("19876543210", "hi"),          # Different number, should get menu
    ]
    
    with app.app_context():
        from app.models import WhatsAppMessage
        
        for phone, message in test_cases:
            print(f"Testing: {phone} sends '{message}'")
            response = WhatsAppService.process_message(
                phone=phone,
                message_text=message,
                message_id=f"test_{phone}_{datetime.now().timestamp()}"
            )
            
            if response:
                print(f"  ✅ Got response: {response[:60]}...\n")
            else:
                print(f"  ❌ No response generated!\n")


def show_help():
    """Show how to verify replies"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║         WhatsApp Bot Reply Verification Guide                  ║
╚════════════════════════════════════════════════════════════════╝

📱 TO CHECK IF REPLIES ARE HAPPENING:

1️⃣  While app is running (PORT=8000 python app.py)
    Open a terminal and run:
    
    python test_telegram_style.py
    
2️⃣  Send a test message from your phone to the WhatsApp Business number

3️⃣  Run the script again - you should see:
    ✅ Incoming message (what you sent)
    ✅ Outgoing message (bot reply)

📋 WHAT SHOULD HAPPEN:

   Your message → Bot processes → Bot replies
   
   ANY message you send should get a reply:
   • Send "hello" → Get menu
   • Send "xyz" → Get "I don't understand" message
   • Send "1" → Get residency options
   • Send random text → Get error message
   
   🎯 THE BOT REPLIES TO EVERYTHING!

🔍 WHERE TO CHECK:

   Option A: This script (shows last 20 messages)
   Option B: Database: sqlite3 nexora_whatsapp.db
   Option C: Logs in terminal where app is running

⚠️  IF YOU DON'T SEE REPLIES:

   • Check .env has valid WHATSAPP_TOKEN
   • Check .env has valid PHONE_NUMBER_ID
   • Check webhook URL is set in Meta Business Suite
   • Check PUBLIC URL is correct (cloudflared/ngrok)
   • Check app logs for errors

""")


if __name__ == '__main__':
    show_help()
    check_messages_status()
    print("\n")
    test_message_processing()
