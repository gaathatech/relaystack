# 🔐 WhatsApp Token Verification & Setup Guide

## Token Validation Result

**Status:** ❌ Token appears to be invalid or expired

**Error:** `Invalid OAuth access token - Cannot parse access token`

---

## ✅ How to Get a VALID Token

### Step 1: Go to Meta Business Suite
1. Open: https://business.facebook.com
2. Sign in with your Meta/Facebook account
3. Select "Nexora by Phoenix Intl" business account

### Step 2: Navigate to WhatsApp Business App
```
Home → Apps → WhatsApp Business Platform
  OR
Left Menu → WhatsApp → API Setup
```

### Step 3: Get Your Permanent Access Token

**Option A: From API Setup**
1. Go to: WhatsApp Business App → API Setup
2. Look for "Permanent Access Token"
3. Click "Generate Token" if needed
4. Click "Copy" to copy the token

**Option B: From Business Settings**
1. Go to: Settings → Business Apps
2. Find "WhatsApp" app
3. Click it → API Credentials
4. Copy "Permanent Access Token"

**Option C: From System User**
1. Go to: Settings → System Users
2. Look for system user tied to WhatsApp
3. Click it → Generate Access Token
4. Select permissions: `whatsapp_business_messaging`, `whatsapp_business_management`
5. Expiry: Select "Never" for permanent token
6. Copy the token

### Step 4: Get Your Phone Number ID

1. In WhatsApp Business App Settings
2. Go to: Phone Numbers
3. Find: +919825728291
4. Click it
5. Copy the "Phone Number ID" (looks like: `12345...` - 25+ digits)

---

## 🔄 Token Format Check

Your token should:
- ✅ Start with `EAAT` for WhatsApp tokens
- ✅ Be 200+ characters long
- ✅ No spaces or line breaks
- ✅ Recently generated (not months old)

**Current token length:** ~200 chars ✅ Format correct ❓ Validity: ❌

---

## 📝 Update .env File

Once you have the valid credentials:

```env
WHATSAPP_TOKEN=<paste_your_permanent_token>
PHONE_NUMBER_ID=<paste_your_phone_id>
VERIFY_TOKEN=nexora_verify_token_2024
WHATSAPP_BUSINESS_PHONE=+919825728291
```

---

## 🧪 Test Your Token

After updating .env, run:

```bash
python3 << 'EOF'
import requests
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('WHATSAPP_TOKEN')

print("Testing token...")
response = requests.get(
    "https://graph.instagram.com/me",
    headers={"Authorization": f"Bearer {token}"}
)

if response.status_code == 200:
    print("✅ Token is VALID!")
    print(f"Account: {response.json()}")
else:
    print(f"❌ Invalid token: {response.json()}")
EOF
```

---

## 🛠️ Common Issues

### "Invalid OAuth access token"
- Token is expired or malformed
- **Solution:** Generate a new permanent token

### "Access token requires permission"
- Token lacks required permissions
- **Solution:** 
  1. Go to System User settings
  2. Add permissions: `whatsapp_business_messaging`, `whatsapp_business_management`
  3. Generate new token

### "Phone number not found"
- Phone Number ID is incorrect
- **Solution:** 
  1. Verify phone number format (should already be +919825728291)
  2. Copy exact 25+ digit ID from WhatsApp settings

### Token keeps expiring
- You're using a short-lived token
- **Solution:** 
  1. Generate a PERMANENT access token
  2. Not a short-lived one
  3. Permanent tokens don't expire unless revoked

---

## 📱 Webhook Configuration

After token is verified, configure in WhatsApp:

1. Go to: WhatsApp Business App → Configuration
2. **Webhook URL:** `https://your-domain.com/webhook`
3. **Verify Token:** `nexora_verify_token_2024`
4. **Subscribe to events:**
   - `messages`
   - `message_status`
   - `message_template_status_update`

---

## ✨ Once Token is Valid

1. Update .env with valid token
2. Run: `flask init-db && flask seed-programs`
3. Start server: `python app.py`
4. Test locally: `curl http://localhost:5000/webhook/health`
5. Send test message to WhatsApp number
6. Deploy to production

---

## 🔗 Quick Links

- Meta Business Suite: https://business.facebook.com
- WhatsApp Business API Docs: https://developers.facebook.com/docs/whatsapp/cloud-api
- System Users Guide: https://developers.facebook.com/docs/development/register
- API Reference: https://developers.facebook.com/docs/whatsapp/cloud-api/reference

---

**Status:** Waiting for valid token to proceed 🔄

Once you have the valid token, update `.env` and reply with the PHONE_NUMBER_ID.
