import os
import json
from pathlib import Path
from datetime import datetime, timedelta

RATE_DIR = Path(os.getcwd()) / 'rate_limits'
RATE_DIR.mkdir(exist_ok=True)

# Simple per-account sliding window limiter
DEFAULT_LIMIT_PER_MINUTE = int(os.environ.get('LIMIT_PER_MINUTE', 30))


def _path(provider, account_id):
    return RATE_DIR / f"{provider}--{account_id}.json"


def consume(provider, account_id, amount=1, limit=DEFAULT_LIMIT_PER_MINUTE):
    path = _path(provider, account_id)
    now = datetime.utcnow()
    window_start = now - timedelta(minutes=1)

    records = []
    if path.exists():
        try:
            records = json.loads(path.read_text())
            records = [datetime.fromisoformat(r) for r in records]
        except Exception:
            records = []

    # drop old
    records = [r for r in records if r > window_start]
    if len(records) + amount > limit:
        # not allowed
        path.write_text(json.dumps([r.isoformat() for r in records]))
        return False

    # record amount times
    for _ in range(amount):
        records.append(now)
    path.write_text(json.dumps([r.isoformat() for r in records]))
    return True
