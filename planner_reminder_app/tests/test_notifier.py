import unittest
import os
from unittest.mock import patch, MagicMock
from app.notifier import Notifier
from app.config import Config

class TestNotifier(unittest.TestCase):

    def setUp(self):
        """
        Set up for Notifier tests.
        """
        self.config = Config()
        self.test_sound_path = os.path.join(self.config.BASE_DIR, 'assets', 'test_notification.mp3')
        # Create a dummy sound file for testing if it doesn't exist
        if not os.path.exists(self.test_sound_path):
            os.makedirs(os.path.dirname(self.test_sound_path), exist_ok=True)
            with open(self.test_sound_path, 'w') as f:
                f.write("dummy sound file content")
        self.notifier = Notifier(sound_path=self.test_sound_path)

    def tearDown(self):
        """
        Clean up after tests.
        """
        if os.path.exists(self.test_sound_path):
            os.remove(self.test_sound_path)
        if os.path.exists(os.path.dirname(self.test_sound_path)) and not os.listdir(os.path.dirname(self.test_sound_path)):
            os.rmdir(os.path.dirname(self.test_sound_path))

    @patch('platform.system', return_value='Windows')
    @patch('app.notifier.playsound')
    def test_play_sound_windows(self, mock_playsound, mock_platform_system):
        """
        Test _play_sound method on Windows using the 'playsound' library.
        """
        # Case 1: playsound is available
        self.notifier._play_sound()
        mock_playsound.assert_called_once_with(self.test_sound_path)

        # Case 2: playsound is not available (mock it as None)
        mock_playsound.reset_mock()
        with patch('app.notifier.playsound', None):
            with patch('builtins.print') as mock_print:
                self.notifier._play_sound()
                mock_playsound.assert_not_called()
                mock_print.assert_any_call("Warning: 'playsound' library not installed. Cannot play sound.")

    @patch('app.notifier.notification.notify')
    def test_send_notification(self, mock_notify):
        """
        Test sending a notification.
        """
        title = "Test Title"
        message = "Test Message"
        self.notifier.send_notification(title, message, sound=False)

        mock_notify.assert_called_once_with(
            title=title,
            message=message,
            app_name='Planner Reminder App',
            timeout=10
        )

    @patch('app.notifier.notification.notify', side_effect=Exception("Test error"))
    @patch('app.notifier.Notifier._fallback_notification')
    def test_send_notification_fallback(self, mock_fallback, mock_notify):
        """
        Test the fallback mechanism when sending a notification fails.
        """
        title = "Fallback Test"
        message = "This should print to console."
        self.notifier.send_notification(title, message, sound=False)

        mock_notify.assert_called_once()
        mock_fallback.assert_called_once_with(title, message)