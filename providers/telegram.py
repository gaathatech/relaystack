import os
import logging
import requests
import openpyxl
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


API_BASE = 'https://api.telegram.org'


def send_telegram_messages_with_log(chat_ids, message, log_path, append=False):
    """Send messages to one or more `chat_ids` using the Bot API and log results to Excel.

    chat_ids: iterable of chat IDs (ints or numeric strings)
    message: message text
    log_path: path to Excel file to write or append
    append: whether to append to an existing workbook
    """
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if token is None:
        raise RuntimeError('TELEGRAM_BOT_TOKEN is required to send Telegram messages')

    if append and os.path.exists(log_path):
        wb = openpyxl.load_workbook(log_path)
        ws = wb.active
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Telegram Logs'
        ws.append(['Chat ID', 'Status', 'Timestamp', 'Response'])

    headers = {'Content-Type': 'application/json'}

    for chat in chat_ids:
        try:
            payload = {
                'chat_id': str(chat),
                'text': message,
                'parse_mode': 'HTML'
            }
            url = f"{API_BASE}/bot{token}/sendMessage"
            r = requests.post(url, json=payload, headers=headers, timeout=8)
            if r.status_code == 200:
                logging.info('Telegram message sent to %s', chat)
                ws.append([chat, 'Sent', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), r.text[:200]])
            else:
                logging.warning('Telegram send failed to %s: %s', chat, r.text)
                ws.append([chat, f'Failed: {r.status_code}', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), r.text[:200]])
        except Exception as e:
            logging.exception('Exception sending to %s', chat)
            ws.append([chat, f'Error: {e}', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), ''])

    wb.save(log_path)
    logging.info('Telegram log saved to %s', log_path)
