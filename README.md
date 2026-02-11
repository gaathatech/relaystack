# Nexora Investments - WhatsApp Business Chatbot

A production-ready WhatsApp Business Cloud API chatbot built with Flask for Nexora Investments. The chatbot provides an IVR-style menu system for exploring residency programs, checking eligibility, consulting with specialists, and accessing resources.

## Features

✅ **WhatsApp Integration**
- Webhook-based message reception
- Two-way messaging with WhatsApp Business Cloud API
- Message status tracking (delivered, read, failed)

✅ **IVR Menu System**
- Conversational flow with main menu
- Residency program exploration (Europe, Caribbean, USA, UAE)
- Eligibility checking based on investment budget
- Consultant consultation booking
- Job search assistance
- Consultation booking portal
- Brochure downloads

✅ **Session Management**
- User conversation state tracking
- 30-minute auto-timeout with reset to main menu
- Persistent session memory with JSON metadata

✅ **Lead Management**
- Automatic lead capture from consultations
- Lead database with contact information
- Admin notifications via email

✅ **Database Schema**
- `whatsapp_messages` - All incoming/outgoing messages
- `whatsapp_leads` - Converted leads
- `whatsapp_sessions` - User conversation state
- `investment_programs` - Residency program database

## Tech Stack

- **Python 3.11+**
- **Flask 2.3** - Web framework
- **SQLAlchemy** - ORM
- **PostgreSQL/SQLite** - Database
- **Requests** - HTTP client
- **python-dotenv** - Environment management

## Project Structure

```
/workspaces/relaystack/
├── app.py                          # Main entry point
├── config.py                       # Configuration management
├── requirements.txt                # Python dependencies
├── .env                           # Environment variables (gitignored)
├── .env.example                   # Example env file
├── README.md                      # This file
├── app/
│   ├── __init__.py               # App factory
│   ├── models.py                 # SQLAlchemy models
│   └── whatsapp/
│       ├── __init__.py           # Blueprint initialization
│       ├── routes.py             # Webhook endpoints
│       └── services.py           # Business logic
└── instance/
    └── nexora_whatsapp.db        # SQLite database (development)
```

## Installation & Setup

### 1. Clone Repository

```bash
cd /workspaces/relaystack
git clone https://github.com/gaathatech/relaystack.git .
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env` and update with your credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```env
FLASK_ENV=development
WHATSAPP_TOKEN=your_permanent_access_token
PHONE_NUMBER_ID=your_phone_number_id
VERIFY_TOKEN=your_webhook_verify_token
DATABASE_URL=sqlite:///nexora_whatsapp.db
```

### 5. Initialize Database

```bash
# Initialize database tables
flask init-db

# Seed investment programs
flask seed-programs
```

### 6. Run Application

```bash
python app.py
```

Server starts on `http://localhost:5000`

## API Endpoints

### Webhook Endpoints

#### GET `/webhook` - Verify Webhook
WhatsApp sends a verification request during setup.

**Parameters:**
- `hub.mode` - Always "subscribe"
- `hub.verify_token` - Token to verify
- `hub.challenge` - Challenge string to return

**Response:**
```
hub.challenge value
```

#### POST `/webhook` - Receive Messages
Incoming messages from WhatsApp users.

**Request Body:**
```json
{
  "entry": [
    {
      "changes": [
        {
          "value": {
            "messages": [
              {
                "from": "1234567890",
                "id": "message_id",
                "text": {"body": "Hello"},
                "timestamp": "1234567890"
              }
            ]
          }
        }
      ]
    }
  ]
}
```

**Response:**
```json
{"status": "received"}
```

### Utility Endpoints

#### GET `/webhook/health` - Health Check
```bash
curl http://localhost:5000/webhook/health
```

#### GET `/webhook/stats/<phone>` - User Statistics
Get conversation history for a user.

```bash
curl http://localhost:5000/webhook/stats/1234567890
```

**Response:**
```json
{
  "phone": "1234567890",
  "total_messages": 15,
  "incoming_messages": 8,
  "outgoing_messages": 7,
  "is_lead": true,
  "lead_info": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "interest": "Talk to Consultant",
    "created_at": "2024-02-11T10:30:00"
  }
}
```

#### GET `/` - Service Status
```bash
curl http://localhost:5000/
```

## Conversation Flow

### Main Menu
User sends: `"hi"`, `"hello"`, `"start"`, or `"menu"`

Bot responds with:
```
👋 Welcome to Nexora Investments!

Please choose an option:

1️⃣ Explore Residency Programs
2️⃣ Check Eligibility
3️⃣ Talk to Consultant
4️⃣ Job Search Assistance
5️⃣ Book Consultation
6️⃣ Download Brochure

Reply with a number.
```

### Flow 1: Explore Residency Programs
User selects: `1`

