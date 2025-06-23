from datetime import datetime
import bleach
import markdown
from werkzeug.utils import secure_filename
from flask import Blueprint, current_app, request, redirect, url_for, flash, render_template
from flask_login import login_user, logout_user, LoginManager, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, Event, Registration, db
import os
import uuid

events = Blueprint("events", __name__)



@events.route('/events/create', methods=['GET'])
@login_required
def render_create_event():
    if not current_user.role:
        flash("You do not have permission to access this page.", "danger")
        return redirect(url_for('index'))
    if current_user.role.name != 'administrator':
        flash("You do not have permission to access this page."+current_user.role.name, "danger")
        return redirect(url_for('index'))
    return render_template('create_event.html')



@events.route('/events/create', methods=['POST'])
@login_required
def create_event():
    if not current_user.role or current_user.role.name != 'administrator':
        flash("You do not have permission to perform this action.", "danger")
        return redirect(url_for('index'))

    try:
        title = request.form['title']
        raw_description = request.form['description']
        date = request.form['date']
        location = request.form['location']
        required = request.form['required_volunteers']
        image = request.files['image']

        if not image:
            flash("Image is required.", "warning")
            return redirect(request.url)

        html_description = markdown.markdown(raw_description)
        ALLOWED_TAGS = list(bleach.sanitizer.ALLOWED_TAGS) + [
            "p", "br", "hr", "h1", "h2", "h3", "strong", "em", "ul", "ol", "li"
        ]
        ALLOWED_ATTRIBUTES = {}
        description = bleach.clean(html_description, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)

        filename = secure_filename(image.filename)
        ext = os.path.splitext(filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        image.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename))

        new_event = Event(
            title=title,
            description=description,
            date=datetime.strptime(date, '%Y-%m-%d'),
            location=location,
            required_volunteers=required,
            image_filename=unique_filename,
            organizer_id=current_user.id
        )
        db.session.add(new_event)
        db.session.commit()

        flash("Event created successfully!", "success")
        return redirect(url_for('index'))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error during event creation: {e}")
        flash(f"An error occurred: {e}", "danger")
        return redirect(request.url)

    



@events.route('/events/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    if not current_user.role or current_user.role.name not in ['administrator', 'moderator']:
        flash("You do not have permission to perform this action.", "danger")
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            event.title = request.form['title']
            raw_description = request.form['description']

            html_description = markdown.markdown(raw_description)
            ALLOWED_TAGS = list(bleach.sanitizer.ALLOWED_TAGS) + [
                "p", "br", "hr", "h1", "h2", "h3", "strong", "em", "ul", "ol", "li"
            ]
            ALLOWED_ATTRIBUTES = {}
            event.description = bleach.clean(html_description, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)

            event.date = datetime.strptime(request.form['date'], '%Y-%m-%d')
            event.location = request.form['location']
            event.required_volunteers = request.form['required_volunteers']

            db.session.commit()
            flash("Event updated successfully!", "success")
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash("An error occurred while updating the event.", "danger")
            return redirect(request.url)

    return render_template('edit_event.html', event=event)




@events.route('/events/<int:event_id>')
def view_event(event_id):
    event = Event.query.get_or_404(event_id)

    accepted_volunteers = Registration.query.filter_by(
        event_id=event_id, status='accepted'
    ).order_by(Registration.registration_date.desc()).all()
    accepted_count = len(accepted_volunteers)

    pending_volunteers = []
    if current_user.is_authenticated and current_user.role and current_user.role.name in ['moderator', 'administrator']:
        pending_volunteers = Registration.query.filter_by(
            event_id=event_id, status='pending'
        ).order_by(Registration.registration_date.desc()).all()

    user_registration = None
    if current_user.is_authenticated and current_user.role and current_user.role.name == 'user':
        user_registration = Registration.query.filter_by(
            event_id=event_id, volunteer_id=current_user.id
        ).first()

    return render_template('view_event.html', event=event,
                           accepted_volunteers=accepted_volunteers,
                           pending_volunteers=pending_volunteers,
                           user_registration=user_registration,
                           accepted_count=accepted_count)



@events.route('/registrations/<int:registration_id>/<action>', methods=['POST'])
@login_required
def moderate_registration(registration_id, action):
    if not current_user.role or current_user.role.name not in ['moderator', 'administrator']:
        flash("You do not have permission to moderate registrations.", "danger")
        return redirect(url_for('index'))

    registration = Registration.query.get_or_404(registration_id)

    if action not in ['accept', 'reject']:
        flash("Invalid action.", "danger")
        return redirect(url_for('events.view_event', event_id=registration.event_id))

    event = registration.event
    accepted_count = Registration.query.filter_by(
        event_id=registration.event_id,
        status='accepted'
    ).count()

    if action == 'accept':
        if accepted_count >= event.required_volunteers:
            flash("Cannot accept more volunteers. Required number already reached.", "warning")
            if registration.status != 'rejected':
                registration.status = 'rejected'
                db.session.commit()
            return redirect(url_for('events.view_event', event_id=registration.event_id))

        registration.status = 'accepted'
        accepted_count += 1

        if accepted_count >= event.required_volunteers:
            Registration.query.filter_by(
                event_id=registration.event_id,
                status='pending'
            ).update({'status': 'rejected'})

    else:
        registration.status = 'rejected'

    db.session.commit()
    flash(f"Registration has been {registration.status}.", "success")
    return redirect(url_for('events.view_event', event_id=registration.event_id))



@events.route('/events/<int:event_id>/register', methods=['POST'])
@login_required
def register_for_event(event_id):
    if not current_user.role or current_user.role.name != 'user':
        flash("You do not have permission to register.", "danger")
        return redirect(url_for('events.view_event', event_id=event_id))

    existing = Registration.query.filter_by(event_id=event_id, volunteer_id=current_user.id).first()
    if existing:
        flash("You are already registered for this event.", "info")
        return redirect(url_for('events.view_event', event_id=event_id))

    contact_info = request.form.get('contact_info')
    if not contact_info:
        flash("Contact information is required.", "warning")
        return redirect(url_for('events.view_event', event_id=event_id))
    

    event = Event.query.get_or_404(event_id)
    accepted_count = Registration.query.filter_by(
        event_id=event_id,
        status='accepted'
    ).count()

    if accepted_count >= event.required_volunteers:
        flash("Registration for this event is closed. Required volunteers already reached.", "warning")
        return redirect(url_for('events.view_event', event_id=event_id))


    registration = Registration(
        volunteer_id=current_user.id,
        event_id=event_id,
        contact_info=contact_info,
        status='pending'
    )
    db.session.add(registration)
    db.session.commit()
    flash("Registration submitted! Waiting for approval.", "success")
    return redirect(url_for('events.view_event', event_id=event_id))



@events.route('/event/<int:event_id>/delete', methods=['POST'])
@login_required
def delete_event(event_id):
    if current_user.role.name != 'administrator':
        flash("У вас нет прав для удаления мероприятия.", "danger")
        return redirect(url_for('index'))

    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()

    flash(f"Мероприятие «{event.title}» успешно удалено.", "success")
    return redirect(url_for('index'))