from flask import Flask, render_template, redirect, url_for, session
import os
from dotenv import load_dotenv
from database import db
from models import User
from seed import seed_db
from routes.login import login_bp
from routes.admin import admin_bp
from routes.account import account_bp
from routes.register import register_bp
from routes.toggle import toggle_bp
from routes.attack import attack_bp

# For env variables
load_dotenv()

app = Flask(__name__)

# Set up db connection
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

# Bind SQLAlchemy to app
db.init_app(app)

# Create tables if they don't exist and seed db
with app.app_context():
    db.create_all()
    seed_db()


# Set up global logged in user based on session for templates to access
@app.context_processor
def set_current_user():
    user_id = session.get("user_id")
    user = db.session.get(User, user_id) if user_id else None
    return dict(current_user=user)


# Helper Functions
def create_account_secure(account_data):
    # Parameterized inputs to protect against SQL injection
    stmt = (
        "INSERT INTO accounts (name, number, balance, user_id)"
        "VALUES (:name, :number, :balance, :user_id)"
    )
    try:
        # Secure submitting parameterized data
        db.session.execute(
            text(stmt),
            {
                "name": account_data["name"],
                "number": account_data["number"],
                "balance": account_data["balance"],
                "user_id": account_data["user_id"],
            },
        )
        db.session.commit()
        return redirect(url_for("accounts"))
    except Exception:
        db.session.rollback()
        # Displays safer generic message instead of raw error msg
        return (
            render_template(
                "new_account.html",
                error="An error occurred creating the new account.",
                security="hardened",
            ),
            500,
        )

# Error Handlers
@app.errorhandler(500)
def handle_exception(e):
    current_state = session.get("toggle_misexc", "vulnerable")
    detailed_error = getattr(e, "original_exception", e)

    if current_state == "vulnerable":
        return render_template(
            "error_500.html",
            error_message=str(detailed_error)
        ), 500
    else:
        return render_template(
            "error_500.html"
        ), 500
def create_account_insecure(account_data):
    # Allows for SQL injection
    stmt = (
        f"INSERT INTO accounts (name, number, balance, user_id)"
        f"VALUES ('{account_data['name']}', '{account_data['number']}', "
        f"{account_data['balance']}, {account_data['user_id']})"
    )
    try:
        # Insecure submitting concatenated raw SQL to db
        db.session.execute(text(stmt))
        db.session.commit()
        return redirect(url_for("accounts"))
    except Exception as e:
        db.session.rollback()
        # Displays raw error message, giving valuable information to attacker
        return (
            render_template("new_account.html", error=str(e), security="vulnerable"),
            500,
        )


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
        return (
            render_template(
                "register.html",
                error="An error occurred creating the new user.",
                security="hardened",
            ),
            500,
        )
# Register blueprints
app.register_blueprint(login_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(account_bp)
app.register_blueprint(register_bp)


# Register blueprints
app.register_blueprint(login_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(account_bp)
app.register_blueprint(register_bp)
app.register_blueprint(toggle_bp)
app.register_blueprint(attack_bp)

# Routes
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(port=8080, debug=True)