Bot asks for category:
```
🌍 Top Residency Categories:
A. Europe Golden Visa
B. Caribbean Citizenship
C. USA EB-5
D. UAE Residency
Reply with A, B, C, or D
```

Bot returns top 3 programs with links.

### Flow 2: Check Eligibility
User selects: `2`

Bot asks for budget:
```
💰 What is your investment budget in USD?
Reply with amount (example: 150000)
```

Bot returns eligible programs based on budget.

### Flow 3: Talk to Consultant
User selects: `3`

Bot collects:
- Full name
- Email address
- Creates lead entry
- Sends admin notification

### Flow 4: Job Search Assistance
User selects: `4`

Bot asks for country:
```
Which country are you looking for jobs in?
```

Integrates with CareerJet API (placeholder for implementation).

### Flow 5: Book Consultation
User selects: `5`

Bot sends:
```
📅 Book your consultation here:
https://nexorainvestments.com/book
```

### Flow 6: Download Brochure
User selects: `6`

Bot sends:
```
📄 Download our brochure:
https://nexorainvestments.com/brochure.pdf
```

## Database Models

### WhatsAppMessage
```python
- id (Integer, Primary Key)
- phone (String, Indexed)
- message (Text)
- direction (String) - 'incoming' or 'outgoing'
- timestamp (DateTime, Indexed)
- message_id (String, Unique)
- status (String) - 'delivered', 'read', 'failed'
```

### WhatsAppLead
```python
- id (Integer, Primary Key)
- phone (String, Unique, Indexed)
- name (String)
- email (String)
- interest (String)
- budget (Integer)
- country_of_interest (String)
- created_at (DateTime, Indexed)
- updated_at (DateTime)
- notes (Text)
```

### WhatsAppSession
```python
- id (Integer, Primary Key)
- phone (String, Unique, Indexed)
- current_step (String)
- metadata (JSON)
- created_at (DateTime)
- updated_at (DateTime)
- last_activity (DateTime)
- is_active (Boolean)
```

### InvestmentProgram
```python
- id (Integer, Primary Key)
- country (String)
- category (String)
- name (String)
- description (Text)
- minimum_investment (Integer)
- processing_time (String)
- link (String)
- rank (Integer)
```

## Security

### Environment Variables
All sensitive data stored in `.env`:
- `WHATSAPP_TOKEN` - Permanent access token
- `PHONE_NUMBER_ID` - WhatsApp Business Account phone number ID
- `VERIFY_TOKEN` - Webhook verification token

### Webhook Verification
Verify WhatsApp webhook requests using token validation.

Optional: Implement HMAC signature verification (currently commented out).

### Error Handling
- Invalid input returns helpful error message
- Session timeout resets to main menu
- Message failures logged and tracked

## Deployment

### Render
1. Connect GitHub repository
2. Set environment variables in Render dashboard
3. Deploy with `gunicorn app:app`

### Railway
1. Connect GitHub repository
2. Add environment variables
3. Platform auto-detects Flask app

### Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
```

## Testing

### Manual Testing with cURL

Verify webhook:
```bash
curl "http://localhost:5000/webhook?hub.mode=subscribe&hub.verify_token=your_token&hub.challenge=test_challenge"
```

Send test message:
```bash
curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "from": "1234567890",
            "id": "msg_123",
            "text": {"body": "hi"},
            "timestamp": "1234567890"
          }]
        }
      }]
    }]
  }'
```

## Common Issues

### Issue: Webhook not receiving messages
**Solution:**
1. Verify VERIFY_TOKEN matches WhatsApp Business Account settings
2. Ensure webhook URL is publicly accessible
3. Check PHONE_NUMBER_ID and ACCESS_TOKEN are correct
4. Enable test messages in WhatsApp Business Account

### Issue: Messages not sending
**Solution:**
1. Verify permanent ACCESS_TOKEN is valid
2. Check PHONE_NUMBER_ID format
3. Ensure rated recipient number is valid
4. Check WhatsApp API rate limits

### Issue: Database errors
**Solution:**
1. Run `flask init-db` to reinitialize
2. Check DATABASE_URL environment variable
3. For PostgreSQL, verify connection string format

## Future Enhancements

- [ ] Email notifications to admin (SendGrid/SMTP integration)
- [ ] Integration with CareerJet API for job search
- [ ] Media handling (images, documents)
- [ ] Multi-language support
- [ ] Analytics dashboard
- [ ] WhatsApp template messages
- [ ] Payment integration for bookings
- [ ] CRM system integration

## API Documentation

Complete endpoint documentation available at `/docs` (when Swagger UI is added).

## Contributing

Follow PEP 8 style guide. Test all changes before pushing.

## License

Proprietary - Nexora Investments 2024

## Support

For issues or questions:
- Email: gaatha.aidni@gmail.com
- GitHub Issues: [Create issue]

---

**Last Updated:** February 11, 2024
**Version:** 1.0.0
**Status:** Production Ready ✅
