from flask import Flask, render_template, request, redirect, url_for
import sender
from urllib.parse import quote
import uuid
import os
import threading
import time
import logging
from utils import clean_number

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

app = Flask(__name__)

sending_thread = None
stop_flag = False


def background_send(numbers, message, log_path, preserve_session=False, provider='whatsapp', account_id='default'):
    """Background sending loop used by the Flask UI.

    Supports multiple providers. `provider` selects which send function to call.
    """
    global stop_flag
    stop_flag = False

    if provider == 'whatsapp':
        from ratelimit import consume
        for i, number in enumerate(numbers):
            if stop_flag:
                logging.info("Sending stopped by user.")
                break
            # Enforce consent for WhatsApp user-account sending
            if not request.form.get('consent') and provider == 'whatsapp':
                logging.warning('Consent not provided; aborting')
                break
            # Rate limit per account
            if not consume('whatsapp', account_id, 1):
                logging.warning('Rate limit exceeded for %s/%s', provider, account_id)
                # Append failed reason to log
                import openpyxl
                wb = openpyxl.load_workbook(log_path) if os.path.exists(log_path) else openpyxl.Workbook()
                ws = wb.active
                ws.append([number, 'Rate limited', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), account_id])
                wb.save(log_path)
                continue

        # Close driver and optionally preserve the session
        sender.close_driver(preserve_session=bool(preserve_session))

    elif provider == 'telegram':
        # Prefer user-account Telegram if a session exists for the account_id
        from sessions import load_session
        sess = load_session('telegram', account_id)
        if sess and 'string' in sess:
            from providers.telegram_user import send_telegram_user_messages_with_log
            for i, chat in enumerate(numbers):
                if stop_flag:
                    logging.info("Sending stopped by user.")
                    break
                try:
                    send_telegram_user_messages_with_log(account_id, [chat], message, log_path, append=True)
                except Exception as e:
                    logging.exception('Telegram(user) send error for %s: %s', chat, e)
        else:
            # Fallback to Bot API provider
            from providers.telegram import send_telegram_messages_with_log
            for i, chat in enumerate(numbers):
                if stop_flag:
                    logging.info("Sending stopped by user.")
                    break
                try:
                    send_telegram_messages_with_log([chat], message, log_path, append=True)
                except Exception as e:
                    logging.exception('Telegram(bot) send error for %s: %s', chat, e)

    else:
        logging.warning('Unsupported provider requested: %s', provider)

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')


@app.route('/terms')
def terms():
    return render_template('terms.html')


@app.route('/', methods=['GET', 'POST'])
def index():
    global sending_thread

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'Stop':
            global stop_flag
            stop_flag = True
            return render_template('index.html', uploaded=True, status='⛔ Stopped')

        provider = request.form.get('provider', 'whatsapp')
        numbers_raw = request.form.get('numbers', '')
        message = request.form.get('message', '')
        preserve_session = True if request.form.get('preserve_session') in ('on','true','1') else False
        account_id = request.form.get('account_id', 'default')

        if not numbers_raw.strip() or not message.strip():
            return render_template('index.html', uploaded=False, error="❌ Please paste numbers and enter a message.")

        # Consent check
        if not request.form.get('consent'):
            return render_template('index.html', uploaded=False, error="❌ You must confirm recipient consent before sending messages.")

        numbers = [clean_number(num.strip()) for num in numbers_raw.split('\n') if num.strip()]
        log_filename = f'{provider}_log_{uuid.uuid4().hex[:6]}.xlsx'
        log_path = os.path.join('static', 'logs', log_filename)
        os.makedirs('static/logs', exist_ok=True)

        if provider != 'whatsapp':
            return render_template('index.html', uploaded=False, error=f"⚠️ Provider '{provider}' is not yet implemented.")

        if sending_thread and sending_thread.is_alive():
            return render_template('index.html', uploaded=False, error="⚠️ Sending already in progress...")

        # Rate limiting per account
        from rate_limiter import allow_send
        if not allow_send(provider, account_id, count=len(numbers)):
            return render_template('index.html', uploaded=False, error=f"⚠️ Rate limit exceeded for account {account_id}. Try later.")

        sending_thread = threading.Thread(target=background_send, args=(numbers, message, log_path, preserve_session, provider, account_id))
        sending_thread.start()

        logging.info('Started background sending thread for %d numbers', len(numbers))
        return render_template('index.html', uploaded=True, count=len(numbers), log_file=log_filename, status="✅ Sending started...")

    # GET - include account list for template
    accounts = []
    base = os.path.join(sender.BASE_USER_DATA_DIR, 'whatsapp')
    if os.path.exists(base):
        for name in os.listdir(base):
            path = os.path.join(base, name)
            if os.path.isdir(path):
                accounts.append({'provider': 'whatsapp', 'account_id': name})
    return render_template('index.html', uploaded=False, accounts=accounts)


