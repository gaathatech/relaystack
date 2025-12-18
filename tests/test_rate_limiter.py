from rate_limiter import allow_send, remaining_quota


def test_rate_limiter_basic(monkeypatch):
    # Set small window via monkeypatching DEFAULT_LIMIT
    import rate_limiter
    monkeypatch.setattr(rate_limiter, 'DEFAULT_LIMIT', 3)

    provider = 'whatsapp'
    account = 'test'

    assert allow_send(provider, account, count=1)
    assert allow_send(provider, account, count=1)
    assert allow_send(provider, account, count=1)
    # now should be exhausted
    assert not allow_send(provider, account, count=1)
    # remaining_quota should be zero
    assert remaining_quota(provider, account) == 0
