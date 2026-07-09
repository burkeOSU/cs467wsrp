from database import db
from models import User, Account
from werkzeug.security import generate_password_hash

USERS = [
    {
        "email": "admin@example.com",
        "first_name": "Admin",
        "last_name": "Istrator",
        "role": "admin",
        "password": "adminPassword"
    },
    {
        "email": "buzz@example.com",
        "first_name": "Buzz",
        "last_name": "Lightyear",
        "role": "customer",
        "password": "buzzPassword"
    },
    {
        "email": "jessie@example.com",
        "first_name": "Jessie",
        "last_name": "Cowgirl",
        "role": "customer",
        "password": "jessiePassword"
    },
]

ACCOUNTS = [
    {
        "number": "12345678",
        "name": "Fidelity",
        "balance": 1000.50,
        "user_email": "buzz@example.com"
    },
    {
        "number": "57574433",
        "name": "Chase",
        "balance": 2300.45,
        "user_email": "buzz@example.com"
    },
    {
        "number": "88990033",
        "name": "Capital One",
        "balance": 1567.88,
        "user_email": "jessie@example.com"
    },

]

def seed_db():
    """Seeds above data into the database on app start."""
    try:
        # First add users
        for user in USERS:
            # Check if user already exists
            existing_user = db.session.scalars(db.select(User).where(User.email == user["email"])).first()
            # If not, create user
            if not existing_user:
                # Hash the pw before putting in the db
                hashed_password = generate_password_hash(user["password"])
                # Create new user from User model
                new_user = User(
                    email=user["email"],
                    first_name=user["first_name"],
                    last_name=user["last_name"],
                    role=user["role"],
                    password_hash=hashed_password
                )
                # Add new user to db session
                db.session.add(new_user)
        
        # Send new users to db
        db.session.flush()

        # Then add accounts
        for acct in ACCOUNTS:
            # Check if acct already exists
            existing_acct = db.session.scalars(
                                db.select(Account)
                                .join(Account.user)
                                .where(Account.number == acct["number"], User.email == acct["user_email"])
                            ).first()
            # If not, create acct
            if not existing_acct:
                # Find user
                acct_user = db.session.scalars(db.select(User).where(User.email == acct["user_email"])).first()
                # Create new acct from acct model
                new_acct = Account(
                    number=acct["number"],
                    name=acct["name"],
                    balance=acct["balance"],
                    user_id=acct_user.id
                )
                # Add new acct to db session
                db.session.add(new_acct)
        # Save changes to db if any were made
        if db.session.new:
            db.session.commit()
            print("Database seeded successfully.")
        else:
            print("Database already seeded, no changes made.")

    except Exception as e:
        db.session.rollback()
        print(f"Error during database seeding: {e}")
