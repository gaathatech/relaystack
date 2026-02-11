# Quick Start Guide - Nexora WhatsApp Chatbot

## 5-Minute Setup

### 1. Install Dependencies
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Credentials
Edit `.env` and add:
```env
WHATSAPP_TOKEN=your_permanent_access_token
PHONE_NUMBER_ID=your_phone_number_id
VERIFY_TOKEN=random_string_you_choose
```

Get these from:
- **WhatsApp Business App** → Settings → Business Accounts → Access Tokens
- **Phone Number ID** → WhatsApp Business Account → Phone Numbers

### 3. Start Server
```bash
python app.py
```

Server runs on `http://localhost:5000`

### 4. Configure WhatsApp Webhook
In WhatsApp Business Account:

1. Go to **Settings** → **Configuration**
2. Set webhook URL: `https://your-domain.com/webhook`
3. Verify Token: Use value from `.env` `VERIFY_TOKEN`
4. Subscribe to messages, message_status, message_template_status_update

### 5. Test
Send WhatsApp message to your business number with text: `hello`

You should get menu response!

---

## Using SQLite (Development)

Default setup uses SQLite. Database file: `nexora_whatsapp.db`

```bash
# Initialize database
flask init-db

# Seed programs
flask seed-programs

# Reset database (careful!)
flask reset-db
```

---

## Using PostgreSQL (Production)

Update `.env`:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/nexora_whatsapp
```

Then:
```bash
flask init-db
flask seed-programs
```

---

## Using Docker

```bash
# With PostgreSQL
docker-compose up

# Or just Flask (needs manual DB setup)
docker build -t nexora .
docker run -p 5000:5000 --env-file .env nexora
```

---

## Testing

```bash
pip install pytest
pytest tests/ -v
```

---

## Deploy to Render

1. Push to GitHub
2. Create new Render service
3. Connect GitHub repo
4. Add environment variables in Render dashboard
5. Deploy!

---

## Deploy to Railway

1. Push to GitHub
2. Create new Railway project
3. Connect GitHub repo
4. Add environment variables
5. Auto-deploys!

---

## WhatsApp Message Flow

```
User: "hello"
  ↓
Flask receives webhook POST
  ↓
Routes to WhatsAppService.process_message()
  ↓
Returns main menu
  ↓
Flask calls WhatsAppService.send_message()
  ↓
WhatsApp Business Cloud API
  ↓
User receives message
```

---

## Troubleshooting

### Webhook not receiving messages
```bash
# Check webhook verification
curl "http://localhost:5000/webhook?hub.mode=subscribe&hub.verify_token=your_verify_token&hub.challenge=test"
```

Should return: `test`

### Database errors
```bash
# Reset database
flask reset-db
flask init-db
flask seed-programs
```

### Messages not sending
1. Check `WHATSAPP_TOKEN` is valid
2. Check `PHONE_NUMBER_ID` format
3. Check recipient number format (with country code)
4. Check WhatsApp rate limits

---

## Useful Commands

```bash
# Initialize database
flask init-db

# Seed programs
flask seed-programs

# Reset database
flask reset-db

# Run tests
pytest tests/ -v

# Check syntax
python -m py_compile app.py app/models.py app/whatsapp/*.py

# Format code (if using black)
black app/ tests/

# Lint code (if using flake8)
flake8 app/ tests/
```

---

## File Structure Reference

```
├── app.py                 ← Main entry point
├── wsgi.py               ← Production entry point
├── config.py             ← Configuration
├── requirements.txt      ← Python packages
├── .env                  ← Secrets (gitignored)
├── Procfile              ← Render/Railway deployment
├── Dockerfile            ← Docker image
├── docker-compose.yml    ← Local Docker setup
├── app/
│   ├── __init__.py       ← Flask app factory
│   ├── models.py         ← Database models
│   └── whatsapp/
│       ├── __init__.py
│       ├── routes.py     ← Webhook endpoints
│       └── services.py   ← Business logic
└── tests/
    ├── __init__.py
    └── test_whatsapp.py  ← Unit tests
```

---

## Next Steps

1. ✅ Setup complete
2. Configure WhatsApp webhook
3. Test with real messages
4. Customize menu options
5. Integrate email notifications
6. Add analytics
7. Deploy to production

---

## Support

Email: gaatha.aidni@gmail.com

---

**Version:** 1.0.0
**Last Updated:** Feb 11, 2024
