import os
from cryptography.fernet import Fernet, InvalidToken
from pathlib import Path
import json

"""Simple encrypted session storage utility.

Usage:
- Set env var SESSION_KEY to a base64 Fernet key to persistably use encryption.
- Use `generate_key()` to produce a key for production and store it safely.
- Sessions are stored in `sessions/` directory as `<provider>--<account_id>.session`.
- API: save_session(provider, account_id, data), load_session(provider, account_id), remove_session(...)
"""

SESSIONS_DIR = Path(os.getcwd()) / 'sessions'
SESSIONS_DIR.mkdir(exist_ok=True)

_SESSION_KEY = os.environ.get('SESSION_KEY')


def generate_key():
    """Return a new Fernet key. Save it to your environment securely."""
    return Fernet.generate_key().decode()


def _get_fernet():
    if not _SESSION_KEY:
        # Fallback to a file-based key in sessions/.local_key (development only)
        key_file = SESSIONS_DIR / '.local_key'
        if key_file.exists():
            key = key_file.read_text().strip()
        else:
            key = Fernet.generate_key().decode()
            key_file.write_text(key)
        return Fernet(key.encode())
    return Fernet(_SESSION_KEY.encode())


def _session_path(provider, account_id):
    safe_name = f"{provider}--{account_id}.session"
    return SESSIONS_DIR / safe_name


def save_session(provider, account_id, data: dict):
    f = _get_fernet()
    payload = json.dumps(data).encode()
    token = f.encrypt(payload)
    path = _session_path(provider, account_id)
    path.write_bytes(token)


def load_session(provider, account_id):
    path = _session_path(provider, account_id)
    if not path.exists():
        return None
    token = path.read_bytes()
    f = _get_fernet()
    try:
        payload = f.decrypt(token)
        return json.loads(payload.decode())
    except InvalidToken:
        raise RuntimeError('Invalid session key or corrupted session file')


def remove_session(provider, account_id):
    path = _session_path(provider, account_id)
    try:
        if path.exists():
            path.unlink()
            return True
    except Exception:
        return False
    return False
