import sqlite3
from datetime import datetime

class DatabaseManager:
    """
    Manages all database operations for the Planner Reminder Application.
    Handles connection, table creation, and CRUD operations for events and reminders.
    """

    def __init__(self, db_path):
        """
        Initializes the DatabaseManager with the path to the SQLite database.
        Args:
            db_path (str): The full path to the SQLite database file.
        """
        self.db_path = db_path
        self._create_tables()

    def _get_connection(self):
        """
        Establishes and returns a connection to the database.
        Returns:
            sqlite3.Connection: A database connection object.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Allows accessing columns by name
        return conn

    def _create_tables(self):
        """
        Creates the necessary tables if they don't already exist.
        Tables:
            - events: Stores details of scheduled events.
            - reminders: Stores details of reminders associated with events.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME,
                    location TEXT,
                    status TEXT DEFAULT 'scheduled'
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER NOT NULL,
                    reminder_time DATETIME NOT NULL,
                    method TEXT DEFAULT 'popup', -- e.g., 'popup', 'sound'
                    is_sent BOOLEAN DEFAULT 0,
                    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
                )
            """)
            conn.commit()

    def add_event(self, title, start_time, description=None, end_time=None, location=None):
        """
        Adds a new event to the database.
        Args:
            title (str):
            start_time (datetime): The start time of the event.
            description (str, optional): A description of the event. Defaults to None.
            end_time (datetime, optional): The end time of the event. Defaults to None.
            location (str, optional): The location of the event. Defaults to None.
        Returns:
            int: The ID of the newly added event.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO events (title, start_time, description, end_time, location)
                VALUES (?, ?, ?, ?, ?)
            """, (title, start_time.isoformat(), description,
                  end_time.isoformat() if end_time else None, location))
            conn.commit()
            return cursor.lastrowid

    def get_event_by_id(self, event_id):
        """
        Retrieves a single event by its primary key.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
            event = cursor.fetchone()
            return event

    def get_all_events(self):
        """
        Retrieves all events from the database, ordered by start time.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events ORDER BY start_time ASC")
            events = cursor.fetchall()
            return events

    def update_event(self, event_id, title, start_time, description=None, end_time=None, location=None):
        """
        Updates an existing event in the database.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE events
                SET title = ?, start_time = ?, description = ?, end_time = ?, location = ?
                WHERE id = ?
            """, (title, start_time.isoformat(), description,
                  end_time.isoformat() if end_time else None, location, event_id))
            conn.commit()

    def delete_event(self, event_id):
        """
        Deletes an event from the database.
        Because of 'ON DELETE CASCADE' in the schema, associated reminders are also deleted.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
            conn.commit()

    def add_reminder(self, event_id, reminder_time, method='popup'):
        """
        Adds a new reminder for an event.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO reminders (event_id, reminder_time, method) VALUES (?, ?, ?)",
                (event_id, reminder_time.isoformat(), method)
            )
            conn.commit()
            return cursor.lastrowid

    def get_reminders_for_event(self, event_id):
        """
        Retrieves all reminders for a specific event.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM reminders WHERE event_id = ? ORDER BY reminder_time ASC", (event_id,))
            return cursor.fetchall()

    def delete_reminder(self, reminder_id):
        """
        Deletes a specific reminder by its ID.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
            conn.commit()

    def get_due_reminders(self, start_time: datetime, end_time: datetime) -> list:
        """
        Retrieves reminders that are due within a given time window and have not been sent.
        """
        query = """
            SELECT id, event_id, reminder_time, method FROM reminders
            WHERE reminder_time >= ? AND reminder_time < ? AND is_sent = 0
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Pass datetime objects directly; sqlite3 driver handles conversion
            cursor.execute(query, (start_time, end_time))
            reminders = cursor.fetchall()
            return reminders

    def mark_reminder_sent(self, reminder_id):
        """
        Marks a reminder as sent to prevent duplicate notifications.
        """
        query = "UPDATE reminders SET is_sent = 1 WHERE id = ?"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (reminder_id,))
            conn.commit()