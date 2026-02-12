# Termux Quick Checklist

- Clone repo: `git clone <your-repo-url> relaystack && cd relaystack`
- Install packages: `pkg update && pkg upgrade -y`
- Install essentials: `pkg install python git wget unzip clang make pkg-config -y`
- Create venv: `python -m venv venv && source venv/bin/activate`
- Install deps: `pip install --upgrade pip && pip install -r requirements.txt`
- Create `.env` (see DEPLOY_COMMANDS.md for vars)
- Run app: `PORT=8000 python app.py` or `./start_termux.sh`
- Expose with ngrok/cloudflared and set webhook to `https://<public>/webhook`
- Notes: keep secrets out of Git and install any additional dev headers (openssl, libffi) if pip build fails
