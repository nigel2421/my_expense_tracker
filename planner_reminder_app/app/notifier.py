import os
import platform
import subprocess
from datetime import datetime

try:
    from plyer import notification
    from playsound import playsound
    from twilio.rest import Client
except ImportError:
    notification = None
    playsound = None
import time

class Notifier:
    """
    Handles sending notifications to the user.
    This class abstracts the platform-specific notification mechanisms.
    """

    def __init__(self, config):
        """
        Initializes the Notifier with an optional sound file path.
        Args:
            config (Config): The application's config object.
        """
        self.sound_path = config.get_notification_sound_path()
        self.twilio_config = config.get_twilio_config()
        self.twilio_client = Client(self.twilio_config['account_sid'], self.twilio_config['auth_token']) if self.twilio_config else None

    def _play_sound(self):
        """
        Plays a notification sound if a sound_path is provided and valid.
        Uses platform-specific commands to play the sound.
        """
        if self.sound_path and os.path.exists(self.sound_path):
            try:
                if platform.system() == "Darwin":  # macOS
                    subprocess.run(["afplay", self.sound_path], check=True)
                elif platform.system() == "Linux":  # Linux
                    # Requires 'aplay' or 'paplay' (pulseaudio)
                    # Try aplay first, then paplay
                    try:
                        subprocess.run(["aplay", self.sound_path], check=True)
                    except FileNotFoundError:
                        subprocess.run(["paplay", self.sound_path], check=True)
                elif platform.system() == "Windows":  # Windows
                    if playsound:
                        playsound(self.sound_path)
                    else:
                        print("Warning: 'playsound' library not installed. Cannot play sound.")
                        print(f"Sound file: {self.sound_path}")
                else:
                    print(f"Warning: Sound playback not supported on {platform.system()}")
            except Exception as e:
                print(f"Error playing sound: {e}")
        elif self.sound_path:
            print(f"Warning: Notification sound file not found at {self.sound_path}")

    def send(self, reminder, event):
        """
        Sends a notification based on the reminder's method.
        Args:
            reminder (dict): The reminder data from the database.
            event (dict): The event data associated with the reminder.
        """
        event_time = datetime.fromisoformat(event['start_time']).strftime('%Y-%m-%d %H:%M')
        message = f"Your event '{event['title']}' is scheduled for {event_time}."
        title = f"Reminder: {event['title']}"

        if reminder['method'] == 'whatsapp':
            self._send_whatsapp_notification(title, message)
        else:  # Default to desktop popup
            self._send_desktop_notification(title, message)

    def _send_desktop_notification(self, title, message, sound=True):
        if notification:
            try:
                notification.notify(
                    title=title,
                    message=message,
                    app_name='Planner Reminder App',
                    timeout=10
                )
                print(f"Notification sent: '{title}'")
            except Exception as e:
                print(f"Failed to send desktop notification: {e}")
                self._fallback_notification(title, message)
        else:
            print("Warning: 'plyer' library not installed. Falling back to console.")
            self._fallback_notification(title, message)

        if sound:
            self._play_sound()

    def _send_whatsapp_notification(self, title, message):
        if not self.twilio_client or not self.twilio_config:
            print("Error: Twilio is not configured. Cannot send WhatsApp message.")
            return

        full_message = f"*{title}*\n\n{message}"
        self.twilio_client.messages.create(from_=self.twilio_config['from_number'], body=full_message, to=self.twilio_config['to_number'])
        print(f"WhatsApp notification sent to {self.twilio_config['to_number']}")

    def _fallback_notification(self, title, message):
        print(f"--- Notification (Fallback) ---")
        print(f"Title: {title}")
        print(f"Message: {message}")
        print(f"-----------------------------")