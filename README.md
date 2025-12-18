# RelayStack
Automated WhatsApp sender demo built by Nexora.

## Overview
RelayStack is a small Flask + Selenium utility for sending WhatsApp messages via WhatsApp Web and logging results to an Excel file.

> NOTE: This project is a demo and not production ready. Review security, rate limits, and legal compliance before using it for real campaigns.

## Setup
1. Create and activate a Python virtualenv
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Provide a Chrome/Chromium binary and optionally chromedriver path via environment variables:

```bash
export CHROME_BINARY=/usr/bin/chromium
export CHROMEDRIVER_PATH=/usr/bin/chromedriver
```

If you don't set `CHROMEDRIVER_PATH`, `webdriver-manager` will attempt to download a matching driver.

By default RelayStack removes the local WhatsApp Web profile after each send so that the next run will require scanning the QR code again (this helps ensure per-run session clearing). If you want to preserve the logged-in session, set:

```bash
export KEEP_WHATSAPP_SESSION=1
```

4. Run the Flask app:

```bash
python app.py
```

5. Open http://localhost:5000 and scan the QR code in WhatsApp Web when prompted. After a send completes the app will clear the session so the next run will ask for a new QR scan unless `KEEP_WHATSAPP_SESSION` is set.

## Legal & Privacy
- A sample Privacy Policy and User Agreement are included in the `templates/` folder. These are **templates only** and should be reviewed and customized by legal counsel for production use.

## Multi-platform roadmap
RelayStack is currently implemented for WhatsApp Web only. Adding additional providers is possible but varies by platform:

- **Telegram:** easiest via the Bot API if recipients have started the bot; for sending as a user account, tools like Telethon can be used (but require storing session data and handling 2FA).
- **Viber:** Viber provides a public REST API for business accounts (requires registering an account and obtaining API keys); user-account flows may require web automation.
- **WhatsApp Business API / Cloud API:** paid and intended for business flows; different provisioning and cost model.
- **Other apps (Errattai, etc.):** feasibility depends on whether the platform offers an API or a programmatic agent.

User-account flows (QR / per-user sessions)

RelayStack now supports creating per-user accounts (Accounts page) and starting a WhatsApp Web login flow per account that opens a browser profile for scanning the QR code. The server keeps the profile directory (under `user_data/<provider>/<account_id>`) so subsequent sends use the logged-in account.

Important security notes:
- Session directories currently live on the server and should be encrypted at rest for production. Use `sessions.py` to store small session metadata and store session files securely.
- Do not commit session files to version control.

Next steps I can take if you want:
- Implement encrypted session file storage for profiles (I have `sessions.py` ready and can integrate it).
- Add Telethon-based Telegram user-account provider to allow user login and persistent sessions.
- Add UI controls to select which account to use when sending messages.

If you'd like to deploy to Render, this repo includes a `Dockerfile`, `run.sh`, and a sample `render.yaml` to make deployment straightforward. Please note the following deployment notes:

- Environment variables you must set in Render (use Render Secrets): `SESSION_KEY`, `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_BOT_TOKEN` (optional), and `RATE_LIMIT_PER_MIN` (optional).
- For WhatsApp QR flows, running the browser headlessly on Render means the QR may not be directly scannable from your machine. For production usage prefer WhatsApp Business Cloud API or run the driver on a machine you control where you can access the browser UI (or set up a secure remote debugging/VNC solution).
- By default, `user_data/` and session files are stored on container filesystem (ephemeral). If you need persistence across restarts, attach a Persistent Disk in Render and mount it at `/app` or switch to S3-backed session storage.

See `Dockerfile`, `run.sh` and `render.yaml` for the deployment setup. Tell me if you want me to add a `docker-compose.yml` for local Docker testing or set up a Render persistent disk example and I will add it.

## Contributing
PRs welcome. Please ensure you do not include real user data in commits.

---
© 2025 Nexora. All rights reserved.
