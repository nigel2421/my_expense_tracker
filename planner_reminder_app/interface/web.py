import os
from flask import Flask, render_template, request, redirect, url_for
from app.utils import parse_datetime
from app.config import Config

def run_web_server(db_manager, host='127.0.0.1', port=5000):
    """
    Runs a Flask-based web interface for the application.
    """
    # Define the template folder path absolutely to avoid path issues.
    # This ensures Flask can find the templates regardless of where the script is run.
    template_dir = os.path.join(Config.BASE_DIR, 'templates')
    app = Flask(__name__, template_folder=template_dir)
    app.config['DB_MANAGER'] = db_manager

    @app.route('/')
    def index():
        """
        Displays a list of all events.
        """
        db = app.config['DB_MANAGER']
        events = db.get_all_events()
        return render_template('index.html', events=events)

    @app.route('/add', methods=['GET', 'POST'])
    def add_event():
        """
        Handles adding a new event via a web form.
        """
        if request.method == 'POST':
            title = request.form.get('title')
            start_time_str = request.form.get('start_time')
            description = request.form.get('description')
            location = request.form.get('location')

            if title and start_time_str:
                start_time = parse_datetime(start_time_str)
                if start_time:
                    db = app.config['DB_MANAGER']
                    db.add_event(title, start_time, description, location=location)
                    return redirect(url_for('index'))
            # Handle error case - for now, just redirect back to form
            return redirect(url_for('add_event'))

        return render_template('add_event.html')

    @app.route('/edit/<int:event_id>', methods=['GET', 'POST'])
    def edit_event(event_id):
        """
        Handles editing an existing event.
        """
        db = app.config['DB_MANAGER']
        if request.method == 'POST':
            title = request.form.get('title')
            start_time_str = request.form.get('start_time')
            description = request.form.get('description')
            location = request.form.get('location')

            if title and start_time_str:
                start_time = parse_datetime(start_time_str)
                if start_time:
                    db.update_event(event_id, title, start_time, description, location=location)
                    return redirect(url_for('index'))
            # On error, redirect back to the edit page
            return redirect(url_for('edit_event', event_id=event_id))

        event = db.get_event_by_id(event_id)
        if event is None:
            return "Event not found", 404

        reminders = db.get_reminders_for_event(event_id)
        return render_template('edit_event.html', event=event, reminders=reminders)

    @app.route('/event/<int:event_id>/add_reminder', methods=['POST'])
    def add_reminder(event_id):
        """
        Handles adding a new reminder to an event.
        """
        db = app.config['DB_MANAGER']
        reminder_time_str = request.form.get('reminder_time')
        method = request.form.get('method', 'popup')

        if reminder_time_str:
            reminder_time = parse_datetime(reminder_time_str)
            if reminder_time:
                db.add_reminder(event_id,

    @app.route('/delete/<int:event_id>', methods=['POST'])
    def delete_event(event_id):
        """
        Handles deleting an event.
        """
        db = app.config['DB_MANAGER']
        db.delete_event(event_id)
        return redirect(url_for('index'))

    print(f"Starting web server at http://{host}:{port}")
    app.run(host=host, port=port, debug=True)