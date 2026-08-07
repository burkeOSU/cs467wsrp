from flask import Blueprint, render_template, redirect, url_for, request, session
from sqlalchemy import text
from models import User, UserRole
from werkzeug.security import generate_password_hash
from database import db

register_bp = Blueprint('register', __name__)

@register_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    if request.method == "POST":
        # case insensitive, delete spaces
        email = request.form.get("email").strip().lower()
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        password = request.form.get("password")

        # Ensure all attributes are present
        if not email or not first_name or not last_name or not password:
            return render_template(
                "register.html", error="Missing one or more fields."
            ), 400

        # Check if user with email already exists
        query = "SELECT id FROM users WHERE email = :email"
        user = db.session.execute(text(query), {"email": email}).fetchone()
        if user:
            return render_template(
                "register.html", error="A user with that email already exists."
            ), 400

        # Encrypt the password
        password_hash = generate_password_hash(password)
        role = UserRole.CUSTOMER.value

        if not session["toggle_misexc"] or session["toggle_misexc"] == "vulnerable":
            return register_insecure(email, first_name, last_name, role, password_hash)

        if session["toggle_misexc"] == "hardened":
            return register_secure(email, first_name, last_name, role, password_hash)


# Helper functions
def register_insecure(email, first_name, last_name, role, password_hash):
    # Insecure stmt that allows for SQL injection
    stmt = (
        "INSERT INTO users (email, first_name, last_name, role, "
        "password_hash)"
        f"VALUES ('{email}', '{first_name}', '{last_name}', '{role}', "
        f"'{password_hash}')"
    )

    # Insecure code, not in try/except block
    result = db.session.execute(text(stmt))
    db.session.commit()
    # Retrieve newly created user info to set session variables
    new_user_id = result.lastrowid
    user = db.session.get(User, new_user_id)
    session["user_id"] = user.id
    session["user_fname"] = user.first_name
    return redirect(url_for("account.accounts"))


def register_secure(email, first_name, last_name, role, password_hash):
    # Insecure stmt that allows for SQL injection
    stmt = (
        "INSERT INTO users (email, first_name, last_name, role, "
        "password_hash)"
        f"VALUES ('{email}', '{first_name}', '{last_name}', '{role}', "
        f"'{password_hash}')"
    )
    # Try/except block to gracefully handle any exceptions
    try:
        # Send constructed stmt to database to register user
        result = db.session.execute(text(stmt))
        db.session.commit()
        # Retrieve newly created user info to set session variables
        new_user_id = result.lastrowid
        user = db.session.get(User, new_user_id)
        session["user_id"] = user.id
        session["user_fname"] = user.first_name
        return redirect(url_for("account.accounts"))
    except BaseException:
        db.session.rollback()
        # Appropriate generic error message is displayed back to user
        return render_template(
            "register.html",
            error="An error occurred creating the new user.",
            security="hardened"
        ), 500
