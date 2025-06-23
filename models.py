from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

from extensions import db

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)

    users = db.relationship('User', backref='role', lazy=True)

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
        }

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    middle_name = db.Column(db.String(100))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False, default=3)

    events = db.relationship('Event', backref='organizer', lazy=True)
    registrations = db.relationship('Registration', back_populates='volunteer', lazy=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def to_json(self):
        return {
            "id": self.id,
            "login": self.login,
            "passwordHash": self.password_hash,
            "lastName": self.last_name,
            "firstName": self.first_name,
            "middleName": self.middle_name,
            "roleId": self.role_id
        }

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    required_volunteers = db.Column(db.Integer, nullable=False)
    image_filename = db.Column(db.String(255), nullable=False)
    organizer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    registrations = db.relationship('Registration', back_populates='event', lazy=True, cascade="all, delete-orphan")

    def to_json(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "date": self.date,
            "location": self.location,
            "requiredVolunteers": self.required_volunteers,
            "imageFilename": self.image_filename,
            "organizerId": self.organizer_id
        }

class Registration(db.Model):
    __tablename__ = 'registrations'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='CASCADE'), nullable=False)
    volunteer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    contact_info = db.Column(db.String(255), nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='pending')

    volunteer = db.relationship('User', back_populates='registrations', lazy=True)
    event = db.relationship('Event', back_populates='registrations', lazy=True)

    def to_json(self):
        return {
            "id": self.id,
            "eventId": self.event_id,
            "volunteerId": self.volunteer_id,
            "contactInfo": self.contact_info,
            "registrationDate": self.registration_date,
            "status": self.status
        }
