import tkinter as tk
from tkinter import messagebox
from app.models import DatabaseManager
from app.utils import parse_datetime, format_datetime
from app.config import Config

class GUI:
    """
    Graphical User Interface for the Planner Reminder Application.
    Provides a user-friendly interface to manage events and reminders.
    """
    def __init__(self, master, db_manager):
        self.master = master
        self.db_manager = db_manager
        self.config = Config()
        master.title(self.config.GUI_WINDOW_TITLE)
        master.geometry(self.config.GUI_WINDOW_SIZE)

        self._create_widgets()

    def _create_widgets(self):
        # Main frame
        main_frame = tk.Frame(self.master, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Event input frame
        input_frame = tk.LabelFrame(main_frame, text="Add/Edit Event", padx=10, pady=10)
        input_frame.pack(fill=tk.X, pady=10)

        tk.Label(input_frame, text="Title:").grid(row=0, column=0, sticky="w", pady=2)
        self.title_entry = tk.Entry(input_frame, width=50)
        self.title_entry.grid(row=0, column=1, pady=2)

        tk.Label(input_frame, text="Description:").grid(row=1, column=0, sticky="w", pady=2)
        self.description_entry = tk.Entry(input_frame, width=50)
        self.description_entry.grid(row=1, column=1, pady=2)

        tk.Label(input_frame, text="Start Time (YYYY-MM-DD HH:MM):").grid(row=2, column=0, sticky="w", pady=2)
        self.start_time_entry = tk.Entry(input_frame, width=50)
        self.start_time_entry.grid(row=2, column=1, pady=2)