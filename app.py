from flask import Flask, render_template, redirect, url_for, request, session
from sqlalchemy.orm import joinedload
from sqlalchemy import text
import os
from dotenv import load_dotenv
from database import db
from models import User, Account, UserRole
from seed import seed_db

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
        email = request.form.get("email")
        password = request.form.get("password")

        # Check that all form data is present
        if not email or not password:
            return {"Error: Missing email or password."}, 400

        # Find user with specified email
        user = db.session.scalars(
            db.select(User).where(User.email == email)).first()

        # Validate password if user exists
        if user and user.check_password(password):
            session["user_id"] = user.id
            session["user_fname"] = user.first_name
            if user.role == UserRole.ADMIN:
                return redirect(url_for("admin"))
            else:
                return redirect(url_for("accounts"))

        return render_template(
            "login.html", error="Invalid email or password."
        ), 401


@app.route("/admin")
def admin():
    user_id = request.args.get("user_id")
    if user_id:
        stmt = f"SELECT * FROM users WHERE id = '{user_id}'"
        result = db.session.execute(text(stmt))
        user = result.fetchone()
    else:
        user = None
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
    # Can retrieve accounts data in template for global current user
    return render_template("accounts.html")

 
@app.route("/new_account", methods=["GET", "POST"])
def new_account():
    if request.method == "GET":
        return render_template("new_account.html")
    
    if request.method == "POST":
        user_id = session.get('user_id')

        name = request.form.get("name")
        number = request.form.get("number")
        balance = request.form.get("balance")

        # Allows for SQL injection to display informational error message on screen
        stmt = (f"INSERT INTO accounts (name, number, balance, user_id)" 
                f"VALUES ('{name}', '{number}', {balance}, {user_id})")
        
        # Parameterized inputs to protect against SQL injection
        # stmt = (f"INSERT INTO accounts (name, number, balance, user_id)" 
        #         f"VALUES (:name, :number, :balance, :user_id)")
        try:
            # Insecure code
            db.session.execute(text(stmt))
            # Secure code
            # db.session.execute(text(stmt), {"name": name, "number": number, "balance": balance, "user_id": user_id})
            db.session.commit()
            return redirect(url_for("accounts"))
        except Exception as e:
            db.session.rollback()
            # Displays raw error message, giving valuable information to attacker
            return render_template(
               "new_account.html", error=str(e)
            ), 500
            # Displays safer generic message
            # return render_template(
            #     "new_account.html", error="An error occurred creating the new account."
            # ), 500


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(port=8080, debug=True)
