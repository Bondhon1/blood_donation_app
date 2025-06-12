from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, UTC


db = SQLAlchemy()

# ✅ Association table for friendships
friends_association = db.Table('friends',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), primary_key=True),
    db.Column('friend_id', db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), primary_key=True)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email_verified = db.Column(db.Boolean, default=False)

    # Optional profile info
    name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    blood_group = db.Column(db.String(5), nullable=True)
    medical_history = db.Column(db.Text, nullable=True)

    
    # Address Fields
    division_id = db.Column(db.Integer, db.ForeignKey('divisions.id'), nullable=True)
    district_id = db.Column(db.Integer, db.ForeignKey('districts.id'), nullable=True)
    upazila_id = db.Column(db.Integer, db.ForeignKey('upazilas.id'), nullable=True)

    # Profile and cover picture
    profile_picture = db.Column(db.String(255), nullable=True, default="default.jpg")
    cover_photo = db.Column(db.String(255), nullable=True, default="default_cover.jpg")

    # ✅ Relationship: User has multiple blood requests
    blood_requests = db.relationship('BloodRequest', backref='user', lazy=True, cascade='all, delete')

    # Relationships
    division = db.relationship('Divisions', backref='users', lazy=True)
    district = db.relationship('Districts', backref='users', lazy=True)
    upazila = db.relationship('Upazilas', backref='users', lazy=True)
    comments = db.relationship('Comment', back_populates='user', lazy=True)
    blood_request_upvotes = db.relationship('BloodRequestUpvote', back_populates='user', lazy=True)

    # ✅ Friend system
    friends = db.relationship(
        'User',
        secondary=friends_association,
        primaryjoin=id == friends_association.c.user_id,
        secondaryjoin=id == friends_association.c.friend_id,
        backref=db.backref('friend_of', lazy='dynamic'),
        lazy='dynamic',
        passive_deletes=True
    )

    # ✅ Chat system
    sent_messages = db.relationship(
        'ChatMessage',
        foreign_keys='ChatMessage.sender_id',
        backref='sender_user',
        lazy=True,
        cascade='all, delete'
    )
    received_messages = db.relationship(
        'ChatMessage',
        foreign_keys='ChatMessage.receiver_id',
        backref='receiver_user',
        lazy=True,
        cascade='all, delete'
    )

    # ✅ Friend request system
    sent_friend_requests = db.relationship(
        'FriendRequest',
        foreign_keys='FriendRequest.sender_id',
        backref='sender',
        lazy=True,
        cascade='all, delete'
    )
    received_friend_requests = db.relationship(
        'FriendRequest',
        foreign_keys='FriendRequest.receiver_id',
        backref='receiver',
        lazy=True,
        cascade='all, delete'
    )

    def __init__(self, username, email, password, name=None, phone=None, address=None, blood_group=None, medical_history=None, profile_picture="default.jpg", cover_photo="default_cover.jpg"):
        self.username = username
        self.email = email
        self.password = generate_password_hash(password)
        self.name = name
        self.phone = phone
        self.address = address
        self.blood_group = blood_group
        self.medical_history = medical_history
        self.profile_picture = profile_picture or "default.jpg"
        self.cover_photo = cover_photo or "default_cover.jpg"

    def check_password(self, password):
        return check_password_hash(self.password, password)

class FriendRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())
    status = db.Column(db.String(20), default='pending')  # Options: 'pending', 'accepted', 'declined'

class ChatMessage(db.Model):  # Renamed from Message
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    images = db.Column(db.Text, nullable=True)
    attachments = db.relationship('ChatAttachment', backref='message', lazy=True)

    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    is_read = db.Column(db.Boolean, default=False)

class ChatAttachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('chat_message.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    filetype = db.Column(db.String(50), nullable=False)  # image, file, etc.
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
   


# ✅ Blood Request Model
class BloodRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    required_date = db.Column(db.Date, nullable=False)
    blood_group = db.Column(db.String(5), nullable=False)
    amount_needed = db.Column(db.Float, nullable=False)
    hospital_name = db.Column(db.String(200), nullable=False)
    urgency_status = db.Column(db.String(20), nullable=False)  # e.g., "High", "Medium", "Low"
    reason = db.Column(db.Text, nullable=False)
    images = db.Column(db.Text)  # Path to images if any
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default="Open")  # New status field
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    upvote_count = db.Column(db.Integer, default=0)  # ✅ New column to store upvotes
    donor_responses = db.relationship("DonorResponse", cascade="all, delete-orphan", back_populates="blood_request")

    upvotes = db.relationship(
        'BloodRequestUpvote',
        back_populates='blood_request',
        lazy=True,
        cascade="all, delete"
    )

    comments = db.relationship(
        'Comment',
        back_populates='blood_request',
        lazy=True,
        cascade="all, delete"
    )

    donors_assigned = db.Column(db.Integer, default=0)
    smoker_preference = db.Column(db.String(20), default="Allow Smokers")

    @property
    def donors_needed(self):
        """Returns the number of additional donors required"""
        return max(0, self.amount_needed - self.donors_assigned)

    @property
    def is_fulfilled(self):
        """Returns True if all required donors have been assigned"""
        return self.donors_needed == 0

    def assign_donor(self):
        """Assign a donor and update the status"""
        if self.donors_needed > 0:
            self.donors_assigned += 1
            if self.is_fulfilled:
                self.status = "Fulfilled"
    
    def to_dict(self):
        return {
            "id": self.id,
            "patient_name": self.patient_name,
            "blood_group": self.blood_group,
            "hospital_name": self.hospital_name,
            "urgency_status": self.urgency_status,
            "location": str(self.location) if self.location else "Unknown",
            "contact_number": self.user.phone or "Not provided",
            "amount_needed": self.amount_needed,
            "required_date": self.required_date.isoformat(),
            "reason": self.reason,
            "images": self.images or [],
            "status": self.status,
            "upvotes": len(self.upvotes),  # ✅ Count instead of sending objects
            "created_at": self.created_at.isoformat(),
            "donors_assigned": self.donors_assigned or 0,
            "user": {
                "username": self.user.username,
                "profile_picture": self.user.profile_picture
            }
        }




class Admin(db.Model):  
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
    __tablename__ = "divisions"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

class Districts(db.Model):
    __tablename__ = "districts"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    division_id = db.Column(db.Integer, db.ForeignKey("divisions.id"), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

class Upazilas(db.Model):
    __tablename__ = "upazilas"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    district_id = db.Column(db.Integer, db.ForeignKey('districts.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    blood_request_id = db.Column(db.Integer, db.ForeignKey('blood_request.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    image = db.Column(db.String(200), nullable=True)

    # ✅ Use back_populates to explicitly define relationships
    user = db.relationship('User', back_populates='comments')
    blood_request = db.relationship('BloodRequest', back_populates='comments')
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy=True)
    likes = db.relationship('CommentLike', backref='comment', lazy=True)

class Reply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    image = db.Column(db.String(200), nullable=True)

    user = db.relationship('User')
    comment = db.relationship('Comment', back_populates='replies')
    likes = db.relationship('ReplyLike', backref='reply', lazy=True)  # ✅ Add this line

Comment.replies = db.relationship('Reply', back_populates='comment', cascade='all, delete-orphan')


class CommentLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=False)


class ReplyLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reply_id = db.Column(db.Integer, db.ForeignKey('reply.id'), nullable=False)


class BloodRequestUpvote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    blood_request_id = db.Column(db.Integer, db.ForeignKey('blood_request.id'), nullable=False)

    user = db.relationship('User', back_populates='blood_request_upvotes')
    blood_request = db.relationship('BloodRequest', back_populates='upvotes')

    # Ensure uniqueness: One user can upvote only once per request
    __table_args__ = (db.UniqueConstraint('user_id', 'blood_request_id', name='unique_upvote'),)

class DonorApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    nid_or_birth_certificate = db.Column(db.String(255), nullable=False)  # Image path
    has_donated_before = db.Column(db.Boolean, nullable=False)
    last_donation_date = db.Column(db.Date, nullable=True)
    medical_conditions = db.Column(db.Text, nullable=True)
    medical_history_images = db.Column(db.String(500), nullable=True)  # Comma-separated image paths
    status = db.Column(db.String(20), default="Pending")

    user = db.relationship('User', backref=db.backref('donor_application', uselist=False))


class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reported_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer)
    reason = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Referral(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('blood_request.id'), nullable=False)
    donor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(50), default='Pending')  # Accepted / Rejected
    referred_at = db.Column(db.DateTime, default=datetime.utcnow)

    donor = db.relationship('User', foreign_keys=[donor_id])
    blood_request = db.relationship('BloodRequest', foreign_keys=[request_id])

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    admin_recipient_id = db.Column(db.Integer, db.ForeignKey('admin.admin_id'), nullable=True)
    message = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    link = db.Column(db.String(255), nullable=True)  # Optional link for more details

    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_notifications')
    admin_recipient = db.relationship('Admin', foreign_keys=[admin_recipient_id], backref='admin_notifications')
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_notifications')

class DonorResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    request_id = db.Column(db.Integer, db.ForeignKey('blood_request.id'), nullable=False)
    responded_at = db.Column(db.DateTime, default=datetime.utcnow)

    donor = db.relationship('User', backref='responses')
    blood_request = db.relationship('BloodRequest', back_populates='donor_responses')

