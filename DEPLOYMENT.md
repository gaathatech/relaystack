# Deployment Guide - Nexora WhatsApp Chatbot

## Production Deployment Options

### Option 1: Render (Recommended)

Render is the easiest option with automatic deployments from GitHub.

#### Steps:

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Initial WhatsApp chatbot"
   git push origin main
   ```

2. **Create Render Service**
   - Go to [render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Connect GitHub repository
   - Auto-filled settings:
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `gunicorn wsgi:app`

3. **Add Environment Variables**
   In Render Dashboard → Environment:
   ```
   FLASK_ENV=production
   WHATSAPP_TOKEN=your_access_token
   PHONE_NUMBER_ID=your_phone_id
   VERIFY_TOKEN=your_verify_token
   DATABASE_URL=postgresql://render_user:password@host/dbname
   ```

4. **Deploy**
   - Click "Create Web Service"
   - Render auto-deploys on every push to main

5. **Configure WhatsApp Webhook**
   - WhatsApp Business App → Settings → Configuration
   - Webhook URL: `https://your-render-app.onrender.com/webhook`
   - Verify Token: Use your `VERIFY_TOKEN`

#### Costs:
- Free tier: 750 hours/month (always free)
- Paid: $7/month per service

---

### Option 2: Railway

Railway has a generous free tier with automatic deployments.

#### Steps:

