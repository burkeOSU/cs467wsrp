"""Toggling route for selecting vulnerable/hardened security mode for Register page."""
from flask import Blueprint, redirect, url_for, request, session

toggle_bp = Blueprint('toggle', __name__)

@toggle_bp.route("/toggle_misexc", methods=["POST"])
def toggle_misexc():
    """Toggle security mode for Register page."""
    # Get the selection from the user and set the session variable
    security_choice = request.form.get("security_choice")
    if security_choice == "vulnerable":
        session["toggle_misexc"] = "vulnerable"
    else:
        session["toggle_misexc"] = "hardened"

    return redirect(url_for('register.register'))
