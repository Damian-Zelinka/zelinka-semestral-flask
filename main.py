from flask import request, jsonify, render_template
from config import app, db
from models import Role, User, Event, Registration
from datetime import datetime

from flask_login import LoginManager
from routes.authreg import authreg, login_manager
from routes.events import events

import sqlite3
from sqlalchemy import event
from sqlalchemy.engine import Engine


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()


app.register_blueprint(authreg)
app.register_blueprint(events)
login_manager.init_app(app)




@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    now = datetime.utcnow()

    pagination = Event.query.filter(Event.date >= now) \
        .order_by(Event.date.asc()) \
        .paginate(page=page, per_page=10, error_out=False)

    events = pagination.items

    event_data = []
    for event in events:
        accepted_count = Registration.query.filter_by(event_id=event.id, status='accepted').count()
        event_data.append({
            'event': event,
            'accepted_count': accepted_count
        })

    return render_template('index.html', event_data=event_data, pagination=pagination)

@app.route("/login")
def render_login():
    return render_template('login.html')

@app.route("/register")
def render_register():
    return render_template('register.html')

























if __name__ == "__main__":
    with app.app_context():
        db.create_all()


    app.run(debug=True)