1. **Create Railway Account**
   - Go to [railway.app](https://railway.app)
   - Sign in with GitHub

2. **Create Project**
   - New Project → Connect GitHub Repo
   - Select relaystack repository

3. **Add PostgreSQL**
   - In Railway Dashboard → Add Service → PostgreSQL
   - Automatically creates DATABASE_URL

4. **Set Environment Variables**
   - Click on Flask service
   - Variables tab:
   ```
   FLASK_ENV=production
   WHATSAPP_TOKEN=your_access_token
   PHONE_NUMBER_ID=your_phone_id
   VERIFY_TOKEN=your_verify_token
   ```

5. **Deploy**
   - Click "Deploy"
   - Railway auto-detects Flask app
   - Uses Procfile for run command

6. **Configure Webhook**
   - Get domain from Railway: `your-app.up.railway.app`
   - WhatsApp webhook: `https://your-app.up.railway.app/webhook`

#### Costs:
- Free tier: $5 credit/month
- No credit card required

---

### Option 3: Docker + Self-Hosted

For running on your own server (AWS, DigitalOcean, VPS, etc)

#### Prerequisites:
- Docker installed
- PostgreSQL or managed database
- Domain name + SSL certificate

#### Steps:

1. **Build Docker Image**
   ```bash
   docker build -t nexora-whatsapp:latest .
   ```

2. **Run Container**
   ```bash
   docker run -d \
     --name nexora \
     -p 80:5000 \
     -e FLASK_ENV=production \
     -e WHATSAPP_TOKEN=your_token \
     -e PHONE_NUMBER_ID=your_id \
     -e VERIFY_TOKEN=your_verify_token \
     -e DATABASE_URL=postgresql://user:pass@db-host/dbname \
     nexora-whatsapp:latest
   ```

3. **With Docker Compose**
   ```bash
   # Create .env.production
   cp .env .env.production
   
   # Edit with production values
   # Then run:
   docker-compose -f docker-compose.yml up -d
   ```

4. **Setup Reverse Proxy (Nginx)**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

5. **SSL Certificate (Let's Encrypt)**
   ```bash
   certbot certonly --nginx -d your-domain.com
   ```

#### Costs:
- Depends on provider (AWS, DigitalOcean, Linode, etc.)
- Typically $5-20/month for entry-level

---

### Option 4: Heroku (Legacy Alternative)

Heroku removed free tier but still works with paid plans.

#### Setup:
```bash
heroku create your-app-name
heroku config:set WHATSAPP_TOKEN=your_token
heroku config:set PHONE_NUMBER_ID=your_id
heroku config:set VERIFY_TOKEN=your_verify_token
git push heroku main
```

---

## Database Setup

### PostgreSQL (Production)

1. **Create Database**
   ```bash
   createdb nexora_whatsapp
   createuser nexora
   ```

2. **Update DATABASE_URL**
   ```
   DATABASE_URL=postgresql://nexora:password@localhost:5432/nexora_whatsapp
   ```

3. **Initialize Database**
   ```bash
   flask init-db
   flask seed-programs
   ```

### SQLite (Development Only)

Use default `.env`:
```
DATABASE_URL=sqlite:///nexora_whatsapp.db
```

---

## Domain Setup

### Point Domain to Your App

#### For Render:
- Render provides `your-app.onrender.com`
- Or add custom domain in Settings → Custom Domains
- Add DNS CNAME record to Render domain

#### For Railway:
- Railway provides `your-app.up.railway.app`
- Add custom domain in project settings

#### For Self-Hosted:
- Point A record to your server IP
- Setup reverse proxy (Nginx)
- Get SSL certificate

---

## SSL/HTTPS (Required by WhatsApp)

**WhatsApp requires HTTPS for webhook!**

### Automatic (Render/Railway):
- Both services provide free HTTPS certificates
- No setup needed

### Self-Hosted:
```bash
# Using Certbot
sudo apt install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d your-domain.com

# Renews automatically
sudo systemctl enable certbot.timer
```

---

## Monitoring & Logs

### Render Logs
```bash
# In Render dashboard or CLI
render logs --service=nexora-service
```

### Railway Logs
- Web UI: Railway Dashboard → Service → Logs

### Self-Hosted
```bash
# Docker logs
docker logs nexora

# System logs
tail -f /var/log/app.log
```

---

## Scaling

### Render
- Auto-scales based on CPU/Memory
- Paid plans: $12+ for multi-instance scaling

### Railway
- Vertical scaling: Increase instance size
- Horizontal scaling: Multiple deployments

### Self-Hosted
- Load balancer (NGINX, HAProxy)
- Multiple app instances
- Database replication

---

## Backup & Maintenance

### Database Backups

#### PostgreSQL
```bash
# Backup
pg_dump nexora_whatsapp > backup.sql

# Restore
psql nexora_whatsapp < backup.sql
```

#### Render/Railway
- Both offer automated daily backups
- Enabled in service settings

### Scheduled Maintenance
```bash
# Cleanup old sessions (run daily)
flask cleanup-sessions

# Backup database (run weekly)
pg_dump $DATABASE_URL > backup-$(date +%Y%m%d).sql
```

---

## Security Checklist

- [ ] HTTPS enabled (WhatsApp requirement)
- [ ] Environment variables set (not in code)
- [ ] Database password strong
- [ ] VERIFY_TOKEN is random string
- [ ] WHATSAPP_TOKEN kept secret
- [ ] .env file in .gitignore
- [ ] Regular database backups
- [ ] Error logs don't expose sensitive data
- [ ] Rate limiting configured (future)
- [ ] Input validation enabled (already in code)

---

## Troubleshooting Deployments

### Webhook Not Receiving Messages
```bash
# Test webhook URL
curl -X GET "https://your-domain.com/webhook?hub.mode=subscribe&hub.verify_token=token&hub.challenge=test"
# Should return: test
```

### Messages Not Sending
1. Check `WHATSAPP_TOKEN` is valid
2. Verify `PHONE_NUMBER_ID` format
3. Check API rate limits
4. Verify recipient phone format with country code

### Database Connection Issues
1. Verify DATABASE_URL format
2. Check credentials
3. Ensure database exists
4. Run `flask init-db` to create tables

### SSL Certificate Issues
- Render/Railway: Auto-handled, no action needed
- Self-hosted: Check certbot renewal cron job
- Force HTTPS: Update app config

---

## Cost Comparison

| Platform | Monthly Cost | Notes |
|----------|------------|-------|
| Render | $0-7/month | Free tier works, Postgres paid |
| Railway | Free-$5/month | Generous free tier, auto scaling |
| Heroku | $25+/month | Dyno minimum |
| AWS | $10-50/month | Highly configurable |
| DigitalOcean | $5-15/month | Need to manage manually |

---

## Post-Deployment

1. **Test Webhook**
   ```bash
   curl "https://your-domain.com/webhook?hub.mode=subscribe&hub.verify_token=YOUR_TOKEN&hub.challenge=challenge"
   ```

2. **Send Test Message**
   - Add business number to WhatsApp contacts
   - Send "hello"
   - Should receive menu

3. **Monitor Logs**
   - Check for errors in logs
   - Verify messages are being stored

4. **Setup Alerts** (optional)
   - Render: Error tracking, uptime monitoring
   - Railway: Health checks, alerts

---

## Version Control

```bash
# Push to GitHub
git add -A
git commit -m "Deploy to production"
git push origin main

# Tag release
git tag -a v1.0.0 -m "Production release"
git push origin v1.0.0
```

---

## Support & Updates

- Check [README.md](README.md) for full documentation
- Review [QUICKSTART.md](QUICKSTART.md) for local setup
- Monitor WhatsApp Business API updates
- Keep dependencies updated: `pip install --upgrade -r requirements.txt`

---

**Last Updated:** February 11, 2024
**Status:** Production Ready ✅
