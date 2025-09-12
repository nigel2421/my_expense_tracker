import time
from datetime import datetime, timedelta

class Scheduler:
    """
    Schedules and manages reminders for events.
    It periodically checks for upcoming events and triggers notifications.
    """

    def __init__(self, db_manager, notifier, interval_seconds=60):
        """
        Initializes the Scheduler.
        Args:
            db_manager (DatabaseManager): An instance of the DatabaseManager for database operations.
            notifier (Notifier): An instance of the Notifier for sending notifications.
            interval_seconds (int): How often the scheduler should check for reminders in seconds.
        """
        self.db_manager = db_manager
        self.notifier = notifier
        self.interval_seconds = interval_seconds
        self._running = False

    def start(self):
        """
        Starts the scheduler loop.
        """
        print(f"Scheduler started, checking every {self.interval_seconds} seconds...")
        self._running = True
        while self._running:
            self.check_for_reminders()
            time.sleep(self.interval_seconds)

    def stop(self):
        """
        Stops the scheduler loop.
        """
        print("Scheduler stopping...")
        self._running = False

    def check_for_reminders(self):
        """
        Checks the database for upcoming reminders and triggers notifications.
        """
        now = datetime.now()
        # Get reminders that are due now or in the very near future and haven't been sent
        # We fetch reminders that are due within the next 'interval_seconds' to ensure we don't miss any
        # and also those that might have been missed from the last check.
        due_reminders = self.db_manager.get_due_reminders(now, now + timedelta(seconds=self.interval_seconds))

        for reminder in due_reminders:
            event = self.db_manager.get_event_by_id(reminder['event_id'])
            if event:
                self.notifier.send(reminder, event)
                self.db_manager.mark_reminder_sent(reminder['id'])