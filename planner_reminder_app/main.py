import threading
import os
import time
from app.models import DatabaseManager
from app.notifier import Notifier
from app.scheduler import Scheduler
from app.config import Config
from interface.cli import CLI
from interface.gui import GUI
from interface.web import run_web_server
import tkinter as tk

def main():
    config = Config()
    db_manager = DatabaseManager(config.get_database_path())
    notifier = Notifier(config)
    scheduler = Scheduler(db_manager, notifier, config.get_scheduler_interval())

    # Start the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=scheduler.start)
    scheduler_thread.daemon = True  # Allow the main program to exit even if scheduler is running
    scheduler_thread.start()

    try:
        # When using Flask's debug mode, it starts a reloader process that
        # re-runs this script. The child process would hang on the input()
        # prompt. We check an environment variable set by Werkzeug to detect
        # the child process and bypass the prompt.
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            # This is the reloader's child process, default to web interface
            interface_choice = 'web'
        else:
            # This is the main process, ask the user for their choice
            interface_choice = input("Choose interface (CLI/GUI/Web): ").strip().lower()

        if interface_choice == 'cli':
            cli = CLI(db_manager)
            cli.cmdloop()
        elif interface_choice == 'gui':
            root = tk.Tk()
            gui = GUI(root, db_manager)
            root.mainloop()
        elif interface_choice == 'web':
            # The web server runs in the main thread, and the scheduler is in the background.
            # When the web server is stopped (e.g., with Ctrl+C), the finally block will execute.
            run_web_server(db_manager)
        else:
            print("Invalid choice. Exiting.")
    except KeyboardInterrupt:
        print("\nApplication interrupted. Shutting down...")
    finally:
        print("Stopping scheduler...")
        scheduler.stop()
        # Wait for the scheduler thread to finish
        if scheduler_thread.is_alive():
            scheduler_thread.join(timeout=2)
        print("Scheduler stopped. Goodbye!")

if __name__ == "__main__":
    main()