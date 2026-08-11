"""Models for users and accounts in database."""
import enum

from werkzeug.security import check_password_hash, generate_password_hash

from database import db


class UserRole(enum.Enum):
    """Defines valid user roles for storage in db."""

    ADMIN = "admin"
    CUSTOMER = "customer"


class User(db.Model):
    """Defines user identity, role, password and lockout status.)"""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.CUSTOMER, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # Lockout function (Prevent Brute Force/BurpIntruder)
    user_lockout = db.Column(db.Boolean, default=False, nullable=False)
    total_failed_logins = db.Column(db.Integer, default=0, nullable=False)

    account = db.relationship("Account", back_populates="user", lazy=True)

    def set_password(self, password):
        """Generate hashed password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check entered password against stored hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Set user id, email and names."""
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
        }


class Account(db.Model):
    """Defines account information and linked user.)"""
    __tablename__ = "accounts"

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    balance = db.Column(db.Numeric(12, 2), default=0.0)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    user = db.relationship("User", back_populates="account", lazy=True)

    def to_dict(self):
        """Set account name, id, balance and associated names."""
        return {
            "name": self.name,
            "number": self.number,
            "balance": self.balance,
            "user_name": f"{self.user.first_name} {self.user.last_name}",
        }
