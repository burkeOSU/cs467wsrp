from flask import Blueprint, render_template, redirect, url_for, request, session
from sqlalchemy import text
from models import User, Account
from database import db

admin_bp = Blueprint('admin', __name__)

@admin_bp.route("/admin")
def admin():
    # User account specific hardening for Auth Bypass attacks
    if session.get("admin_hardened", True):
        # Check user is logged in
        if "user_id" not in session:
            return redirect(url_for("login.login"))

        # Check user role is admin
        current_user = db.session.get(User, session["user_id"])
        if current_user.role.value != "admin":
            return render_template("access_denied.html", showHint=True), 403

    security_choice = request.form.get("security_choice")
    user_id = request.args.get("user_id")
    # Secure code
    if session["toggle_sqli_blind"] == "hardened":
        if not user_id.isdigit():
            return (
                render_template("admin.html", error="Invalid user ID, only numerical characters accepted."),
                400,
            )
            
    else:
        if user_id:
            stmt = f"SELECT * FROM users WHERE id = '{user_id}'"
            result = db.session.execute(text(stmt))
            user = result.fetchone()
        else:
            user = None


    if user:
        # If user was found with matching id, get their accounts and return
        accts = db.session.scalars(
            db.select(Account).where(Account.user_id == user.id)
        ).all()
        return render_template("admin.html", selected_user=user, accts=accts)
    else:
        if user_id:
            # Send error message that id did not match user
            return (
                render_template("admin.html", error="No user exists with that id."),
                400,
            )
        else:
            # Render initial page before user id selection by admin user
            return render_template("admin.html")
