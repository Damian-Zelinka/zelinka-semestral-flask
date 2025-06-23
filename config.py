from flask import Flask, request, render_template
from flask_cors import CORS
import os
import sqlite3
from datetime import datetime
from sqlalchemy import event
from sqlalchemy.engine import Engine

from extensions import db, migrate
from models import Role, User, Event, Registration
from routes.authreg import authreg, login_manager
from routes.events import events
from flask_login import LoginManager

app = Flask(__name__)
CORS(app)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mydatabase.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join('static', 'uploads')

db.init_app(app)
migrate.init_app(app, db)

app.register_blueprint(authreg)
app.register_blueprint(events)
login_manager.init_app(app)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    now = datetime.utcnow()
    pagination = Event.query.filter(Event.date >= now).order_by(Event.date.asc()).paginate(page=page, per_page=10, error_out=False)
    events = pagination.items
    event_data = [{'event': event, 'accepted_count': Registration.query.filter_by(event_id=event.id, status='accepted').count()} for event in events]
    return render_template('index.html', event_data=event_data, pagination=pagination)

@app.route("/login")
def render_login():
    return render_template('login.html')

@app.route("/register")
def render_register():
    return render_template('register.html')
