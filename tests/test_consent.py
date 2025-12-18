from app import app


def test_missing_consent():
    client = app.test_client()
    rv = client.post('/', data={'provider':'whatsapp', 'numbers':'919876543210','message':'hi'}, follow_redirects=True)
    assert rv.status_code == 200
    assert b'You must confirm recipient consent' in rv.data