@app.route('/status/whatsapp')
def whatsapp_status():
    try:
        # default account 'default'
        ready = sender.check_whatsapp_logged_in(account_id='default')
        return { 'ready': bool(ready) }
    except Exception as e:
        logging.exception('Failed to check whatsapp status')
        return { 'ready': False, 'error': str(e) }


@app.route('/accounts')
def accounts_list():
    """List known accounts (based on profile dirs)."""
    accounts = []
    # WhatsApp accounts
    base = os.path.join(sender.BASE_USER_DATA_DIR, 'whatsapp')
    if os.path.exists(base):
        for name in os.listdir(base):
            path = os.path.join(base, name)
            if os.path.isdir(path):
                accounts.append({'provider': 'whatsapp', 'account_id': name})
    # Telegram accounts (sessions stored via sessions.py)
    from sessions import SESSIONS_DIR
    tg_dir = SESSIONS_DIR
    for f in tg_dir.glob('telegram--*.session'):
        name = f.name.replace('telegram--', '').replace('.session','')
        accounts.append({'provider': 'telegram', 'account_id': name})
    return render_template('accounts.html', accounts=accounts)


@app.route('/accounts/create', methods=['POST'])
def accounts_create():
    provider = request.form.get('provider')
    account_id = request.form.get('account_id')
    if not account_id:
        return redirect(url_for('accounts_list'))

    if provider == 'whatsapp':
        profile_dir = os.path.join(sender.BASE_USER_DATA_DIR, provider, account_id)
        os.makedirs(profile_dir, exist_ok=True)
    elif provider == 'telegram':
        # create a placeholder session file via sessions.save_session with empty content
        from sessions import save_session
        save_session('telegram', account_id, {})
    return redirect(url_for('accounts_list'))

@app.route('/accounts/<provider>/<account_id>/start_login')
def accounts_start_login(provider, account_id):
    if provider == 'whatsapp':
        # Start a background thread to open a browser with the profile and wait for login
        def _bg():
            try:
                sender.init_driver_for_profile(provider, account_id, wait_for_login=True, timeout=300)
                # Do not remove the profile; keep it so the account is logged in for next runs
                logging.info('Login flow finished for %s/%s', provider, account_id)
            except Exception:
                logging.exception('Login flow failed')

        threading.Thread(target=_bg, daemon=True).start()
        return redirect(url_for('accounts_list'))


@app.route('/accounts/telegram/<account_id>/send_code', methods=['POST'])
def accounts_telegram_send_code(account_id, provider='telegram'):
    phone = request.form.get('phone')
    if not phone:
        return redirect(url_for('accounts_list'))
    try:
        from providers.telegram_user import start_telegram_login
        start_telegram_login(phone, provider, account_id)
        return render_template('accounts_telegram_verify.html', provider=provider, account_id=account_id)
    except Exception as e:
        logging.exception('Failed to start telegram login')
        return redirect(url_for('accounts_list'))


@app.route('/accounts/telegram/<account_id>/verify', methods=['POST'])
def accounts_telegram_verify(account_id, provider='telegram'):
    code = request.form.get('code')
    try:
        from providers.telegram_user import complete_telegram_login
        complete_telegram_login(code, provider, account_id)
        return redirect(url_for('accounts_list'))
    except Exception as e:
        logging.exception('Telegram login verify failed')
        return redirect(url_for('accounts_list'))
        # Render phone entry form for Telegram login
        return render_template('accounts_telegram_login.html', provider=provider, account_id=account_id)

    return redirect(url_for('accounts_list'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
