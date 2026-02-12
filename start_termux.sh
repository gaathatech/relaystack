#!/usr/bin/env bash
set -e

# start_termux.sh — helper to run the app and ngrok on Termux
# Place this in the project root and run: ./start_termux.sh

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$REPO_DIR/venv"
NGROK_PATH="$REPO_DIR/ngrok"
PORT=${PORT:-8000}
LOG="$REPO_DIR/relaystack.log"

echo "Using repo: $REPO_DIR"

# create venv and install deps if needed
if [ ! -d "$VENV" ]; then
  echo "Creating virtualenv and installing requirements..."
  python -m venv "$VENV"
  source "$VENV/bin/activate"
  pip install --upgrade pip
  if [ -f "$REPO_DIR/requirements.txt" ]; then
    pip install -r "$REPO_DIR/requirements.txt"
  fi
else
  source "$VENV/bin/activate"
fi

export PORT

echo "Starting Flask app on port $PORT (logs -> $LOG)"
nohup python "$REPO_DIR/app.py" > "$LOG" 2>&1 &

sleep 1

if [ -x "$NGROK_PATH" ]; then
  echo "Starting ngrok..."
  nohup "$NGROK_PATH" http "$PORT" > /dev/null 2>&1 &

  # wait for ngrok local API and extract public url
  PUBLIC_URL=""
  for i in {1..20}; do
    sleep 0.5
    TUNNELS=$(curl -s http://127.0.0.1:4040/api/tunnels || true)
    PUBLIC_URL=$(echo "$TUNNELS" | grep -oE 'https://[0-9a-zA-Z.-]+' | head -n1 || true)
    if [ -n "$PUBLIC_URL" ]; then break; fi
  done

  if [ -n "$PUBLIC_URL" ]; then
    echo "ngrok public URL: $PUBLIC_URL"
    echo "Webhook callback URL: $PUBLIC_URL/webhook"
    echo
    echo "Set your Meta webhook callback URL to: $PUBLIC_URL/webhook"
    echo "Use VERIFY_TOKEN value from your .env as the verify token."
    echo
    echo "Example webhook registration (app-level, needs <APP_ID> and app access token):"
    echo "curl -X POST \"https://graph.facebook.com/<APP_ID>/subscriptions\" -d 'object=whatsapp' -d 'callback_url=${PUBLIC_URL}/webhook' -d 'verify_token=${VERIFY_TOKEN}' -d 'fields=messages' -d 'access_token=<APP_ACCESS_TOKEN>'"
  else
    echo "ngrok started but couldn't detect public URL. Check ngrok UI: http://127.0.0.1:4040"
  fi
else
  echo "ngrok executable not found at $NGROK_PATH"
  echo "Start ngrok manually: ./ngrok http $PORT"
fi

echo "App logs: $LOG"
echo "To stop the server, find the PID and kill it: pkill -f 'python $REPO_DIR/app.py' || true"

echo "Note: make this script executable: chmod +x start_termux.sh"
