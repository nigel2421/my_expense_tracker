import os
import configparser

class Config:
    """
    Configuration class for the Planner Reminder Application.
    Manages settings by reading from a config.ini file.
    """
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    CONFIG_FILE = os.path.join(BASE_DIR, 'config.ini')

    def __init__(self):
        self.config = configparser.ConfigParser()
        if not os.path.exists(self.CONFIG_FILE):
            self._create_default_config()
        self.config.read(self.CONFIG_FILE)

    def _create_default_config(self):
        default_config = configparser.ConfigParser()
        default_config['database'] = {
            'path': os.path.join(self.BASE_DIR, 'data', 'planner_reminder.db')
        }
        default_config['scheduler'] = {
            'interval_seconds': '60'
        }
        default_config['notifications'] = {
            'sound_path': os.path.join(self.BASE_DIR, 'assets', 'notification.mp3')
        }
        default_config['twilio'] = {
            'account_sid': 'YOUR_ACCOUNT_SID_HERE',
            'auth_token': 'YOUR_AUTH_TOKEN_HERE',
            'from_number': 'whatsapp:+14155238886',
            'to_number': 'whatsapp:YOUR_PERSONAL_WHATSAPP_NUMBER'
        }
        with open(self.CONFIG_FILE, 'w') as configfile:
            default_config.write(configfile)
        print(f"Created default config file at: {self.CONFIG_FILE}")
        print("Please edit it with your Twilio credentials.")

    def get_database_path(self):
        db_path = self.config.get('database', 'path')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        return db_path

    def get_notification_sound_path(self):
        return self.config.get('notifications', 'sound_path', fallback=None)

    def get_scheduler_interval(self):
        return self.config.getint('scheduler', 'interval_seconds', fallback=60)

    def get_twilio_config(self):
        if 'twilio' in self.config and self.config.get('twilio', 'account_sid', fallback='').startswith('AC'):
            return dict(self.config.items('twilio'))
        return None