import unittest
import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from app.scheduler import Scheduler
from app.models import DatabaseManager
from app.notifier import Notifier
from app.config import Config

class TestScheduler(unittest.TestCase):

    def setUp(self):
        """
        Set up for Scheduler tests.
        """
        self.config = Config()
        # Mock DatabaseManager and Notifier
        self.mock_db_manager = MagicMock(spec=DatabaseManager)
        self.mock_notifier = MagicMock(spec=Notifier)
        self.scheduler = Scheduler(self.mock_db_manager, self.mock_notifier, 1) # Interval 1 second for faster testing

    def test_scheduler_initialization(self):
        """
        Test if the scheduler initializes correctly.
        """
        self.assertIsInstance(self.scheduler.db_manager, MagicMock)
        self.assertIsInstance(self.scheduler.notifier, MagicMock)
        self.assertEqual(self.scheduler.interval_seconds, 1)
        self.assertFalse(self.scheduler._running)

    @patch('time.sleep', return_value=None) # Mock time.sleep to prevent actual delays
    def test_scheduler_start_stop(self, mock_sleep):
        """
        Test starting and stopping the scheduler.
        """
        # Start the scheduler in a separate thread or with a limited loop for testing
        # For simplicity, we'll just test the state change and a single loop iteration
        self.scheduler._running = True # Manually set to True to simulate running
        with patch.object(self.scheduler, 'check_for_reminders') as mock_check:
            # Simulate one loop iteration
            self.scheduler.start()
            self.assertFalse(self.scheduler._running) # Should be False after stopping
            mock_check.assert_called_once() # check_for_reminders should have been called once

        self.scheduler._running = False # Reset for stop test
        self.scheduler.stop()
        self.assertFalse(self.scheduler._running)

    def test_check_for_reminders_no_due_reminders(self):
        """
        Test check_for_reminders when there are no due reminders.
        """
        self.mock_db_manager.get_due_reminders.return_value = []
        self.scheduler.check_for_reminders()
        self.mock_db_manager.get_due_reminders.assert_called_once()
        self.mock_db_manager.get_event_by_id.assert_not_called()
        self.mock_notifier.send_notification.assert_not_called()
        self.mock_db_manager.mark_reminder_sent.assert_not_called()