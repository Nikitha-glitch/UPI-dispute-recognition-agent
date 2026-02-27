from app import app, bcrypt, User, db

with app.app_context():
    # Retrieve first user
    user = User.query.first()
    if user:
        print(f"User found: {user.phone}, MPIN Hash: {user.mpin_hash}")
        # Test hash matching for '1234'
        match = bcrypt.check_password_hash(user.mpin_hash, '1234')
        print(f"Matches '1234': {match}")
    else:
        print("No user found")
