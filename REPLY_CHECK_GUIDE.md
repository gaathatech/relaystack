# 🤖 WhatsApp Bot - Reply Verification Guide

## Quick Answer to Your Questions:

### ❓ "Can I check if replies are happening?"
**YES!** Here are 3 ways:

---

## 🔍 Method 1: Check Logs (EASIEST)

While your app is running, watch the terminal for these messages:

```bash
# Keep your app running
PORT=8000 python app.py

# You should see logs like:
# Incoming message from +919825728291: "hello"
# Processing message...
# Sending reply to +919825728291
# Message sent successfully!
```

✅ If you see these logs after sending a WhatsApp → **REPLY IS HAPPENING!**

---

## 📊 Method 2: Use the Monitor Script

Open a **NEW terminal** in Termux:

```bash
cd /workspaces/relaystack

# Make script executable
chmod +x monitor_bot.sh

# Run the monitor
./monitor_bot.sh
```

This will show:
```
📊 Message Count:
   Incoming (your messages): 5
   Outgoing (bot replies):   5
   
✅ BOT IS WORKING! (receiving and replying)

📋 Last 10 Messages:
Time      | Type     | Phone    | Message
09:15:30  | incoming | 9825... | hello
09:15:31  | outgoing | 9825... | 👋 Welcome to Nexora...
```

✅ **If incoming count matches outgoing count** → **REPLYING TO EVERYTHING!**

---

## 🧪 Method 3: Check Database Directly

```bash
# Open database
sqlite3 nexora_whatsapp.db

# See all messages
SELECT direction, phone, message, timestamp FROM whatsapp_messages ORDER BY timestamp DESC LIMIT 10;

# Count incoming vs outgoing
SELECT direction, COUNT(*) as count FROM whatsapp_messages GROUP BY direction;

# Exit
.quit
```

Expected output:
```
incoming | +919825728291 | hello | 2025-02-12 09:15:30
outgoing | +919825728291 | 👋 Welcome to Nexora... | 2025-02-12 09:15:31
incoming | +919825728291 | 1 | 2025-02-12 09:16:00
outgoing | +919825728291 | 🌍 Top Residency... | 2025-02-12 09:16:01
```

---

## ✅ Does the Bot Reply to EVERY Message?

**YES! It replies to EVERYTHING** ✅

### What happens when you send:
- `"hello"` → Gets **MAIN MENU** ✓
- `"1"` → Gets **RESIDENCY OPTIONS** ✓
- `"random xyz"` → Gets **"I don't understand..."** ✓
- `"abc123!@#"` → Gets **INVALID INPUT** message ✓
- Image/Audio → Gets **"Unsupported message type"** ✓

**Every single message gets a reply back!**

---

## 🚨 If Bot is NOT Replying - Checklist:

| Issue | Solution |
|-------|----------|
| No logs appearing | Check if app got crashed - restart: `PORT=8000 python app.py` |
| Logs say "Invalid signature" | This is OK - WhatsApp is just verifying |
| Logs say "WHATSAPP_TOKEN" error | Add it to `.env`: `WHATSAPP_TOKEN=EAAT...` |
| Logs say "PHONE_NUMBER_ID" error | Add it to `.env`: `PHONE_NUMBER_ID=12345...` |
| Message received but no reply | Check webhook URL in Meta Business Suite matches your ngrok/cloudflared URL |
| Database shows 0 outgoing messages | Check if WHATSAPP_TOKEN is valid (test with curl) |

---

## 📱 Test Step by Step:

```
1. Terminal A: Start Flask app
   $ PORT=8000 python app.py
   
2. Terminal B: Run monitor
   $ ./monitor_bot.sh
   
3. Your Phone: Send "hello" to WhatsApp Business number
   
4. Check Results:
   - Terminal A: Should show "Incoming message... Sending reply..."
   - Terminal B: Incoming and Outgoing counts should match
   - Your Phone: Should get automatic reply in 5-30 seconds
   
5. Repeat test with different messages:
   "hi" → menu
   "1" → residency
   "xyz" → error message
```

---

## 🎯 Summary

**Your app automatically replies to EVERY message!**

The only time it doesn't reply is if:
- ❌ App crashed
- ❌ WHATSAPP_TOKEN is invalid
- ❌ Webhook URL is wrong
- ❌ Not on public internet (ngrok/cloudflared not running)

**To verify:** Use `monitor_bot.sh` or check logs in terminal! 🚀
