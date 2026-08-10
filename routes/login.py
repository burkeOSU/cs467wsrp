from flask import Blueprint, render_template, redirect, url_for, request, session
from models import User
from database import db

login_bp = Blueprint('login', __name__)

@login_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    if request.method == "POST":

        # Get form data
        security_choice = request.form.get("security_choice")
        email = request.form.get("email")
        password = request.form.get("password")

        # Check that all form data is present
        if not email or not password:
            return (
                render_template(
                    "login.html",
                    error=f"Error: Missing email or password.",
                    security_choice=security_choice,
                ),
                400,
            )

        # Find user with specified email
        user = db.session.scalars(db.select(User).where(User.email == email)).first()

        if not user:
            return (
                render_template(
                    "login.html",
                    error="Please enter a valid email.",
                    security_choice=security_choice,
                ),
                401,
            )

        # Secure code
        # Check user is lockedout before checking password
        if security_choice == "hardened" and user.user_lockout:
            # Permanent lockout
            return (
                render_template(
                    "login.html",
                    error=f"Too many failed login attempts. The account is now locked.",
                    security_choice="hardened",
                    locked=user.user_lockout
                ),
                429,
            )

        # Validate password
        if user.check_password(password):
            session["user_id"] = user.id
            session["user_fname"] = user.first_name
            return redirect(url_for("account.accounts"))

        # Secure code
        else:
            if security_choice == "hardened":
                # Unsuccessful login = increment total_failed_logins
                user.total_failed_logins += 1
                if user.total_failed_logins >= 3:
                    user.user_lockout = True
                db.session.commit()

        return (
            render_template(
                "login.html",
                error="Invalid password.",
                security_choice=security_choice,
            ),
            401,
        )


# Attack: Brute Force
@login_bp.route("/reset_lockout", methods=["POST"])
def reset_lockout():
    # Reset lockout for account/email
    email = request.form.get("email")

    # Missing email
    if not email:
        return (
            render_template(
                "login.html",
                error="Please enter a valid email.",
                security_choice="hardened",
                locked=True
            ),
            400,
        )

    user = db.session.scalars(db.select(User).where(User.email == email)).first()

    # Invalid email
    if not user:
        return (
            render_template(
                "login.html",
                error="Please enter a valid email.",
                security_choice="hardened",
                locked=True
            ),
            400,
        )

    # Reset lockout
    user.user_lockout = False
    user.total_failed_logins = 0
    db.session.commit()

    # HTTP 200: Request Successful
    return (
        render_template(
            "login.html",
            error="Account lockout successfully reset.",
            security_choice="hardened",
        ),
        200,
    )