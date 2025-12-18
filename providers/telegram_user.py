import os
import asyncio
import logging
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError
from sessions import save_session, load_session
import openpyxl
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# API creds are read at call time from env so tests can monkeypatch env dynamically.



# Simple in-memory pending auth store for ongoing flows. For production persist temporarily and secure it.
_pending_auth = {}


def _make_client_from_string(session_str: str):
    return TelegramClient(StringSession(session_str), int(API_ID), API_HASH)


async def _send_code_async(phone, account_id, api_id, api_hash):
    """Send code to a phone and return the phone_code_hash-like info via telethon."""
    client = TelegramClient(StringSession(), int(api_id), api_hash)
    await client.connect()
    res = await client.send_code_request(phone)
    await client.disconnect()
    return res


def start_telegram_login(phone: str, provider: str, account_id: str):
    """Initiate login by sending code to `phone`. Stores temporary info in `_pending_auth` and returns True if sent."""
    api_id = os.environ.get('TELEGRAM_API_ID')
    api_hash = os.environ.get('TELEGRAM_API_HASH')
    if not api_id or not api_hash:
        raise RuntimeError('TELEGRAM_API_ID and TELEGAM_API_HASH required')

    # run async send_code_request
    loop = asyncio.new_event_loop()
    try:
        res = loop.run_until_complete(_send_code_async(phone, account_id, api_id, api_hash))
    finally:
        loop.close()

    # store phone and phone_code_hash in pending store
    _pending_auth[(provider, account_id)] = {'phone': phone, 'phone_code_hash': getattr(res, 'phone_code_hash', None)}
    return True


async def _sign_in_async(code, provider, account_id, api_id, api_hash):
    # Use a temporary client tied to this account to sign in and return the string session
    client = TelegramClient(StringSession(), int(api_id), api_hash)
    await client.connect()
    try:
        if (provider, account_id) not in _pending_auth:
            raise RuntimeError('No pending login for account')
        info = _pending_auth[(provider, account_id)]
        phone = info['phone']
        phone_code_hash = info.get('phone_code_hash')
        # Telethon's sign_in can accept the code and phone_code_hash
        try:
            if phone_code_hash:
                try:
                    res = await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
                except TypeError:
                    # some client implementations (e.g., test dummy) may not accept phone_code_hash
                    res = await client.sign_in(phone=phone, code=code)
            else:
                res = await client.sign_in(phone=phone, code=code)
        except SessionPasswordNeededError:
            # account has 2FA password; caller needs to call with password (not implemented here)
            raise

        # After sign in, export string session
        try:
            if hasattr(client.session, 'save'):
                string = client.session.save()
            else:
                string = StringSession.save(client.session)
        except Exception:
            # fallback to str
            string = str(client.session)
        await client.disconnect()
        return string
    except Exception:
        await client.disconnect()
        raise


def complete_telegram_login(code: str, provider: str, account_id: str):
    """Complete login using code; on success save session via sessions.save_session and return True."""
    api_id = os.environ.get('TELEGRAM_API_ID')
    api_hash = os.environ.get('TELEGRAM_API_HASH')
    if not api_id or not api_hash:
        raise RuntimeError('TELEGRAM_API_ID and TELEGAM_API_HASH required')

    loop = asyncio.new_event_loop()
    try:
        session_str = loop.run_until_complete(_sign_in_async(code, provider, account_id, api_id, api_hash))
    finally:
        loop.close()

    save_session('telegram', account_id, {'string': session_str})
    # cleanup pending
    _pending_auth.pop((provider, account_id), None)
    return True


async def _send_user_message_async(session_str, chat_id, message):
    client = _make_client_from_string(session_str)
    await client.connect()
    try:
        await client.send_message(int(chat_id), message)
    finally:
        await client.disconnect()


def send_telegram_user_messages_with_log(chat_ids, message, log_path, append=False, account_id='default'):
    # Prepare workbook
    if append and os.path.exists(log_path):
        wb = openpyxl.load_workbook(log_path)
        ws = wb.active
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Telegram User Logs'
        ws.append(['Chat ID', 'Status', 'Timestamp', 'Account'])

    sess = load_session('telegram', account_id)
    if not sess or 'string' not in sess:
        raise RuntimeError('No stored session for this telegram account')

    session_str = sess['string']

    for chat in chat_ids:
        try:
            asyncio.run(_send_user_message_async(session_str, chat, message))
            ws.append([chat, 'Sent', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), account_id])
        except Exception as e:
            logging.exception('Failed to send Telegram user message to %s', chat)
            ws.append([chat, f'Failed: {e}', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), account_id])

    wb.save(log_path)
    logging.info('Telegram user log saved to %s', log_path)
