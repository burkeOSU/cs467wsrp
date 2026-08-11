from flask import Blueprint, redirect, request, session, url_for

toggle_bp = Blueprint("toggle", __name__)


@toggle_bp.route("/toggle_auth_bypass", methods=["POST"])
def toggle_auth_bypass():
    security_choice = request.form.get("security_choice")
    # Set security toggle for Auth Bypass attack on /admin
    if security_choice == "vulnerable":
        session["admin_hardened"] = False
    elif security_choice == "hardened":
        session["admin_hardened"] = True

    return redirect(url_for("account.accounts"))


@toggle_bp.route("/toggle_misexc", methods=["POST"])
def toggle_misexc():
    # Get the selection from the user and set the session variable
    security_choice = request.form.get("security_choice")
    if security_choice == "vulnerable":
        session["toggle_misexc"] = "vulnerable"
    else:
        session["toggle_misexc"] = "hardened"

    return redirect(url_for("register.register"))


@toggle_bp.route("/toggle_sqli_blind", methods=["POST"])
def toggle_sqli_blind():
    # Get the selection from the user and set the session variable
    security_choice = request.form.get("security_choice")
    if security_choice == "vulnerable":
        session["toggle_sqli_blind"] = "vulnerable"
    else:
        session["toggle_sqli_blind"] = "hardened"

    return redirect(url_for("admin.admin"))
