"""Login routes for verifying user credentials."""
import time
from flask import Blueprint, render_template, redirect, url_for, request, session
from models import User, UserRole
from database import db

login_bp = Blueprint('login', __name__)

@login_bp.route("/login", methods=["GET", "POST"])
def login():
    """Authenticate user credentials and log in user."""
    if request.method == "GET":
        return render_template("login.html")

    if request.method == "POST":

        # Get form data
        security_choice = request.form.get("security_choice")
        email = request.form.get("email")
        password = request.form.get("password")

        # Check that all form data is present
        if not email or not password:
            return {"Error: Missing email or password."}, 400

        # Secure code
        if security_choice == "hardened":
            # Set lockout time remaining
            now = int(time.time())
            lockout_time = session.get("lockout_time_seconds", 0)

            if lockout_time > now:
                remaining = lockout_time - now
                # HTTP 429 = "Too Many Requests" error
                return render_template(
                "login.html",
                error=(
                    "Too many failed login attempts. "
                    f"Please try again in {remaining} seconds."
                ),
            ), 429
            # After 30 seconds, reset lockout timer and failed attempt counter
            if lockout_time > 0 and lockout_time <= now:
                session["total_failed_logins"] = 0
                session["lockout_time_seconds"] = 0

        # Find user with specified email
        user = db.session.scalars(
            db.select(User).where(User.email == email)).first()

        # Validate password if user exists
        if user and user.check_password(password):
            session["user_id"] = user.id
            session["user_fname"] = user.first_name
            # Secure code
            if security_choice == "hardened":
                # Successful login = reset lockout parameters
                session["total_failed_logins"] = 0
                session["lockout_time_seconds"] = 0
            if user.role == UserRole.ADMIN:
                return redirect(url_for('admin.admin'))
            else:
                return redirect(url_for("account.accounts"))

        # Secure code
        if security_choice == "hardened":    
            # Unsuccessful login = increment total_failed_logins
            total_failed_logins = session.get("total_failed_logins", 0) + 1
            session["total_failed_logins"] = total_failed_logins

            if total_failed_logins >=3:
                session["lockout_time_seconds"] = now + 30
                remaining = session["lockout_time_seconds"] - now
                return render_template(
                "login.html",
                error=(
                    "Too many failed login attempts. "
                    f"Please try again in {remaining} seconds."
                ),
            ), 429

        return render_template(
            "login.html", error="Invalid email or password."
        ), 401
    