from flask import Flask, render_template, request, redirect, url_for, session, flash
import sender
from urllib.parse import quote
import uuid
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash
import threading
import time
import logging
from utils import clean_number
import base64
import sqlite3
from sessions import SESSIONS_DIR

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'change-me-please')

# Simple file-backed user store (sufficient for small deployments).
# Store users DB inside the sessions directory so a single persistent mount
# can cover both sessions and user data.
USERS_DB = os.environ.get('USERS_DB_PATH', os.path.join(str(SESSIONS_DIR), 'users.db'))

def _get_db_conn():
    conn = sqlite3.connect(USERS_DB)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_users_db():
    if not os.path.exists(USERS_DB):
        conn = _get_db_conn()
        cur = conn.cursor()
        cur.execute('CREATE TABLE users (username TEXT PRIMARY KEY, password_hash TEXT NOT NULL)')
        conn.commit()
        conn.close()

    # Create default admin user if none exist
    try:
        conn = _get_db_conn()
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) as c FROM users')
        row = cur.fetchone()
        if row and row['c'] == 0:
            admin_user = os.environ.get('ADMIN_USER', 'admin')
            admin_pass = os.environ.get('ADMIN_PASS', 'adminpass')
            cur.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (admin_user, generate_password_hash(admin_pass)))
            conn.commit()
            logging.debug('Created default admin user: %s', admin_user)
    except Exception:
        logging.exception('Failed to create default admin user')
    finally:
        try:
            conn.close()
        except Exception:
            pass



def create_user(username, password):
    ensure_users_db()
    try:
        conn = _get_db_conn()
        cur = conn.cursor()
        cur.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, generate_password_hash(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass

def authenticate_user(username, password):
    ensure_users_db()
    conn = _get_db_conn()
    cur = conn.cursor()
    cur.execute('SELECT password_hash FROM users WHERE username=?', (username,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return False
    return check_password_hash(row['password_hash'], password)


def is_admin(username):
    return username == 'admin'  # Simple check; can be extended


def get_all_users():
    ensure_users_db()
    conn = _get_db_conn()
    cur = conn.cursor()
    cur.execute('SELECT username FROM users')
    rows = cur.fetchall()
    conn.close()
    return [row['username'] for row in rows]


def delete_user(username):
    if username == 'admin':
        return False  # Prevent deleting admin
    ensure_users_db()
    conn = _get_db_conn()
    cur = conn.cursor()
    cur.execute('DELETE FROM users WHERE username=?', (username,))
    conn.commit()
    conn.close()
    return True


from functools import wraps
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        # Allow disabling login requirement via config or env var for testing/dev.
        require = app.config.get('REQUIRE_LOGIN', os.environ.get('REQUIRE_LOGIN', '0') == '1')
        if not require:
            return f(*args, **kwargs)
        if not session.get('user'):
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return wrapper


@app.route('/accounts/<provider>/<account_id>/qr_image')
@login_required
def accounts_qr_image(provider, account_id):
    try:
        if provider == 'whatsapp':
            png = sender.get_login_screenshot(provider, account_id, timeout=5)
            if png:
                data = base64.b64encode(png).decode()
                return {'qr': f"data:image/png;base64,{data}"}
    except Exception:
        logging.exception('Failed to fetch qr image for %s/%s', provider, account_id)
    return {'qr': None}

sending_thread = None
stop_flag = False


def background_send(numbers, message, log_path, preserve_session=False, provider='whatsapp', account_id='default', consent=False):
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
            if not consent and provider == 'whatsapp':
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
@login_required
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
        consent = request.form.get('consent') == 'on'
        if not consent:
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

        sending_thread = threading.Thread(target=background_send, args=(numbers, message, log_path, preserve_session, provider, account_id, consent))
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


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('Please provide username and password', 'error')
            return render_template('signup.html')
        if create_user(username, password):
            session['user'] = username
            flash('Account created — welcome!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Username already exists', 'error')
            return render_template('signup.html')
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if authenticate_user(username, password):
            session['user'] = username
            flash('Logged in', 'success')
            next_url = request.args.get('next') or url_for('index')
            return redirect(next_url)
        else:
            flash('Invalid credentials', 'error')
            return render_template('login.html')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out', 'info')
    return redirect(url_for('login'))


@app.route('/admin')
@login_required
def admin():
    if not is_admin(session.get('user')):
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    users = get_all_users()
    # Also get accounts
    accounts = []
    base = os.path.join(sender.BASE_USER_DATA_DIR, 'whatsapp')
    if os.path.exists(base):
        for name in os.listdir(base):
            path = os.path.join(base, name)
            if os.path.isdir(path):
                accounts.append({'provider': 'whatsapp', 'account_id': name})
    from sessions import SESSIONS_DIR
    tg_dir = SESSIONS_DIR
    for f in tg_dir.glob('telegram--*.session'):
        name = f.name.replace('telegram--', '').replace('.session','')
        accounts.append({'provider': 'telegram', 'account_id': name})
    return render_template('admin.html', users=users, accounts=accounts)


@app.route('/admin/delete_user/<username>', methods=['POST'])
@login_required
def admin_delete_user(username):
    if not is_admin(session.get('user')):
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    if delete_user(username):
        flash(f'User {username} deleted', 'success')
    else:
        flash('Cannot delete user', 'error')
    return redirect(url_for('admin'))


@app.route('/status/whatsapp')
@login_required
def whatsapp_status():
    try:
        # default account 'default'
        ready = sender.check_whatsapp_logged_in(account_id='default')
        return { 'ready': bool(ready) }
    except Exception as e:
        logging.exception('Failed to check whatsapp status')
        return { 'ready': False, 'error': str(e) }


@app.route('/accounts')
@login_required
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
@login_required
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
@login_required
def accounts_start_login(provider, account_id):
    if provider != 'whatsapp':
        return redirect(url_for('accounts_list'))
    try:
        # Return a page showing the current WhatsApp Web screenshot (contains the QR if not logged in)
        png = sender.get_login_screenshot(provider, account_id, timeout=10)
        if png:
            import base64
            data = base64.b64encode(png).decode()
            img_data = f"data:image/png;base64,{data}"
            return render_template('accounts_qr.html', provider=provider, account_id=account_id, qr_image=img_data)
    except Exception:
        logging.exception('Failed to start login flow for %s/%s', provider, account_id)
    # Fallback
    return redirect(url_for('accounts_list'))


@app.route('/accounts/telegram/<account_id>/send_code', methods=['POST'])
@login_required
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
@login_required
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


@app.route('/accounts/<provider>/<account_id>/login_status')
@login_required
def accounts_login_status(provider, account_id):
    try:
        if provider == 'whatsapp':
            ready = sender.check_whatsapp_logged_in(provider=provider, account_id=account_id)
            return { 'ready': bool(ready) }
    except Exception:
        logging.exception('Failed to check login status for %s/%s', provider, account_id)
    return { 'ready': False }


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
