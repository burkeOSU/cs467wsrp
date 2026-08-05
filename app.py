from flask import Flask, render_template, redirect, url_for, request, session
from sqlalchemy import text
import os
from dotenv import load_dotenv
from database import db
from models import User, Account, UserRole
from seed import seed_db
from werkzeug.security import generate_password_hash
from routes.login import login_bp
from routes.admin import admin_bp
from routes.account import account_bp

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

# Register blueprints
app.register_blueprint(login_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(account_bp)

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


# Routes
@app.route("/")
def home():
    return render_template("index.html")


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
