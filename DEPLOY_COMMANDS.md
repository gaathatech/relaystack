# Relaystack — Deployment & Quick Commands

This file collects the commands for running the app on Termux (phone), exposing it with `ngrok` or `cloudflared`, and performing common WhatsApp Graph API calls used during setup and testing.

---

## Environment variables (example)

Set these in a `.env` or export them in your shell before running commands:

```bash
WHATSAPP_TOKEN=EAAT3Q4oZCLo0BQiETys... (keep secret)
PHONE_NUMBER_ID=888107177721942
WABA_ID=1132341818969288
VERIFY_TOKEN=your_verify_token_here
PORT=8000
DATABASE_URL=sqlite:///nexora_whatsapp.db
```

---

## Termux — prepare environment

```bash
# update & install
pkg update && pkg upgrade -y
pkg install python git wget unzip -y

# clone project (or copy files into Termux home)
git clone <your-repo-url> relaystack
cd relaystack

# virtualenv and deps
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Create `.env` (example):

```bash
cat > .env <<EOF
WHATSAPP_TOKEN=${WHATSAPP_TOKEN}
PHONE_NUMBER_ID=${PHONE_NUMBER_ID}
VERIFY_TOKEN=${VERIFY_TOKEN}
PORT=8000
DATABASE_URL=sqlite:///nexora_whatsapp.db
EOF
```

Run the app on alternate port (8000):

```bash
source venv/bin/activate
python app.py
# or explicitly: PORT=8000 python app.py
```

---

## Expose locally to the internet

Option A — ngrok (quick test):

```bash
# download ngrok for your device and authenticate
./ngrok http 8000
# copy the https forwarding URL (e.g. https://abcd1234.ngrok.io)
```

Option B — cloudflared (Cloudflare Tunnel):

```bash
# install cloudflared for your platform
cloudflared tunnel --url http://localhost:8000
# copy the provided public URL
```

Use the public https URL as your webhook endpoint: `https://<public>/webhook`

---

## Meta / WhatsApp Graph API — useful calls

# 1) Validate token / get profile
```bash
curl "https://graph.facebook.com/v18.0/me?access_token=${WHATSAPP_TOKEN}"
```

# 2) List connected Pages
```bash
curl "https://graph.facebook.com/v18.0/me/accounts?access_token=${WHATSAPP_TOKEN}"
```

# 3) List businesses you manage
```bash
curl "https://graph.facebook.com/v18.0/me?fields=businesses&access_token=${WHATSAPP_TOKEN}"
```

# 4) List owned WABA IDs for a Business
```bash
curl "https://graph.facebook.com/v18.0/<BUSINESS_ID>/owned_whatsapp_business_accounts?fields=id,phone_numbers{phone_number,id}&access_token=${WHATSAPP_TOKEN}"
```

# 5) List phone numbers for a WABA
```bash
curl "https://graph.facebook.com/v18.0/${WABA_ID}/phone_numbers?fields=id,phone_number,display_phone_number&access_token=${WHATSAPP_TOKEN}"
```

# 6) Send a text message (server-initiated)
```bash
curl -X POST "https://graph.facebook.com/v18.0/${PHONE_NUMBER_ID}/messages" \
  -H "Authorization: Bearer ${WHATSAPP_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "messaging_product": "whatsapp",
    "to": "919825728291",
    "type": "text",
    "text": { "body": "Hello from Relaystack!" }
  }'
```

# 7) Verify webhook (Graph API will perform GET to your callback):
Set callback URL to `https://<public>/webhook` and verify token to your `VERIFY_TOKEN`.

---

## Common debugging commands

```bash
# Check app root
curl -i https://<public>/

# Check health endpoint
curl -i https://<public>/webhook/health

# Re-check token and pages
curl "https://graph.facebook.com/v18.0/me?access_token=${WHATSAPP_TOKEN}"
curl "https://graph.facebook.com/v18.0/me/accounts?access_token=${WHATSAPP_TOKEN}"
```

---

## Automate start (optional helper)

Create a simple script `start_termux.sh` to activate venv, run app, and start ngrok (if you have it):

```bash
#!/bin/bash
set -e
source venv/bin/activate
export PORT=${PORT:-8000}
python app.py &
NGROK_PATH=./ngrok
if [ -x "$NGROK_PATH" ]; then
  $NGROK_PATH http $PORT
else
  echo "ngrok not found; start it manually: ./ngrok http $PORT"
fi
```

Make executable:
```bash
chmod +x start_termux.sh
```

---

## Security notes

- Never commit `.env` to source control. Keep secrets out of Git.
- Rotate `WHATSAPP_TOKEN` if it is exposed publicly.

---

If you'd like, I can also add `start_termux.sh` to the repo and a curl command to register the webhook programmatically once you provide the public URL. 
