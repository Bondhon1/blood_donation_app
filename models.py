from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email_verified = db.Column(db.Boolean, default=False)  # Already present

    # ✅ New Fields
    name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    blood_group = db.Column(db.String(5), nullable=True)
    medical_history = db.Column(db.Text, nullable=True)

    # ✅ Profile Picture Column
    profile_picture = db.Column(db.String(255), nullable=True, default="default.jpg")

    def __init__(self, username, email, password, name=None, phone=None, address=None, blood_group=None, medical_history=None, profile_picture="default.jpg"):
        self.username = username
        self.email = email
        self.password = generate_password_hash(password)
        self.name = name
        self.phone = phone
        self.address = address
        self.blood_group = blood_group
        self.medical_history = medical_history
        self.profile_picture = profile_picture or "default.jpg"
    def check_password(self, password):
        return check_password_hash(self.password, password)