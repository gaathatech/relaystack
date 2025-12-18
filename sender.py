import logging
import os
import time
import shutil
from datetime import datetime
from urllib.parse import quote
import openpyxl

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Map provider+account -> WebDriver instances to support multiple profiles
_drivers = {}
# base user_data dir for provider profiles: user_data/<provider>/<account_id>
BASE_USER_DATA_DIR = os.path.join(os.getcwd(), 'user_data')



def init_driver_for_profile(provider: str, account_id: str, wait_for_login=True, timeout=300):
    """Create or return a Chrome driver tied to a provider/account profile.

    - profile_dir will be user_data/<provider>/<account_id>
    - if wait_for_login is True, the function will wait for WhatsApp Web side element.
    """
    key = f"{provider}:{account_id}"
    if key in _drivers:
        return _drivers[key]

    profile_dir = os.path.join(BASE_USER_DATA_DIR, provider, account_id)
    os.makedirs(profile_dir, exist_ok=True)

    options = webdriver.ChromeOptions()
    chrome_bin = os.environ.get('CHROME_BINARY')
    if chrome_bin:
        options.binary_location = chrome_bin
        logging.info('Using CHROME_BINARY from environment: %s', chrome_bin)

    options.add_argument(f'--user-data-dir={profile_dir}')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--remote-debugging-port=9222')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-background-timer-throttling')
    options.add_argument('--disable-backgrounding-occluded-windows')
    options.add_argument('--disable-renderer-backgrounding')

    chromedriver_path = os.environ.get('CHROMEDRIVER_PATH')
    if chromedriver_path:
        service = Service(chromedriver_path)
    else:
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
        except Exception:
            service = Service('/usr/bin/chromedriver')

    try:
        drv = webdriver.Chrome(service=service, options=options)
    except Exception:
        logging.exception('Unable to start Chrome driver for profile %s/%s', provider, account_id)
        raise

    if wait_for_login:
        try:
            drv.get('https://web.whatsapp.com')
            WebDriverWait(drv, timeout).until(
                EC.presence_of_element_located((By.ID, "side"))
            )
            logging.info('Profile %s/%s appears logged in', provider, account_id)
        except Exception:
            logging.info('Profile %s/%s not logged in within timeout', provider, account_id)
    _drivers[key] = drv
    return drv


def get_login_screenshot(provider: str, account_id: str, timeout=30):
    """Start (or reuse) a driver for the profile and return a PNG screenshot bytes of the login/QR page.

    This is a best-effort helper: it loads web.whatsapp.com and returns a PNG of the page which
    usually contains the QR code for scanning when not logged in.
    """
    key = f"{provider}:{account_id}"
    if key in _drivers:
        drv = _drivers[key]
    else:
        # Do not wait for login here; we want the QR to appear if not logged in
        drv = init_driver_for_profile(provider, account_id, wait_for_login=False)

    try:
        drv.get('https://web.whatsapp.com')
        # Give the page some time to render the QR
        time.sleep(min(5, timeout))
        png = drv.get_screenshot_as_png()

        # Crop to focus on QR area (center square, assuming 1080x1920 or similar)
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(png))
        width, height = img.size
        # Assume QR is in the center; crop to a square of min(width, height) centered
        size = min(width, height)
        left = (width - size) // 2
        top = (height - size) // 2
        right = left + size
        bottom = top + size
        cropped = img.crop((left, top, right, bottom))
        output = io.BytesIO()
        cropped.save(output, format='PNG')
        return output.getvalue()
    except Exception:
        logging.exception('Failed to capture login screenshot for %s/%s', provider, account_id)
        return None


def send_whatsapp_messages_with_log(numbers, message, log_path, append=False, account_id='default'):
    # Prepare Excel workbook for logging
    if append and os.path.exists(log_path):
        wb = openpyxl.load_workbook(log_path)
        ws = wb.active
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "WhatsApp Logs"
        ws.append(['Phone Number', 'Status', 'Timestamp', 'Account'])

    driver = init_driver_for_profile('whatsapp', account_id, wait_for_login=True)

    encoded_message = quote(message)

    for number in numbers:
        try:
            url = f"https://web.whatsapp.com/send?phone={number}&text={encoded_message}"
            driver.get(url)

            # Wait for the send button and click
            send_button = WebDriverWait(driver, 40).until(
                EC.element_to_be_clickable((By.XPATH, '//span[@data-icon="send"]'))
            )
            send_button.click()

            logging.info('Message sent to %s (account=%s)', number, account_id)
            ws.append([number, "Sent", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), account_id])
            time.sleep(8)

        except Exception as e:
            try:
                page = driver.page_source
            except Exception:
                page = ''

            if "Phone number shared via URL is invalid" in page:
                logging.warning('Invalid number: %s', number)
                ws.append([number, "Invalid", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), account_id])
            else:
                logging.exception('Failed to send to %s', number)
                ws.append([number, f"Failed: {str(e)}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), account_id])

    wb.save(log_path)
    logging.info('Log saved to %s', log_path)


def check_whatsapp_logged_in(timeout=8, provider='whatsapp', account_id='default'):
    """Check whether the given provider/account profile appears logged in by opening a short-lived driver."""
    profile_dir = os.path.join(BASE_USER_DATA_DIR, provider, account_id)
    if not os.path.exists(profile_dir):
        return False

    drv = None
    try:
        options = webdriver.ChromeOptions()
        chrome_bin = os.environ.get('CHROME_BINARY')
        if chrome_bin:
            options.binary_location = chrome_bin
        options.add_argument(f'--user-data-dir={profile_dir}')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        chromedriver_path = os.environ.get('CHROMEDRIVER_PATH')
        if chromedriver_path:
            service = Service(chromedriver_path)
        else:
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
            except Exception:
                service = Service('/usr/bin/chromedriver')

        drv = webdriver.Chrome(service=service, options=options)
        drv.set_page_load_timeout(timeout)
        drv.get('https://web.whatsapp.com')
        try:
            WebDriverWait(drv, 5).until(EC.presence_of_element_located((By.ID, 'side')))
            return True
        except Exception:
            return False
    except Exception:
        logging.exception('Error while checking WhatsApp status')
        return False
    finally:
        try:
            if drv:
                drv.quit()
        except Exception:
            pass

def close_driver(preserve_session=False):
    """Close the Chrome driver and optionally remove the persisted WhatsApp session.

    By default this function will remove the Chrome `user_data` directory so that
    the next driver start will require scanning the WhatsApp Web QR code again.
    Pass `preserve_session=True` to keep the user data directory in place.
    """
    global driver
    if driver:
        try:
            driver.quit()
        except Exception:
            logging.exception('Error closing driver')
        driver = None

    # Remove the persisted user data directory unless requested to preserve it
    if not preserve_session:
        try:
            if os.path.exists(USER_DATA_DIR):
                shutil.rmtree(USER_DATA_DIR)
                logging.info('Removed user data dir (%s) to force QR re-scan next time', USER_DATA_DIR)
        except Exception:
            logging.exception('Failed to remove user data dir')
    else:
        logging.info('Preserving user data dir: %s', USER_DATA_DIR)
