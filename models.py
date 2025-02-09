from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email_verified = db.Column(db.Boolean, default=False)

    # ✅ Additional Profile Fields
    name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    blood_group = db.Column(db.String(5), nullable=True)
    medical_history = db.Column(db.Text, nullable=True)

    # Address Fields
    division_id = db.Column(db.Integer, db.ForeignKey('divisions.id'), nullable=True)
    district_id = db.Column(db.Integer, db.ForeignKey('districts.id'), nullable=True)
    upazila_id = db.Column(db.Integer, db.ForeignKey('upazilas.id'), nullable=True)

    # ✅ Profile and Cover Picture
    profile_picture = db.Column(db.String(255), nullable=True, default="default.jpg")
    cover_photo = db.Column(db.String(255), nullable=True, default="default_cover.jpg")

    # ✅ Relationship: User has multiple blood requests
    blood_requests = db.relationship('BloodRequest', backref='user', lazy=True)
    # Relationships
    division = db.relationship('Divisions', backref='users', lazy=True)
    district = db.relationship('Districts', backref='users', lazy=True)
    upazila = db.relationship('Upazilas', backref='users', lazy=True)

    def __init__(self, username, email, password, name=None, phone=None, address=None, blood_group=None, medical_history=None, profile_picture="default.jpg", cover_photo="default_cover.jpg", division=None, district=None, Upazila=None):
        self.username = username
        self.email = email
        self.password = generate_password_hash(password)
        self.name = name
        self.phone = phone
        self.address = address
        self.blood_group = blood_group
        self.medical_history = medical_history
        self.division_id = division
        self.district_id = district
        self.upazila_id = Upazila
        self.profile_picture = profile_picture or "default.jpg"
        self.cover_photo = cover_photo or "default_cover.jpg"

    def check_password(self, password):
        return check_password_hash(self.password, password)

# ✅ Blood Request Model
class BloodRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    blood_group = db.Column(db.String(5), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    contact_info = db.Column(db.String(255), nullable=False)
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="Pending")  # Pending, Fulfilled, Canceled

    def __init__(self, user_id, blood_group, location, contact_info):
        self.user_id = user_id
        self.blood_group = blood_group
        self.location = location
        self.contact_info = contact_info

class Admin(db.Model):  # Fix the typo here
    admin_id = db.Column(db.Integer, primary_key=True)
    admin_username = db.Column(db.String(50), unique=True, nullable=False)
    admin_email = db.Column(db.String(120), unique=True, nullable=False)
    admin_password = db.Column(db.String(255), nullable=False)

    def __init__(self, admin_username, admin_email, admin_password):
        self.admin_username = admin_username
        self.admin_email = admin_email
        self.admin_password = generate_password_hash(admin_password)

    def check_password(self, password):
        return check_password_hash(self.admin_password, password)
# Models for divisions, districts, upazilas if not already defined:
class Divisions(db.Model):
    __tablename__ = "divisions"  # Ensure this matches the ForeignKey reference
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Districts(db.Model):
    __tablename__ = "districts"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    division_id = db.Column(db.Integer, db.ForeignKey("divisions.id"), nullable=False)  # Make sure this matches


class Upazilas(db.Model):
    __tablename__ = "upazilas"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    district_id = db.Column(db.Integer, db.ForeignKey('districts.id'), nullable=False)