from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from sender import send_whatsapp_messages_with_log, close_driver, check_whatsapp_logged_in
from kivy.uix.checkbox import CheckBox
from kivy.clock import Clock
import uuid
import os
import threading
import time
import logging
from utils import clean_number

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

class WhatsAppUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=10, padding=10, **kwargs)

        self.numbers_input = TextInput(hint_text='Paste numbers (one per line)', multiline=True, size_hint_y=0.4)
        self.message_input = TextInput(hint_text='Enter your message', multiline=True, size_hint_y=0.3)
        self.status_label = Label(text='', size_hint_y=0.1)
        self.qr_notice = Label(text=("Note: After sending, WhatsApp session will be cleared and you'll need to scan QR next time." if os.environ.get('KEEP_WHATSAPP_SESSION','')=='' else "Note: WhatsApp session will be preserved (KEEP_WHATSAPP_SESSION set)."), size_hint_y=0.08)

        self.start_button = Button(text='Start', size_hint_y=0.1)

        self.start_button = Button(text='Start', size_hint_y=0.1)
        self.pause_button = Button(text='Pause', size_hint_y=0.1, disabled=True)
        self.resume_button = Button(text='Resume', size_hint_y=0.1, disabled=True)
        self.stop_button = Button(text='Stop', size_hint_y=0.1, disabled=True)

        self.start_button.bind(on_press=self.start_sending)
        self.pause_button.bind(on_press=self.pause_sending)
        self.resume_button.bind(on_press=self.resume_sending)
        self.stop_button.bind(on_press=self.stop_sending)

        self.add_widget(self.numbers_input)
        self.add_widget(self.message_input)
        self.add_widget(self.start_button)
        self.add_widget(self.pause_button)
        self.add_widget(self.resume_button)
        self.add_widget(self.stop_button)
        self.add_widget(self.status_label)
        self.add_widget(self.qr_notice)

        # Preserve session checkbox and status check button
        self.preserve_checkbox = CheckBox(active=False)
        cb_row = BoxLayout(orientation='horizontal', size_hint_y=0.05)
        cb_row.add_widget(Label(text='Preserve WhatsApp session', size_hint_x=0.8))
        cb_row.add_widget(self.preserve_checkbox)
        self.add_widget(cb_row)

        self.check_button = Button(text='Check WhatsApp status', size_hint_y=0.08)
        self.check_button.bind(on_press=self.on_check_status)
        self.add_widget(self.check_button)

        self._stop_flag = False
        self._pause_event = threading.Event()
        self._pause_event.set()
        self._thread = None

    def start_sending(self, instance):
        raw_numbers = self.numbers_input.text
        message = self.message_input.text

        if not raw_numbers.strip() or not message.strip():
            self.status_label.text = "❌ Please enter numbers and message"
            return

        self.numbers = [clean_number(num.strip()) for num in raw_numbers.split('\n') if num.strip()]
        self.message = message
        self.log_filename = f'whatsapp_log_{uuid.uuid4().hex[:6]}.xlsx'
        self.log_path = os.path.join('logs', self.log_filename)
        os.makedirs('logs', exist_ok=True)

        self._stop_flag = False
        self._pause_event.set()

        self.start_button.disabled = True
        self.pause_button.disabled = False
        self.resume_button.disabled = True
        self.stop_button.disabled = False
        self.status_label.text = "📤 Sending messages..."

        self._thread = threading.Thread(target=self._send_loop)
        self._thread.start()

    def pause_sending(self, instance):
        self._pause_event.clear()
        self.status_label.text = "⏸️ Paused"
        self.pause_button.disabled = True
        self.resume_button.disabled = False

    def resume_sending(self, instance):
        self._pause_event.set()
        self.status_label.text = "▶️ Resumed"
        self.pause_button.disabled = False
        self.resume_button.disabled = True

    def stop_sending(self, instance):
        self._stop_flag = True
        self._pause_event.set()  # In case it was paused
        self.status_label.text = "⏹️ Stopping..."

    def on_check_status(self, instance):
        # Run status check in background to avoid blocking the UI
        threading.Thread(target=self._do_check_status, daemon=True).start()

    def _do_check_status(self):
        try:
            ready = check_whatsapp_logged_in()
            text = "✅ WhatsApp ready" if ready else "❌ WhatsApp not ready - please scan QR"
        except Exception:
            text = "⚠️ Error checking status"
        Clock.schedule_once(lambda dt: setattr(self.qr_notice, 'text', text))

    def _send_loop(self):
        try:
            results = []
            for idx, num in enumerate(self.numbers):
                if self._stop_flag:
                    self.status_label.text = f"⏹️ Stopped at {idx} / {len(self.numbers)}"
                    break

                self._pause_event.wait()  # Wait if paused

                logging.info('Sending to %s (%d/%d)', num, idx+1, len(self.numbers))
                send_whatsapp_messages_with_log([num], self.message, self.log_path, append=True)
                self.status_label.text = f"✅ Sent {idx + 1} / {len(self.numbers)}"
                time.sleep(1)

            if not self._stop_flag:
                self.status_label.text = f"✅ All messages sent!\nLog saved: {self.log_filename}"
        except Exception as e:
            logging.exception('Error in sending loop')
            self.status_label.text = f"❌ Error: {e}"
        finally:
            self.start_button.disabled = False
            self.pause_button.disabled = True
            self.resume_button.disabled = True
            self.stop_button.disabled = True
            # Ensure driver is closed and session cleared so next run will require QR scan
            try:
                close_driver(preserve_session=self.preserve_checkbox.active)
            except Exception:
                logging.exception('Error closing driver from UI')

class RelayStackApp(App):
    def build(self):
        self.title = 'RelayStack - WhatsApp Sender'
        return WhatsAppUI()

if __name__ == '__main__':
    RelayStackApp().run()
