from app import app
import providers.telegram_user as tuser
import sessions


def test_telegram_login_flow(monkeypatch, tmp_path):
    # Monkeypatch start/complete to avoid real Telethon calls
    monkeypatch.setattr(tuser, 'start_telegram_login', lambda phone, provider, account_id: True)
    monkeypatch.setattr(tuser, 'complete_telegram_login', lambda code, provider, account_id: sessions.save_session('telegram', account_id, {'string':'fake'}))

    client = app.test_client()
    # create account slot
    rv = client.post('/accounts/create', data={'provider':'telegram', 'account_id':'testuser'})
    assert rv.status_code in (302, 200)

    # start login
    rv = client.post(f'/accounts/telegram/testuser/send_code', data={'phone':'+123'}, follow_redirects=True)
    assert b'Enter Code' in rv.data or rv.status_code == 200

    # verify
    rv = client.post(f'/accounts/telegram/testuser/verify', data={'code':'1234'}, follow_redirects=True)
    assert rv.status_code in (302, 200)

    # session should exist
    data = sessions.load_session('telegram', 'testuser')
    assert data is not None
    assert 'string' in data
