from flask import Flask, render_template, redirect, url_for, request, session
from sqlalchemy import text
import os
from dotenv import load_dotenv
from database import db
from models import User, Account, UserRole
from seed import seed_db
from werkzeug.security import generate_password_hash
import time

# For env variables
load_dotenv()

app = Flask(__name__)

# Set up db connection
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Bind SQLAlchemy to app
db.init_app(app)

# Create tables if they don't exist and seed db
with app.app_context():
    db.create_all()
    seed_db()


# Set up global logged in user based on session for templates to access
@app.context_processor
def set_current_user():
    user_id = session.get('user_id')
    user = db.session.get(User, user_id) if user_id else None
    return dict(current_user=user)

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
        return redirect(url_for("accounts"))
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
        return redirect(url_for("accounts"))
    except Exception as e:
        db.session.rollback()
        # Displays raw error message, giving valuable information to attacker
        return render_template(
            "new_account.html", error=str(e),
            security="vulnerable"
        ), 500


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
    return redirect(url_for("accounts"))


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
        return redirect(url_for("accounts"))
    except BaseException:
        db.session.rollback()
        # Appropriate generic error message is displayed back to user
        return render_template(
            "register.html",
            error="An error occurred creating the new user.",
            security="hardened"
        ), 500


# Routes
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
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
                "login.html", error=f"Too many failed login attempts. Please try again in {remaining} seconds."
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
                return redirect(url_for("admin"))
            else:
                return redirect(url_for("accounts"))

        # Secure code
        if security_choice == "hardened":    
            # Unsuccessful login = increment total_failed_logins
            total_failed_logins = session.get("total_failed_logins", 0) + 1
            session["total_failed_logins"] = total_failed_logins
            
            if total_failed_logins >=3:
                session["lockout_time_seconds"] = now + 30
                remaining = session["lockout_time_seconds"] - now
                return render_template(
                "login.html", error=f"Too many failed login attempts. Please try again in {remaining} seconds."
            ), 429

        return render_template(
            "login.html", error="Invalid email or password."
        ), 401


@app.route("/admin")
def admin():
    # User account specific hardening for Auth Bypass attacks
    if session.get("admin_hardened"):
        # Check user is logged in
        if "user_id" not in session:
            return redirect(url_for("login"))

        # Check user role is admin
        current_user_id = session.get('user_id')
        current_user = db.session.get(User, current_user_id)
        if current_user.role.value != "admin":
            return render_template("access_denied.html"), 403
    
    user_id = request.args.get("user_id")
    if user_id:
        stmt = f"SELECT * FROM users WHERE id = '{user_id}'"
        result = db.session.execute(text(stmt))
        user = result.fetchone()
    else:
        user = None
    # Secure code
    # user = db.session.get(User, user_id) if user_id else None

    if user:
        # If user was found with matching id, get their accounts and return
        accts = db.session.scalars(db.select(Account).where(
            Account.user_id == user.id)).all()
        return render_template(
            "admin.html", selected_user=user, accts=accts
        )
    else:
        if user_id:
            # Send error message that id did not match user
            return render_template(
                "admin.html", error="No user exists with that id."
            ), 400
        else:
            # Render initial page before user id selection by admin user
            return render_template("admin.html")


@app.route("/accounts", methods=["GET"])
def accounts():
    security_choice = request.form.get("security_choice")
    # Set security toggle for Auth Bypass attack on /admin
    if security_choice == "vulnerable":
        session["admin_hardened"] = False
    if security_choice == "hardened":
        session["admin_hardened"] = True
    # Can retrieve accounts data in template for global current user
    return render_template("accounts.html")


@app.route("/new_account", methods=["GET", "POST"])
def new_account():
    # Ensure user is logged in before accessing this page
    if "user_id" not in session:
        return redirect(url_for("login"))

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


@app.route("/edit_account/<int:id>", methods=["GET", "POST"])
def edit_account(id):
    # Ensure user is logged in before accessing this page
    if "user_id" not in session:
        return redirect(url_for("login"))

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


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    if request.method == "POST":
        security = request.form.get("security_choice")
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

        if security == "vulnerable":
            return register_insecure(email, first_name, last_name, role, password_hash)

        if security == "hardened":
            return register_secure(email, first_name, last_name, role, password_hash)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(port=8080, debug=True)
