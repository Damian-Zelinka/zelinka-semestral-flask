from flask import Blueprint, request, redirect, url_for, flash
from flask_login import login_user, logout_user, LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, db

authreg = Blueprint("authreg", __name__)
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@login_manager.unauthorized_handler
def unauthorized_callback():
    flash("Please log in to access this page.", "danger")
    return redirect(url_for('render_login'))



@authreg.route("/loginbp", methods=["POST"])
def login():
    login_input = request.form.get("login")
    password_input = request.form.get("password")
    remember = bool(request.form.get("remember_me"))

    user = User.query.filter_by(login=login_input).first()
    if user and check_password_hash(user.password_hash, password_input):
        login_user(user, remember=remember)
        flash("Logged in successfully", "success")
        return redirect(url_for("index"))

    flash("Invalid login or password", "danger")
    return redirect(url_for("render_login"))


@authreg.route("/registerbp", methods=["POST"])
def register():
    login_input = request.form.get("login")
    password_input = request.form.get("password")
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    middle_name = request.form.get("middle_name", "")

    if User.query.filter_by(login=login_input).first():
        flash("Login already taken", "danger")
        return redirect(url_for("render_register"))

    new_user = User(
        login=login_input,
        password_hash=generate_password_hash(password_input),
        first_name=first_name,
        last_name=last_name,
        middle_name=middle_name
    )
    db.session.add(new_user)
    db.session.commit()
    flash("Registration successful. Please log in.", "success")
    return redirect(url_for("render_login"))


@authreg.route("/logoutbp")
def logout():
    logout_user()
    flash("You have been logged out", "info")
    return redirect(url_for("index"))
