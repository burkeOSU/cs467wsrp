"""Set up Flask, web app and database connection."""
import os

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, session, url_for

from database import db
from models import User
from routes.account import account_bp
from routes.admin import admin_bp
from routes.attack import attack_bp
from routes.login import login_bp
from routes.register import register_bp
from routes.toggle import toggle_bp
from seed import seed_db

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
    """Set up user based on session."""
    user_id = session.get("user_id")
    user = db.session.get(User, user_id) if user_id else None
    return dict(current_user=user)


# Error Handlers
@app.errorhandler(500)
def handle_exception(e):
    """Handle errors depending on session and security toggle state."""
    current_state = session.get("toggle_misexc", "vulnerable")
    detailed_error = getattr(e, "original_exception", e)

    if current_state == "vulnerable":
        return (
            render_template("error_500.html", error_message=str(detailed_error)),
            500,
        )
    else:
        return render_template("error_500.html"), 500


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
    """Render home page."""
    return render_template("index.html")


@app.route("/logout")
def logout():
    """Logout user, clear session and redirect to home page."""
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(port=8080, debug=False)
