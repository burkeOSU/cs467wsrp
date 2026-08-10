from flask import Blueprint, render_template, redirect, url_for, request, session
from sqlalchemy import text
from models import Account
from database import db

account_bp = Blueprint('account', __name__)

@account_bp.route("/accounts", methods=["GET"])
def accounts():
    security_choice = request.form.get("security_choice")
    # Set security toggle for Auth Bypass attack on /admin
    if security_choice == "vulnerable":
        session["admin_hardened"] = False
    if security_choice == "hardened":
        session["admin_hardened"] = True
    # Can retrieve accounts data in template for global current user
    return render_template("accounts.html")


@account_bp.route("/new_account", methods=["GET", "POST"])
def new_account():
    # Ensure user is logged in before accessing this page
    if "user_id" not in session:
        return redirect(url_for("login.login"))

    if request.method == "GET":
        return render_template("new_account.html")

    if request.method == "POST":
        security_choice = request.form.get("security_choice")
        data = {
            "user_id": session.get('user_id'),
            "name": request.form.get("name"),
            "number": request.form.get("number"),
            "balance": request.form.get("balance")
        }

        # Check that all attributes are present
        if not data["name"] or not data["number"] or not data["balance"]:
            return render_template(
                "new_account.html", error="Missing one or more parameters."
            ), 400

        if security_choice == "vulnerable":
            # Allows for SQL injection to display informational error message
            # on screen (error-based SQLi)
            return create_account_insecure(data)

        if security_choice == "hardened":
            # Protects against SQL injection by parameterizing inputs
            return create_account_secure(data)


@account_bp.route("/edit_account/<int:id>", methods=["GET", "POST"])
def edit_account(id):
    # Ensure user is logged in before accessing this page
    if "user_id" not in session:
        return redirect(url_for("login.login"))

    # Get account with that id, check that it exists
    account = db.session.get(Account, id)
    if account is None:
        return render_template("edit_account.html", error="Account not found."), 404

    # Check that user has access to this account
    if account.user_id != session["user_id"]:
        return render_template("access_denied.html"), 403

    # Return form prefilled with acct data if GET
    if request.method == "GET":
        return render_template("edit_account.html", acct=account)

    # Process update
    if request.method == "POST":
        # Get form data
        security_choice = request.form.get("security_choice")
        name = request.form.get("name")
        number = request.form.get("number")
        balance = request.form.get("balance")

        # Check that all attributes are present
        if not name or not number or not balance:
            return render_template(
                "edit_account.html", 
                error="Missing one or more parameters.",
                acct=account
            ), 400

        try:
            # SQLAlchemy ORM auto generates prepared stmt with parameterized inputs (protects against SQLi)
            account.name = name
            account.number = number
            account.balance = balance
            db.session.commit()
            return render_template(
                "edit_account.html",
                acct=account,
                success="Account successfully updated.",
                security=security_choice)
        except:
            db.session.rollback()
            return render_template(
                "edit_account.html",
                error="An error occurred updating the account.",
                acct=account,
                security=security_choice
            ), 500


# Helper Functions
def create_account_secure(account_data):
    # Parameterized inputs to protect against SQL injection
    stmt = ("INSERT INTO accounts (name, number, balance, user_id)"
            "VALUES (:name, :number, :balance, :user_id)")
    try:
        # Secure submitting parameterized data
        db.session.execute(text(stmt), {
            "name": account_data["name"],
            "number": account_data["number"],
            "balance": account_data["balance"],
            "user_id": account_data["user_id"]
        })
        db.session.commit()
        return redirect(url_for("account.accounts"))
    except Exception:
        db.session.rollback()
        # Displays safer generic message instead of raw error msg
        return render_template(
            "new_account.html",
            error="An error occurred creating the new account.",
            security="hardened"
        ), 500


def create_account_insecure(account_data):
    # Allows for SQL injection
    stmt = (f"INSERT INTO accounts (name, number, balance, user_id)"
            f"VALUES ('{account_data['name']}', '{account_data['number']}', "
            f"{account_data['balance']}, {account_data['user_id']})")
    try:
        # Insecure submitting concatenated raw SQL to db
        db.session.execute(text(stmt))
        db.session.commit()
        return redirect(url_for("account.accounts"))
    except Exception as e:
        db.session.rollback()
        # Displays raw error message, giving valuable information to attacker
        return render_template(
            "new_account.html", error=str(e),
            security="vulnerable"
        ), 500
