import os
import json
import requests
import pytest
from providers import telegram


class DummyResp:
    def __init__(self, status_code, text):
        self.status_code = status_code
        self.text = text


def test_send_telegram_messages_with_log_monkeypatch(tmp_path, monkeypatch):
    # Prepare a fake response
    def fake_post(url, json, headers, timeout):
        assert 'bot' in url
        assert 'chat_id' in json
        return DummyResp(200, '{"ok":true}')

    monkeypatch.setattr(requests, 'post', fake_post)
    monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'fake-token')

    log_file = tmp_path / 'tg_log.xlsx'
    telegram.send_telegram_messages_with_log([12345], 'hello', str(log_file), append=False)

    assert log_file.exists()
