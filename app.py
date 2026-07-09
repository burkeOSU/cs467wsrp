from flask import Flask, render_template, redirect, url_for, request, session
from sqlalchemy.orm import joinedload
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
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
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
    user = db.session.get(User, user_id) if user_id else None if user_id else None
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
        user = db.session.scalars(db.select(User).where(User.email == email)).first()

        # Validate password if user exists
        if user and user.check_password(password):
            session["user_id"] = user.id
            session["user_fname"] = user.first_name
            return redirect(url_for("database"))
        
        return render_template("login.html", error="Invalid email or password."), 401

@app.route("/database")
def database():
    user_id = session.get("user_id")
    user = db.session.get(User, user_id) if user_id else None

    # Retrieve all accounts if logged in user is admin
    all_accts = None
    if user and user.role == UserRole.ADMIN:
        statement = db.select(Account).options(joinedload(Account.user))
        all_accts = db.session.scalars(statement).all()

    # Can retrieve accounts data in template for global current user
    return render_template("database.html", all_accts=all_accts)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(port=8080, debug=True)
