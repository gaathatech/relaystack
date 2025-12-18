from app import app
import sender


def test_whatsapp_status_endpoint(monkeypatch):
    monkeypatch.setattr(sender, 'check_whatsapp_logged_in', lambda *a, **k: True)
    client = app.test_client()
    rv = client.get('/status/whatsapp')
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['ready'] is True

    monkeypatch.setattr(sender, 'check_whatsapp_logged_in', lambda *a, **k: False)
    rv = client.get('/status/whatsapp')
    data = rv.get_json()
    assert data['ready'] is False
