import cmd
from datetime import datetime, timedelta
from app.models import DatabaseManager
from app.utils import parse_datetime, format_datetime
from app.config import Config

class CLI(cmd.Cmd):
    """
    Command Line Interface for the Planner Reminder Application.
    Provides an interactive shell to manage events and reminders.
    """
    intro = 'Welcome to the Planner Reminder App CLI. Type help or ? to list commands.\n'
    prompt = Config().CLI_PROMPT

    def __init__(self, db_manager):
        """
        Initializes the CLI with a DatabaseManager instance.
        Args:
            db_manager (DatabaseManager): An instance of the DatabaseManager.
        """
        super().__init__()
        self.db_manager = db_manager
        self.config = Config()

    def do_add_event(self, arg):
        """
        Adds a new event.
        Usage: add_event <title> <start_time> [description] [end_time] [location]
        Example: add_event "Team Meeting" "2023-12-25 10:00" "Discuss Q4 results" "2023-12-25 11:00" "Office"
        """
        args = arg.split('"')
        parsed_args = [a.strip() for a in args if a.strip()]

        if len(parsed_args) < 2:
            print("Usage: add_event <title> <start_time> [description] [end_time] [location]");
            return

        title = parsed_args[0]
        start_time_str = parsed_args[1]
        description = parsed_args[2] if len(parsed_args) > 2 else None
        end_time_str = parsed_args[3] if len(parsed_args) > 3 else None
        location = parsed_args[4] if len(parsed_args) > 4 else None

        start_time = parse_datetime(start_time_str)
        end_time = parse_datetime(end_time_str) if end_time_str else None

        if not start_time:
            print("Error: Invalid start time format. Please use YYYY-MM-DD HH:MM or similar.");