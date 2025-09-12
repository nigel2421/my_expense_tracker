import unittest
import os
from datetime import datetime, timedelta
from app.models import DatabaseManager

class TestDatabaseManager(unittest.TestCase):

    def setUp(self):
        """
        Set up a temporary in-memory database for testing.
        """
        self.db_path = ':memory:'  # Use in-memory database for testing
        self.db_manager = DatabaseManager(self.db_path)

    def tearDown(self):
        """
        Clean up after each test.
        """
        # No explicit cleanup needed for in-memory database as it's destroyed after connection closes
        pass

    def test_add_event(self):
        """
        Test adding a new event to the database.
        """
        title = "Test Event"
        start_time = datetime.now()
        description = "This is a test event."
        location = "Test Location"

        event_id = self.db_manager.add_event(title, start_time, description=description, location=location)
        self.assertIsNotNone(event_id)
        self.assertIsInstance(event_id, int)
 
        event = self.db_manager.get_event_by_id(event_id)
        self.assertIsNotNone(event)
        self.assertEqual(event['title'], title)
        self.assertEqual(event['description'], description)
        self.assertEqual(datetime.fromisoformat(event['start_time']), start_time.replace(microsecond=0))
        self.assertEqual(event['location'], location)
        self.assertEqual(event['status'], 'scheduled')

    def test_get_event_by_id(self):
        """
        Test retrieving an event by its ID.
        """
        title = "Another Test Event"
        start_time = datetime.now() + timedelta(days=1)
        event_id = self.db_manager.add_event(title, start_time)

        event = self.db_manager.get_event_by_id(event_id)
        self.assertIsNotNone(event)
        self.assertEqual(event['id'], event_id)
        self.assertEqual(event['title'], title)

        # Test for non-existent event
        non_existent_event = self.db_manager.get_event_by_id(99999)
        self.assertIsNone(non_existent_event)

    def test_reminders(self):
        """
        Test adding, retrieving, and marking reminders.
        """
        # 1. Add an event to associate a reminder with
        event_id = self.db_manager.add_event("Event with Reminder", datetime.now() + timedelta(hours=2))
        self.assertIsNotNone(event_id)

        # 2. Add a reminder for this event that is due in 5 minutes
        reminder_time_due = datetime.now() + timedelta(minutes=5)
        reminder_id = self.db_manager.add_reminder(event_id, reminder_time_due)
        self.assertIsNotNone(reminder_id)

        # 3. Check for due reminders in a window that doesn't include our reminder
        now = datetime.now()
        due_reminders_none = self.db_manager.get_due_reminders(now, now + timedelta(minutes=4))
        self.assertEqual(len(due_reminders_none), 0)

        # 4. Check for due reminders in the correct time window
        due_reminders_one = self.db_manager.get_due_reminders(now, now + timedelta(minutes=6))
        self.assertEqual(len(due_reminders_one), 1)
        self.assertEqual(due_reminders_one[0]['id'], reminder_id)
        self.assertEqual(due_reminders_one[0]['event_id'], event_id)

        # 5. Mark the reminder as sent and check that it's no longer retrieved
        self.db_manager.mark_reminder_sent(reminder_id)
        due_reminders_after_sent = self.db_manager.get_due_reminders(now, now + timedelta(minutes=6))
        self.assertEqual(len(due_reminders_after_sent), 0)

    def test_update_event(self):
        """
        Test updating an existing event.
        """
        # Add an event first
        start_time = datetime.now()
        event_id = self.db_manager.add_event("Original Title", start_time, "Original Desc", location="Original Loc")

        # Now update it
        new_title = "Updated Title"
        new_start_time = start_time + timedelta(days=1)
        new_desc = "Updated Desc"
        new_loc = "Updated Loc"
        self.db_manager.update_event(event_id, new_title, new_start_time, description=new_desc, location=new_loc)

        # Retrieve and check
        updated_event = self.db_manager.get_event_by_id(event_id)
        self.assertIsNotNone(updated_event)
        self.assertEqual(updated_event['title'], new_title)
        self.assertEqual(datetime.fromisoformat(updated_event['start_time']), new_start_time.replace(microsecond=0))
        self.assertEqual(updated_event['description'], new_desc)
        self.assertEqual(updated_event['location'], new_loc)

    def test_delete_event(self):
        """
        Test deleting an event.
        """
        event_id = self.db_manager.add_event("To Be Deleted", datetime.now())
        self.assertIsNotNone(self.db_manager.get_event_by_id(event_id))

        self.db_manager.delete_event(event_id)
        self.assertIsNone(self.db_manager.get_event_by_id(event_id))