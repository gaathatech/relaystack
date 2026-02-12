#!/bin/bash
# Quick WhatsApp Bot Monitor for Termux
# Run this in a separate terminal while your app is running

echo "🤖 WhatsApp Bot Monitoring Script"
echo "=================================="
echo ""
echo "This will help you verify if your bot is receiving and replying to messages"
echo ""
echo "📌 Instructions:"
echo "1. Keep your Flask app running: PORT=8000 python app.py"
echo "2. Run THIS script in another Termux terminal"
echo "3. Send a WhatsApp message to your Business number"
echo "4. Check the output below"
echo ""
echo "=================================="
echo ""

# Function to count messages
check_messages() {
    sqlite3 /workspaces/relaystack/nexora_whatsapp.db << EOF
.mode list
.separator " | "
SELECT COUNT(*) as incoming FROM whatsapp_messages WHERE direction='incoming';
SELECT COUNT(*) as outgoing FROM whatsapp_messages WHERE direction='outgoing';
EOF
}

# Function to show latest messages
show_latest() {
    sqlite3 "nexora_whatsapp.db" << EOF
.mode column
.headers on
.width 20 10 15 50
SELECT 
    SUBSTR(timestamp, 12, 8) as 'Time',
    direction as 'Type',
    SUBSTR(phone, -10) as 'Phone',
    SUBSTR(message, 1, 47) as 'Message'
FROM whatsapp_messages 
ORDER BY timestamp DESC 
LIMIT 10;
EOF
}

echo "Checking current message count..."
echo ""

if command -v sqlite3 &> /dev/null; then
    if [ -f "nexora_whatsapp.db" ]; then
        while true; do
            clear
            echo "🤖 WhatsApp Bot Monitor"
            echo "======================="
            echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
            echo ""
            
            INCOMING=$(sqlite3 nexora_whatsapp.db "SELECT COUNT(*) FROM whatsapp_messages WHERE direction='incoming';" 2>/dev/null || echo "0")
            OUTGOING=$(sqlite3 nexora_whatsapp.db "SELECT COUNT(*) FROM whatsapp_messages WHERE direction='outgoing';" 2>/dev/null || echo "0")
            
            echo "📊 Message Count:"
            echo "   Incoming (your messages): $INCOMING"
            echo "   Outgoing (bot replies):   $OUTGOING"
            echo ""
            
            if [ "$INCOMING" -gt 0 ] && [ "$OUTGOING" -gt 0 ]; then
                echo "✅ BOT IS WORKING! (receiving and replying)"
            elif [ "$INCOMING" -gt 0 ]; then
                echo "⚠️  Messages received but NO replies sent yet"
            else
                echo "❌ No messages received yet"
            fi
            
            echo ""
            echo "📋 Last 10 Messages:"
            echo "===================="
            sqlite3 "nexora_whatsapp.db" << EOSQL
.mode column
.headers on
.width 12 10 12 45
SELECT 
    SUBSTR(timestamp, 12, 8) as Time,
    direction as Type,
    SUBSTR(phone, -10) as Phone,
    SUBSTR(message, 1, 42) as Message
FROM whatsapp_messages 
ORDER BY timestamp DESC 
LIMIT 10;
EOSQL
            
            echo ""
            echo "Press Ctrl+C to stop | Refreshing every 5 seconds..."
            sleep 5
        done
    else
        echo "❌ Database file not found: nexora_whatsapp.db"
        echo "   Make sure the app has been run at least once"
    fi
else
    echo "❌ sqlite3 not installed"
    echo "   Run: pkg install sqlite"
fi
