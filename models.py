import enum
from database import db
from werkzeug.security import generate_password_hash, check_password_hash

class UserRole(enum.Enum):
    """Defines valid user roles for storage in db."""
    ADMIN = "admin"
    CUSTOMER = "customer"

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.CUSTOMER, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    account = db.relationship('Account', back_populates='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name
        }

class Account(db.Model):
    __tablename__ = 'accounts'

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    balance = db.Column(db.Numeric(12, 2), default=0.0)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    user = db.relationship('User', back_populates='account', lazy=True)

    def to_dict(self):
        return {
            "name": self.name,
            "number": self.number,
            "balance": self.balance,
            "user_name": f"{self.user.first_name} {self.user.last_name}"
        }
