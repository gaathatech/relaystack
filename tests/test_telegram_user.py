import os
import pytest
from providers import telegram_user


class DummyClient:
    def __init__(self, *a, **kw):
        self._msgs = []
    async def connect(self):
        return True
    async def send_code_request(self, phone):
        class R: phone_code_hash='hash'
        return R()
    async def sign_in(self, phone=None, code=None):
        return True
    async def disconnect(self):
        return True
    def __getattr__(self, name):
        async def _(*a, **k): return True
        return _


def test_start_and_complete_login_monkeypatch(monkeypatch, tmp_path):
    monkeypatch.setenv('TELEGRAM_API_ID', '12345')
    monkeypatch.setenv('TELEGRAM_API_HASH', 'abcdef')

    # monkeypatch the TelegramClient so we don't call real network
    monkeypatch.setattr(telegram_user, 'TelegramClient', lambda *a, **k: DummyClient())
    monkeypatch.setattr(telegram_user, 'StringSession', lambda *a, **k: type('S', (), {'save': lambda s: 'sessstr', 'session': None}) )

    # start login
    assert telegram_user.start_telegram_login('+1000000000', 'telegram', 'testacc')

    # complete login (will save session)
    assert telegram_user.complete_telegram_login('1234', 'telegram', 'testacc')

    # session should be stored via sessions module
    from sessions import load_session
    sess = load_session('telegram','testacc')
    assert sess and 'string' in sess
