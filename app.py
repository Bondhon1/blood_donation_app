from flask import Flask, render_template, redirect, url_for, flash, session, request, jsonify, abort
from config import Config
from models import db, User, BloodRequest, Admin, Divisions, Districts, Upazilas, Comment, BloodRequestUpvote, DonorApplication, Reply, CommentLike, ReplyLike, Report, Referral, Notification, DonorResponse
from forms import RegistrationForm, LoginForm, BloodRequestForm, DonorApplicationForm, AdminLoginForm
from werkzeug.security import check_password_hash, generate_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import os
from werkzeug.utils import secure_filename
from flask import current_app
import requests
from geopy.distance import geodesic  # To calculate the closest location
from datetime import datetime, timezone, UTC, timedelta
from flask_login import current_user, login_required
import uuid
import json
from PIL import Image
from PIL import Image, ExifTags
from flask_wtf.csrf import CSRFProtect
from flask_socketio import SocketIO, join_room


UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static/profile_pics')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__)
csrf = CSRFProtect(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config.from_object(Config)
db.init_app(app)
migrate = Migrate(app, db) 
socketio = SocketIO(app, cors_allowed_origins="*")  # ← ADD THIS HERE



ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


mail = Mail(app)
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])


@app.route('/')
def home():
    if 'user_id' in session:
        user = User.query.filter_by(id=session['user_id']).first()
        if user:
            return redirect(url_for('news_feed', username=user.username))  # ✅ Pass username
    return render_template('home.html')

@socketio.on('join')
def handle_join(data):
    user_id = data.get('user_id')
    if user_id:
        join_room(str(user_id))  # Use string in case user_id is int
        print(f"User {user_id} joined their socket room.")

### ✅ API: Check Username & Email Availability
@app.route('/check_user', methods=['POST'])
def check_user():
    data = request.json
    username = data.get("username")
    email = data.get("email")

    if not username and not email:
        return jsonify({"error": "Invalid request"}), 400

    user = User.query.filter((User.username == username) | (User.email == email)).first()
    
    if user:
        message = "Username is already taken." if user.username == username else "Email is already in use."
        return jsonify({"exists": True, "message": message}), 200
    
    return jsonify({"exists": False, "message": "Available"}), 200

### ✅ API: User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter((User.username == form.username.data) | (User.email == form.email.data)).first()
        
        if existing_user:
            message = "Username is already taken." if existing_user.username == form.username.data else "Email is already in use."
            flash(message, "danger")
            return redirect(url_for('register'))
        
        # ✅ Fix: Hash password in the User model constructor, not here
        new_user = User(
            username=form.username.data, 
            email=form.email.data, 
            password=form.password.data  # Don't hash here, let model handle it
        )
        db.session.add(new_user)
        db.session.commit()

        send_verification_email(new_user.email)
        
        flash("Registration successful! Please verify your email before logging in.", "success")
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)



def send_verification_email(email):
    token = generate_email_token(email)
    msg = Message("Verify Your Email", sender="samiulhaquebondhon0@gmail.com", recipients=[email])
    msg.body = f"Click the link to verify your email: {url_for('verify_email', token=token, _external=True)}"
    mail.send(msg)
@app.route('/verify_email/<token>')
def verify_email(token):
    try:
        email = serializer.loads(token, salt="email-confirm", max_age=3600)  # Expires in 1 hour
        user = User.query.filter_by(email=email).first()

        if user:
            user.email_verified = True
            db.session.commit()
            flash("Email verified successfully!", "success")
            return redirect(url_for('news_feed', username=user.username))
    except:
        flash("Invalid or expired token!", "danger")

    return redirect(url_for('home'))


def generate_email_token(email):
    return serializer.dumps(email, salt="email-confirm")

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and user.check_password(form.password.data):  # ✅ Using method in User model
            session['user_id'] = user.id
            session['username'] = user.username  # ✅ Store username in session
            flash("Login successful!", "success")
            return redirect(url_for('news_feed', username=user.username))  # ✅ Fixed
        
        flash("Invalid credentials", "danger")  # ✅ Ensure message shows
        return redirect(url_for('login'))  # ✅ Redirect after flashing message
    
    return render_template('login.html', form=form)
@app.route('/api/get_user_id')
def get_user_id():
    user_id = session.get('user_id')
    admin_id = session.get('admin_id')
    if user_id:
        return {'user_id': user_id, 'is_admin': False}, 200
    elif admin_id:
        return {'user_id': admin_id, 'is_admin': True}, 200
    else:
        return {'user_id': None, 'is_admin': None}, 200



@app.before_request
def update_last_active():
    if 'user_id' in session:
        session['last_active'] = datetime.now(timezone.utc).timestamp()

@app.before_request
def auto_logout():
    timeout = 600  # 10 minutes
    if 'last_active' in session and (datetime.now(timezone.utc).timestamp() - session['last_active'] > timeout):
        session.clear()
        flash("Session expired. Please log in again.", "info")
        return redirect(url_for('login'))

@app.route("/save_location", methods=["POST"])
def save_location():
    try:
        data = request.json
        user_lat = data.get("latitude")
        user_lon = data.get("longitude")

        if not user_lat or not user_lon:
            return jsonify({"error": "Invalid location data"}), 400

        # 🏙 Find the closest district based on latitude & longitude
        districts = Districts.query.all()
        nearest_district = None
        min_distance = float("inf")

        for district in districts:
            if district.latitude and district.longitude:
                dist = geodesic((user_lat, user_lon), (district.latitude, district.longitude)).km
                if dist < min_distance:
                    min_distance = dist
                    nearest_district = district
        print(nearest_district)
        if nearest_district:
            division = db.session.get(Divisions, nearest_district.division_id)  # ✅ Fixed
            session["district"] = nearest_district.name
            session["division"] = division.name if division else "Unknown"

            print(f"✅ Nearest District: {nearest_district.name}, Division: {session['division']}")

            return jsonify({
                "message": "Location received!",
                "district": session["district"],
                "division": session["division"]
            }), 200
        else:
            return jsonify({"error": "No district found"}), 404

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"error": "Something went wrong"}), 500



### ✅ API: User Logout
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect(url_for('home'))
@app.context_processor
def inject_user_id():
    return {'user_id': session.get('user_id')}

@app.route('/news_feed/<username>')
def news_feed(username):
    if 'user_id' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))
    user_id = session.get('user_id')
    
    user = User.query.get(session['user_id'])
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('login'))

    # ✅ Fetch unread DB notifications
    db_notifications = Notification.query.filter_by(
        recipient_id=user.id, is_read=False
    ).order_by(Notification.timestamp.desc()).all()

    notif_messages = [
        {
            "id": n.id,
            "message": n.message,
            "link": n.link
        }
        for n in db_notifications
    ]


    # Add non-database inline notifications
    if not user.email_verified:
        notif_messages.append({
            "id": None,
            "message": "Please verify your email address. <a href='/resend_verification'>Resend</a>",
            "link": None
        })

 

    # ✅ Store in session for use in popup
    session['notifications'] = notif_messages

    # --- Blood Request Priority Logic ---
    LIMIT_COUNT = 10
    session_district = session.get('district')
    session_division = session.get('division')

    priority1 = BloodRequest.query.filter(BloodRequest.location.ilike(f"%{session_district}%")).all()
    priority2 = BloodRequest.query.filter(
        BloodRequest.location.ilike(f"%{session_division}%"),
        ~BloodRequest.location.ilike(f"%{session_district}%")
    ).limit(LIMIT_COUNT).all()
    priority3 = BloodRequest.query.filter(
        BloodRequest.urgency_status.ilike("High"),
        ~BloodRequest.location.ilike(f"%{session_division}%")
    ).limit(LIMIT_COUNT).all()

    priority_ids = {req.id for req in priority1 + priority2 + priority3}
    priority4 = BloodRequest.query.filter(~BloodRequest.id.in_(priority_ids)).limit(LIMIT_COUNT).all()

    sorted_requests = priority1 + priority2 + priority3 + priority4

    donor_app = DonorApplication.query.filter_by(user_id=user.id, status='Approved').first()
    session['is_donor'] = donor_app is not None

    return render_template(
        'news_feed.html',
        username=username,
        user=user,
        donation_requests=sorted_requests,
        notifications=session['notifications'],
        user_id=user_id,
    )


@app.route('/api/news_feed')
def api_news_feed():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    session_district = session.get('district')
    session_division = session.get('division')
    if not session_district or not session_division:
        return jsonify({"error": "Missing location information."}), 400

    offset = int(request.args.get('offset', 0))
    limit = int(request.args.get('limit', 6))

    # Priority logic as before...
    LIMIT_COUNT = 10
    location_str = f"{session_district}, {session_division}"

    priority1 = BloodRequest.query.filter(BloodRequest.location.ilike(f"%{session_district}%")).all()
    priority2 = BloodRequest.query.filter(
        BloodRequest.location.ilike(f"%{session_division}%"),
        ~BloodRequest.location.ilike(f"%{session_district}%")
    ).limit(LIMIT_COUNT).all()
    priority3 = BloodRequest.query.filter(
        BloodRequest.urgency_status.ilike("High"),
        ~BloodRequest.location.ilike(f"%{session_division}%")
    ).limit(LIMIT_COUNT).all()

    priority_ids = {req.id for req in priority1 + priority2 + priority3}
    priority4 = BloodRequest.query.filter(~BloodRequest.id.in_(priority_ids)).limit(LIMIT_COUNT).all()

    sorted_requests = priority1 + priority2 + priority3 + priority4
    paginated = sorted_requests[offset:offset+limit]

    return jsonify({
        "requests": [r.to_dict() for r in paginated],
        "has_more": offset + limit < len(sorted_requests)
    })

@app.route('/admin/reports')
def admin_reports():
    if 'user_id' not in session:
        flash("Login required", "warning")
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if not user or not user.is_admin:
        flash("Access denied", "danger")
        return redirect(url_for('news_feed', username=session.get('username')))

    reports = Report.query.order_by(Report.created_at.desc()).all()
    return render_template('admin_reports.html', reports=reports)



@app.route('/referral/<int:referral_id>/<action>')
def handle_referral(referral_id, action):
    if 'user_id' not in session:
        flash("Login required", "warning")
        return redirect(url_for('login'))

    referral = Referral.query.get(referral_id)
    if not referral or referral.referred_user_id != session['user_id']:
        flash("Unauthorized action", "danger")
        return redirect(url_for('donor_referrals'))

    if action == 'accept':
        referral.status = 'Accepted'
        flash("Referral accepted!", "success")
        # Optionally: auto-create donor application, notify original referrer, etc.
    elif action == 'reject':
        referral.status = 'Rejected'
        flash("Referral rejected", "info")
    
    db.session.commit()
    return redirect(url_for('donor_referrals'))

@app.route('/donor_response/<int:request_id>', methods=['POST'])
def donor_response(request_id):
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    user = db.session.get(User, session['user_id'])
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    donor_app = DonorApplication.query.filter_by(user_id=user.id, status='Approved').first()
    if not donor_app:
        return jsonify({"status": "error", "message": "Only approved donors can respond."}), 403

    # Check 90-day interval
    last_donation = donor_app.last_donation_date
    if last_donation and (datetime.now(timezone.utc).date() - last_donation).days < 90:
        next_date = last_donation + timedelta(days=90)
        return jsonify({
            "status": "error",
            "message": f"You can donate again after {next_date.strftime('%Y-%m-%d')}."
        })

    blood_request = db.session.get(BloodRequest, request_id)
    if not blood_request:
        return jsonify({"status": "error", "message": "Request not found"}), 404

    if blood_request.is_fulfilled:
        return jsonify({"status": "error", "message": "This request is already fulfilled."})

    # Check for duplicate donor assignment
    already_responded = DonorResponse.query.filter_by(
        donor_id=user.id, request_id=request_id
    ).first()
    if already_responded:
        return jsonify({
            "status": "error",
            "message": "You have already responded to this request."
        })

    # Check blood group match
    if user.blood_group != blood_request.blood_group:
        return jsonify({
            "status": "error",
            "message": "Your blood group does not match the required blood group for this request."
        })

    try:
        # Assign donor
        blood_request.assign_donor()
        donor_app.last_donation_date = blood_request.required_date or datetime.now(timezone.utc).date()

        # Create DonorResponse entry
        response = DonorResponse(donor_id=user.id, request_id=blood_request.id)
        db.session.add(response)
        db.session.flush()

        # Notify creator
        notification = Notification(
            recipient_id=blood_request.user.id,
            sender_id=user.id,
            message=f"Donor {user.name or user.username} has responded to your blood request for {blood_request.patient_name}.",
            link=url_for('view_donor_info', response_id=response.id),
            is_read=False
        )
        db.session.add(notification)
        db.session.commit()
        socketio.emit('new_notification', {
            'recipient_id': notification.recipient_id,
            'message': notification.message,
            'link': notification.link,
            'notif_id': notification.id
        }, room=str(notification.recipient_id))
        return jsonify({
            "status": "success",
            "message": "You have been assigned as a donor.",
            "donors_assigned": blood_request.donors_assigned,
            "amount_needed": blood_request.amount_needed
        })

    except Exception as e:
        db.session.rollback()
        print("Error:", e)
        return jsonify({"status": "error", "message": "Something went wrong. Try again later."})


@app.route('/view_donor/<int:response_id>')
def view_donor_info(response_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    response = db.session.get(DonorResponse, response_id)
    if not response:
        return "Response not found", 404

    # Optional: ensure only request owner can view
    if session['user_id'] != response.request.user_id:
        return "Unauthorized", 403

    # Mark notification as read (if you want to do it here)
    notif_id = request.args.get('notif_id')
    if notif_id:
        notif = Notification.query.filter_by(id=notif_id, recipient_id=session['user_id']).first()
        if notif:
            notif.is_read = True
            db.session.commit()

    return render_template('donor_info.html', donor=response.donor, request=response.request)

@app.route('/resend_verification')
def resend_verification():
    if 'user_id' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))

    user = User.query.filter_by(id=session['user_id']).first()
    if user and not user.email_verified:
        send_verification_email(user.email)
        flash("Verification email sent!", "info")
    else:
        flash("Your email is already verified!", "success")

    return redirect(url_for('news_feed', username=user.username))

@app.context_processor
def inject_user():
    user = None
    if 'user_id' in session:
        user = db.session.get(User, session['user_id'])

    return dict(user=user)

@app.route('/profile/<username>', methods=['GET', 'POST'])
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    donor = DonorApplication.query.filter_by(user_id=user.id).first()
    blood_requests = BloodRequest.query.filter_by(user_id=user.id).all()
    
    divisions = Divisions.query.all()

    # Check if the session user is the same as the requested profile
    if session.get("username") == username:
        form = BloodRequestForm()
        donor_application_form = DonorApplicationForm()
        return render_template(
            'profile.html',
            user=user,
            blood_requests=blood_requests,
            divisions=divisions,
            form=form,
            donor_application_form=donor_application_form,
            donor=donor
        )
    else:
        # Show readonly version
        return render_template(
            'user_profile.html',
            user=user,
            blood_requests=blood_requests,
            donor=donor
        )
    
@app.route('/get_districts/<int:division_id>')
def get_districts(division_id):
    districts = Districts.query.filter_by(division_id=division_id).all()
    return jsonify([{"id": district.id, "name": district.name} for district in districts])

@app.route('/get_upazilas/<int:district_id>')
def get_upazilas(district_id):
    upazilas = Upazilas.query.filter_by(district_id=district_id).all()
    return jsonify([{"id": upazila.id, "name": upazila.name} for upazila in upazilas])

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({"message": "Unauthorized"}), 401

    user = User.query.filter_by(id=session['user_id']).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.json
    user.name = data.get('name', user.name)
    user.username = data.get('username', user.username)
    user.phone = data.get('phone', user.phone)
    user.address = data.get('address', user.address)
    user.blood_group = data.get('blood_group', user.blood_group)
    user.medical_history = data.get('medical_history', user.medical_history)
    user.division_id = data.get('division_id', user.division_id)
    user.district_id = data.get('district_id', user.district_id)
    user.upazila_id = data.get('upazila_id', user.upazila_id)

    db.session.commit()
    return jsonify({"message": "Profile updated successfully!"})

@app.route('/upload_profile_pic', methods=['POST'])
def upload_profile_pic():
    print("🔹 Upload Profile Pic API Called!")
    if 'user_id' not in session:
        return jsonify({"message": "Unauthorized"}), 401

    user = db.session.get(User, session['user_id'])  # ✅ Correct for SQLAlchemy 2.0
    if not user:
        return jsonify({"message": "User not found"}), 404

    if 'file' not in request.files:
        return jsonify({"message": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    if file and allowed_file(file.filename):
        # ✅ Generate a secure filename
        filename = secure_filename(f"user_{user.id}_" + file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # ✅ Save file in static/profile_pics
        file.save(file_path)

        # ✅ Store the filename in the database
        user.profile_picture = filename
        db.session.commit()

        return jsonify({"message": "Profile picture updated!", "image_url": url_for('static', filename='profile_pics/' + filename)})
    
    return jsonify({"message": "Invalid file type"}), 400


@app.route('/upload_cover_photo', methods=['POST'])
def upload_cover_photo():
    if 'user_id' not in session:
        return jsonify({"message": "Unauthorized"}), 401

    user = db.session.get(User, session['user_id'])  # ✅ Correct for SQLAlchemy 2.0

    if not user:
        return jsonify({"message": "User not found"}), 404

    if 'file' not in request.files:
        return jsonify({"message": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(f"user_{user.id}_cover_" + file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # ✅ Save the file
        file.save(file_path)

        # ✅ Store in DB
        user.cover_photo = filename
        db.session.commit()

        return jsonify({"message": "Cover photo updated!", "image_url": url_for('static', filename='profile_pics/' + filename)})
    
    return jsonify({"message": "Invalid file type"}), 400
@app.route('/new_blood_request', methods=['POST'])
def new_blood_request():
    if 'user_id' not in session:
        return jsonify({"message": "Unauthorized"}), 401

    form = BloodRequestForm()  # ✅ Do NOT pass request.form here

    if form.validate_on_submit():
        user_id = session['user_id']
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({"message": "User not found"}), 404
        # ✅ Check if essential user details are missing
        required_fields = [user.name, user.phone, user.blood_group, user.district_id, user.division_id, user.upazila_id]
        

        # ✅ Properly check for missing values
        if any(field is None or str(field).strip().lower() in ["none", "null", ""] for field in required_fields):
            flash("Please complete your profile before submitting a blood request.", "warning")
            return redirect(url_for('profile', username=user.username))  # Redirect to profile update page

        
        # ✅ Handle multiple image uploads
        image_filenames = []
        images = request.files.getlist('images')  # ✅ Fetch files properly

        if images and len(images) > 10:
            flash("You can upload a maximum of 10 images.", "danger")
            return redirect(url_for('profile', username=user.username))

        for image in images:
            if image and image.filename:  # Ensure file is not empty
                ext = os.path.splitext(image.filename)[1]  # Get file extension
                unique_filename = f"{uuid.uuid4().hex}{ext}"  # Unique filename
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                image.save(image_path)  # ✅ Save file in profile_pics folder
                image_filenames.append(unique_filename)

        image_paths_str = ",".join(image_filenames) if image_filenames else None

        new_request = BloodRequest(
            patient_name=form.patient_name.data,
            gender=form.gender.data,
            required_date=form.required_date.data,
            blood_group=form.blood_group.data,
            amount_needed=float(form.amount_needed.data),
            hospital_name=form.hospital_name.data,
            urgency_status=form.urgency_status.data,
            smoker_preference=form.smoker_preference.data,
            reason=form.reason.data,
            user_id=user_id,
            status="Open",
            location=f"{session.get('district')}, {session.get('division')}",
            images=image_paths_str,  # ✅ Store filenames in DB
            created_at=datetime.now().astimezone(timezone.utc)  # ✅ Ensure UTC timezone
        )

        db.session.add(new_request)
        db.session.commit()

        flash("Blood request posted successfully!", "success")
        return redirect(url_for('profile', username=user.username))  

    flash("Failed to post blood request. Please check your input.", "danger")

    user_id = session.get('user_id')  
    user = User.query.filter_by(id=user_id).first()

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('index'))

    donor = DonorApplication.query.filter_by(user_id=user.id).first()
    donor_application_form = DonorApplicationForm()

    return render_template(
        'profile.html', 
        user=user,  
        form=form,
        donor_application_form=donor_application_form,
        donor=donor,
        divisions=Divisions.query.all(), 
        blood_requests=BloodRequest.query.filter_by(user_id=user.id).all()
    )

@app.route('/load_past_requests')
def load_past_requests():
    if 'user_id' not in session:
        return jsonify({"message": "Unauthorized"}), 401

    offset = int(request.args.get("offset", 0))
    limit = int(request.args.get("limit", 6))

    requests = (BloodRequest.query
                .filter_by(user_id=session['user_id'])
                .order_by(BloodRequest.created_at.desc())
                .offset(offset).limit(limit).all())

    has_more = BloodRequest.query.filter_by(user_id=session['user_id']).count() > offset + limit

    return jsonify({
        "requests": [{
            "id": r.id,
            "user": {
                "id": r.user.id,
                "username": r.user.username,
                "profile_picture": r.user.profile_picture
            },
            "patient_name": r.patient_name,  # ✅ Add patient's name
            "blood_group": r.blood_group,
            "hospital_name": r.hospital_name,
            "urgency_status": r.urgency_status,
            "reason": r.reason,
            "donors_assigned": r.donors_assigned,
            "amount_needed": r.amount_needed,  # ✅ Blood bags needed
            "donors_needed": r.amount_needed,  # ✅ One donor per bag
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M"),
            "images": r.images.split(",") if r.images else [],
            "upvotes": r.upvote_count
        } for r in requests],
        "has_more": has_more
    })



def resize_image(image_path, max_size=(800, 800)):
    """Resize image to a max width & height while maintaining aspect ratio and correcting rotation."""
    img = Image.open(image_path)

    # Handle EXIF rotation (common for phone images)
    try:
        exif = img._getexif()
        if exif:
            orientation_key = next(
                (key for key, val in ExifTags.TAGS.items() if val == "Orientation"), None
            )
            if orientation_key and orientation_key in exif:
                orientation = exif[orientation_key]
                if orientation == 3:
                    img = img.rotate(180, expand=True)
                elif orientation == 6:
                    img = img.rotate(270, expand=True)
                elif orientation == 8:
                    img = img.rotate(90, expand=True)
    except Exception as e:
        print(f"EXIF rotation issue: {e}")

    img.thumbnail(max_size)  # Resize maintaining aspect ratio
    img.save(image_path, optimize=True)

@app.route("/edit_post/<int:post_id>", methods=["POST"])
def edit_post(post_id):
    post = BloodRequest.query.get_or_404(post_id)
    removed_images = request.form.get('removed_images', '[]')

    # Update text fields
    post.patient_name = request.form["patient_name"]
    post.blood_group = request.form["blood_group"]
    post.amount_needed = float(request.form["amount_needed"])
    post.hospital_name = request.form["hospital_name"]
    post.required_date = request.form["required_date"]
    post.urgency_status = request.form["urgency_status"]
    post.reason = request.form["reason"]

    # ✅ Update status based on new amount_needed vs. donors_assigned
    if post.donors_assigned >= post.amount_needed:
        post.status = "Fulfilled"
    else:
        post.status = "Open"

    # Handle removed images
    if removed_images:
        removed_images = json.loads(removed_images)
        image_list = post.images.split(',') if post.images else []
        for img in removed_images:
            if img in image_list:
                image_list.remove(img)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], img)
                if os.path.exists(image_path):
                    os.remove(image_path)
        post.images = ','.join(image_list)

    # Handle new image uploads
    if "images" in request.files:
        files = request.files.getlist("images")
        new_filenames = []
        for file in files:
            if file.filename:
                filename = f"{post_id}_{file.filename}"
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                resize_image(filepath)
                new_filenames.append(filename)

        if new_filenames:
            old = post.images.split(",") if post.images else []
            post.images = ",".join(old + new_filenames)

    db.session.commit()

    # ✅ Determine donor status text
    if post.donors_assigned == 0:
        donor_status = "No donors yet"
    elif post.donors_assigned >= post.amount_needed:
        donor_status = "All donors assigned"
    else:
        donor_status = f"{post.donors_assigned} out of {int(post.amount_needed)} Donors Assigned"

    return jsonify({
        "success": True,
        "message": "Post updated successfully",
        "updated": {
            "post_id": post.id,
            "patient_name": post.patient_name,
            "reason": post.reason,
            "blood_group": post.blood_group,
            "amount_needed": post.amount_needed,
            "hospital_name": post.hospital_name,
            "urgency_status": post.urgency_status,
            "images": post.images.split(",") if post.images else [],
            "status": post.status,
            "donors_assigned": post.donors_assigned,
            "donor_status": donor_status
        }
    })

# Helper: Get current user from session
def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)

@app.route("/api/search_donors")
def search_donors():
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "Unauthorized"}), 401

    query = request.args.get("query", "").strip()
    request_id = request.args.get("request_id")

    if not query or not request_id:
        return jsonify(results=[])

    blood_request = BloodRequest.query.get_or_404(request_id)

    eligible_donors = db.session.query(User).join(DonorApplication).filter(
        User.blood_group == blood_request.blood_group,
        DonorApplication.status == "Approved",
        ((DonorApplication.last_donation_date == None) |
         (DonorApplication.last_donation_date <= datetime.utcnow() - timedelta(days=90))),
        (
            (User.username.ilike(f"%{query}%")) |
            (User.name.ilike(f"%{query}%"))
        )
    ).limit(10).all()

    results = [{
        "id": d.id,
        "username": d.username,
        "name": d.name,
        "profile_picture": d.profile_picture or "default.png",
        "blood_group": d.blood_group,
        "last_donation_date": d.donor_application.last_donation_date.strftime("%Y-%m-%d")
            if d.donor_application and d.donor_application.last_donation_date else None
    } for d in eligible_donors]

    return jsonify(results=results)


# Route: Refer Donor
@app.route("/api/refer_donor", methods=["POST"])
def refer_donor():
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    donor_id = data.get("donor_id")
    request_id = data.get("request_id")

    donor = User.query.get_or_404(donor_id)
    blood_request = BloodRequest.query.get_or_404(request_id)
    creator = blood_request.user

    if not donor_id or not request_id:
        return jsonify({"error": "Missing donor_id or request_id"}), 400

    existing = Referral.query.filter_by(donor_id=donor_id, request_id=request_id).first()
    if existing:
        return jsonify({"message": "Already referred."})

    referral = Referral(
        donor_id=donor_id,
        request_id=request_id,
        status="Pending"
    )
    db.session.add(referral)
    db.session.commit()


    # Construct link to the request (adjust your frontend route accordingly)
    base_url = request.host_url.rstrip('/')
    request_link = f"{base_url}/request_details/{request_id}"

    # 🔔 Notify referred donor
    donor_message = f"{current_user.username} referred you for a blood request at {blood_request.hospital_name}."
    donor_notif = Notification(
        recipient_id=donor.id,
        sender_id=current_user.id,
        message=donor_message,
        link=request_link
    )
    db.session.add(donor_notif)
    

    # 🔔 Notify request creator
    creator_message = f"{current_user.username} referred {donor.username} as a donor for your blood request."
    creator_notif = Notification(
        recipient_id=creator.id,
        sender_id=current_user.id,
        message=creator_message,
        link=request_link
    )
    db.session.add(creator_notif)

    # 📧 Send email to donor
    try:
        msg = Message(
            subject="You've been referred as a blood donor",
            recipients=[donor.email],
            body=f"""Hi {donor.name or donor.username},

            You have been referred for a blood request at {blood_request.hospital_name}.

            View the request here: {request_link}

            Regards,
            Lifedrop Team"""
        )
        mail.send(msg)
    except Exception as e:
        print("Failed to send email:", e)

    db.session.commit()
    socketio.emit('new_notification', {
            'recipient_id': donor_notif.recipient_id,
            'message': donor_notif.message,
            'link': donor_notif.link,
            'notif_id': donor_notif.id
        }, room=str(donor_notif.recipient_id))
    socketio.emit('new_notification', {
            'recipient_id': creator_notif.recipient_id,
            'message': creator_notif.message,
            'link': creator_notif.link,
            'notif_id': creator_notif.id
        }, room=str(creator_notif.recipient_id))
    return jsonify({"message": "Referral successful. Notifications and email sent."})

@app.route('/api/notifications')
def get_notifications():
    user_id = session.get('user_id')
    admin_id = session.get('admin_id')

    if user_id:
        notifications = Notification.query.filter_by(
            recipient_id=user_id
        ).order_by(Notification.timestamp.desc()).limit(20).all()
    elif admin_id:
        notifications = Notification.query.filter_by(
            admin_recipient_id=admin_id
        ).order_by(Notification.timestamp.desc()).limit(20).all()
    else:
        return jsonify({"notifications": []})

    notif_list = [{
        'id': n.id,
        'message': n.message,
        'link': n.link,
        'is_read': n.is_read,
        'timestamp': n.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    } for n in notifications]

    return jsonify({"notifications": notif_list})


@app.route('/api/mark_notification_read/<int:notif_id>', methods=['POST'])
def mark_notification_read(notif_id):
    user_id = session.get('user_id')
    admin_id = session.get('admin_id')

    if not user_id and not admin_id:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    notif = Notification.query.get(notif_id)
    if not notif:
        return jsonify({"success": False, "error": "Notification not found"}), 404

    # For normal users
    if user_id and notif.recipient_id == user_id:
        notif.is_read = True
        db.session.commit()
        return jsonify({"success": True})

    # For admin users
    if admin_id and notif.admin_recipient_id == admin_id:
        notif.is_read = True
        db.session.commit()
        return jsonify({"success": True})

    return jsonify({"success": False, "error": "Forbidden"}), 403



@app.route("/request_details/<int:request_id>")
def request_details(request_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))  # or your preferred redirect

    user_id = session['user_id']
    request_obj = BloodRequest.query.get_or_404(request_id)

    referral = Referral.query.filter_by(
        donor_id=user_id, request_id=request_id
    ).first()

    return render_template("request_details.html", request_obj=request_obj, referral=referral)

@app.route("/respond_referral/<int:request_id>/<string:action>", methods=["POST"])
def respond_referral(request_id, action):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    referral = Referral.query.filter_by(
        donor_id=user_id, request_id=request_id
    ).first_or_404()

    if action not in ["accept", "reject"]:
        return "Invalid action", 400

    referral.status = "Accepted" if action == "accept" else "Rejected"
    db.session.commit()

    return redirect(url_for('request_details', request_id=request_id))

@app.route("/api/report_post", methods=["POST"])
def report_post():
    data = request.get_json()
    request_id = data.get("request_id")

    if not request_id or "user_id" not in session:
        return jsonify({"message": "Invalid request"}), 400

    reporter_id = session["user_id"]
    blood_request = BloodRequest.query.get(request_id)

    if not blood_request:
        return jsonify({"message": "Blood request not found."}), 404

    # Notify all admins
    admins = Admin.query.all()
    for admin in admins:
        notif = Notification(
            admin_recipient_id=admin.admin_id,
            sender_id=reporter_id,
            message=f"A post (ID #{request_id}) has been reported by user ID {reporter_id}.",
            link=url_for('admin_view_post', request_id=request_id),
            is_read=False
        )
        db.session.add(notif)
        db.session.flush()  # Assigns notif.id before commit

        # Emit real-time notification to the admin
        socketio.emit('new_notification', {
            'admin_recipient_id': admin.admin_id,
            'message': notif.message,
            'link': notif.link,
            'notif_id': notif.id
        }, namespace='/notifications', room=str(notif.admin_recipient_id))  # optional namespace

    db.session.commit()

    return jsonify({"message": "Reported successfully. Admins have been notified."})

@app.route("/admin/request_details/<int:request_id>")
def admin_view_post(request_id):
    if 'admin_id' not in session:
        return "Unauthorized", 403

    request_obj = BloodRequest.query.get_or_404(request_id)
    return render_template("admin_request_details.html", request_obj=request_obj)

@app.route("/admin/delete_request/<int:request_id>", methods=["POST"])
def delete_blood_request(request_id):
    if 'admin_id' not in session:
        return "Unauthorized", 403

    blood_request = BloodRequest.query.get_or_404(request_id)
    db.session.delete(blood_request)
    db.session.commit()
    flash("Blood request deleted.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route('/get_post/<int:post_id>')
def get_post(post_id):
    post = BloodRequest.query.get_or_404(post_id)
    
    return jsonify({
        "id": post.id,
        "patient_name": post.patient_name,
        "blood_group": post.blood_group,
        "amount_needed": post.amount_needed,
        "hospital_name": post.hospital_name,
        "required_date": post.required_date.strftime("%Y-%m-%dT%H:%M") if post.required_date else "",
        "urgency_status": post.urgency_status,
        "reason": post.reason,
        "images": post.images.split(",") if post.images else []
    })


@app.route('/delete_post/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    post = BloodRequest.query.get_or_404(post_id)

    if session.get("user_id") != post.user_id:
        return jsonify({"message": "Unauthorized"}), 403

    db.session.delete(post)
    db.session.commit()
    return jsonify({"message": "Post deleted successfully"})

@app.route('/mark_donor_found/<int:post_id>', methods=['POST'])
def mark_donor_found(post_id):
    post = BloodRequest.query.get_or_404(post_id)

    if session.get("user_id") != post.user_id:
        return jsonify({"message": "Unauthorized"}), 403

    data = request.get_json()
    found_count = data.get('found_count')

    if found_count is None or not isinstance(found_count, int) or found_count <= 0:
        return jsonify({"message": "Invalid donor count"}), 400

    # ❗Check if found_count exceeds remaining needed
    remaining_needed = post.donors_needed
    if found_count > remaining_needed:
        return jsonify({"message": f"Only {remaining_needed} donor(s) needed. You entered {found_count}."}), 400

    post.donors_assigned += found_count

    if post.is_fulfilled:
        post.status = "Fulfilled"

    db.session.commit()

    return jsonify({
        "message": f"{found_count} donor(s) marked as found.",
        "new_assigned": f"{post.donors_assigned} out of {post.amount_needed} Donors Assigned" if not post.is_fulfilled else "All Donors Assigned",
        "status": post.status
    })




@app.route('/upvote_request/<int:post_id>', methods=['POST'])
def upvote_request(post_id):
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session['user_id']
    blood_request = BloodRequest.query.get_or_404(post_id)

    existing_upvote = BloodRequestUpvote.query.filter_by(
        user_id=user_id, blood_request_id=post_id
    ).first()

    if existing_upvote:
        # ✅ Remove the upvote and decrement count
        db.session.delete(existing_upvote)
        blood_request.upvote_count = max(0, blood_request.upvote_count - 1)
    else:
        # ✅ Add new upvote and increment count
        new_upvote = BloodRequestUpvote(user_id=user_id, blood_request_id=post_id)
        db.session.add(new_upvote)
        blood_request.upvote_count += 1

    db.session.commit()

    return jsonify({"success": True, "upvotes": blood_request.upvote_count})


@app.route('/get_comments/<int:request_id>')
def get_comments(request_id):
    comments = Comment.query.filter_by(blood_request_id=request_id).order_by(Comment.created_at.asc()).all()

    result = []
    for comment in comments:
        replies_data = [{
            "id": reply.id,
            "text": reply.text,
            "image": reply.image if reply.image else None,
            "username": reply.user.username,
            "profile_picture": reply.user.profile_picture,
            "created_at": reply.created_at.isoformat(),
            "like_count": len(reply.commentlikereply) if hasattr(reply, 'commentlikereply') else len(reply.likes)  # fallback
        } for reply in comment.replies]

        result.append({
            "id": comment.id,
            "text": comment.text,
            "username": comment.user.username,
            "image": comment.image if comment.image else None,
            "profile_picture": comment.user.profile_picture,
            "created_at": comment.created_at.isoformat(),
            "like_count": len(comment.likes),
            "replies": replies_data
        })

    return jsonify({"comments": result})



@app.route('/add_reply/<int:comment_id>', methods=['POST'])
def add_reply(comment_id):
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    text = request.form.get('text')
    if not text:
        text = ""

    image = request.files.get('image')
    image_filename = None
    if image:
        image_filename = secure_filename(f"{uuid.uuid4().hex}_{image.filename}")
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

    reply = Reply(
        user_id=session['user_id'],
        comment_id=comment_id,
        text=text,
        image=image_filename
    )
    db.session.add(reply)
    db.session.commit()
    return jsonify({"success": True})



@app.route('/add_comment/<int:request_id>', methods=['POST'])
def add_comment(request_id):
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    text = request.form.get('text')
    if not text:
        text = ""

    image = request.files.get('image')
    image_filename = None
    if image:
        image_filename = secure_filename(f"{uuid.uuid4().hex}_{image.filename}")
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

    new_comment = Comment(
        user_id=session['user_id'],
        blood_request_id=request_id,
        text=text,
        image=image_filename
    )
    db.session.add(new_comment)
    db.session.commit()
    return jsonify({"success": True})


@app.route('/like_comment/<int:comment_id>', methods=['POST'])
def like_comment(comment_id):
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    comment = Comment.query.get_or_404(comment_id)
    user = current_user
    if user in comment.liked_by:
        comment.liked_by.remove(user)
    else:
        comment.liked_by.append(user)
    db.session.commit()
    return jsonify({'success': True, 'likes': len(comment.liked_by)})

@app.route('/delete_comment/<int:comment_id>', methods=['POST'])
def delete_comment(comment_id):
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    comment = Comment.query.get_or_404(comment_id)
    if comment.user_id != current_user.id:
        abort(403)
    db.session.delete(comment)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/become_donor', methods=['POST'])
def become_donor():
    if 'user_id' not in session:
        flash("You need to log in to apply.", "danger")
        return redirect(url_for('login'))

    user = db.session.get(User, session['user_id'])
    existing_application = DonorApplication.query.filter_by(user_id=user.id).first()

    if existing_application:
        flash("You are already a donor or your application is pending.", "info")
        return redirect(url_for('profile', username=user.username))

    form = DonorApplicationForm()

    if form.validate_on_submit():
        has_donated_before = request.form.get("has_donated_before") == "yes"
        last_donation_date = form.last_donation_date.data if has_donated_before else None

        nid_filename = secure_filename(form.nid_or_birth_certificate.data.filename)
        form.nid_or_birth_certificate.data.save(os.path.join('static/uploads/nid/', nid_filename))

        medical_images = []
        if form.medical_history_images.data:
            for file in form.medical_history_images.data:
                filename = secure_filename(file.filename)
                file.save(os.path.join('static/uploads/medical/', filename))
                medical_images.append(filename)

        new_application = DonorApplication(
            user_id=user.id,
            date_of_birth=form.date_of_birth.data,
            nid_or_birth_certificate=nid_filename,
            has_donated_before=has_donated_before,
            last_donation_date=last_donation_date,
            medical_conditions=form.medical_conditions.data,
            medical_history_images=",".join(medical_images) if medical_images else None,
            status="Pending"
        )

        db.session.add(new_application)
        db.session.commit()
        

    return jsonify({"message": "Request sent successfully"})


@app.route('/update_donor_info', methods=['POST'])
def update_donor_info():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 403

    user = db.session.get(User, session['user_id'])
    donor = DonorApplication.query.filter_by(user_id=user.id).first()

    if not donor:
        return jsonify({"error": "Donor not found"}), 404

    data = request.get_json()
    donor.last_donation_date = data.get("last_donation_date")
    donor.medical_conditions = data.get("medical_conditions")

    db.session.commit()
    return jsonify({"message": "Updated successfully"})

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login_page():
    secret_code = request.args.get("code")
    if secret_code != Config.SECRET_ADMIN_CODE:
        abort(404)

    form = AdminLoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        admin = Admin.query.filter_by(admin_username=username).first()
        if admin and admin.check_password(password):
            session["admin_id"] = admin.admin_id
            session['admin_username'] = admin.admin_username
            session["is_admin"] = True
            return redirect(url_for("admin_dashboard"))

        return render_template("admin_login.html", form=form, error="Invalid credentials")

    return render_template("admin_login.html", form=form)

@app.route("/admin_login", methods=["POST"])
def admin_login():
    
    username = request.form["username"]
    password = request.form["password"]

    admin = Admin.query.filter_by(admin_username=username).first()

    if admin and admin.check_password(password):
        session["admin_id"] = admin.admin_id  # ✅ Ensure this matches your model
        session['admin_username'] = admin.admin_username
        session["is_admin"] = True
        
        return redirect(url_for("admin_dashboard"))

    return render_template("admin_login.html", error="Invalid credentials")


@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        flash("Please log in as an admin.", "danger")
        return redirect(url_for('admin_login'))

    admin = Admin.query.filter_by(admin_id=session['admin_id']).first()
    if not admin:
        flash("Admin not found.", "danger")
        return redirect(url_for('admin_login'))

    # Fetch all admin notifications from DB
    admin_notifications = Notification.query.filter_by(
        admin_recipient_id=admin.admin_id
    ).order_by(Notification.timestamp.desc()).all()

    # Optional: store in session for popup (if needed)
    session['notifications'] = [
        {
            'id': notif.id,
            'message': notif.message,
            'link': notif.link
        } for notif in admin_notifications if not notif.is_read
    ]

    donor_applications = DonorApplication.query.all()
    pending_apps = [app for app in donor_applications if app.status == 'Pending']

    return render_template(
        "admin_dashboard.html",
        admin=admin,
        admins=Admin.query.all(),
        users=User.query.all(),
        donor_applications=donor_applications,
        blood_requests=BloodRequest.query.all(),
        notifications=session['notifications']
    )


from forms import AddAdminForm

@app.route('/admin/add_admin', methods=['GET', 'POST'])
def admin_add_admin_page():
    if 'admin_id' not in session:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('admin_login'))

    form = AddAdminForm()

    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data

        if Admin.query.filter_by(admin_username=username).first():
            flash("Username already exists!", "danger")
            return redirect(url_for('admin_dashboard'))

        new_admin = Admin(admin_username=username, admin_email=email)
        new_admin.set_password(password)  # Make sure you're hashing the password
        db.session.add(new_admin)
        db.session.commit()

        flash("New admin added successfully!", "success")
        return redirect(url_for('admin_dashboard'))

    return render_template('add_admin.html', form=form)


@app.route('/add_admin', methods=['POST'])
def add_admin():
    if 'admin_id' not in session:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('admin_login'))

    username = request.form['username']
    email = request.form['email']
    password = request.form['password']

    if Admin.query.filter_by(admin_username=username).first():
        flash("Username already exists!", "danger")
        return redirect(url_for('admin_dashboard'))

    new_admin = Admin(admin_username=username, admin_email=email, admin_password=password)
    db.session.add(new_admin)
    db.session.commit()

    flash("New admin added successfully!", "success")
    return redirect(url_for('admin_dashboard'))
@app.route('/admin/manage-users')
def manage_users():
    if 'admin_id' not in session:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('admin_login'))
    
    users = User.query.all()
    return render_template('manage_users.html', users=users)

@app.route('/admin/manage-requests')
def manage_requests():
    if 'admin_id' not in session:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('admin_login'))
    
    blood_requests = BloodRequest.query.all()
    return render_template('manage_requests.html', blood_requests=blood_requests)

@app.route('/admin/manage-donors')
def manage_donors():
    if 'admin_id' not in session:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('admin_login'))
    
    donor_applications = DonorApplication.query.all()
    return render_template('manage_donors.html', donor_applications=donor_applications)



@app.route('/remove_user/<int:user_id>', methods=['POST'])
def remove_user(user_id):
    if 'admin_id' not in session:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('admin_login'))

    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash("User removed successfully.", "success")
    else:
        flash("User not found.", "danger")

    return redirect(url_for('admin_dashboard'))
@app.route('/approve_donor/<int:application_id>', methods=['POST'])
def approve_donor(application_id):
    if 'admin_id' not in session:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('admin_login'))

    application = DonorApplication.query.get(application_id)
    if application:
        application.status = "Approved"
        db.session.commit()
        flash("Donor application approved.", "success")
    else:
        flash("Application not found.", "danger")

    return redirect(url_for('admin_dashboard'))


@app.route('/reject_donor/<int:application_id>', methods=['POST'])
def reject_donor(application_id):
    if 'admin_id' not in session:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('admin_login'))

    application = DonorApplication.query.get(application_id)
    if application:
        application.status = "Rejected"
        db.session.commit()
        flash("Donor application rejected.", "warning")
    else:
        flash("Application not found.", "danger")

    return redirect(url_for('admin_dashboard'))
@app.route('/remove_blood_request/<int:request_id>', methods=['POST'])
def remove_blood_request(request_id):
    if 'admin_id' not in session:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('admin_login'))

    blood_request = BloodRequest.query.get(request_id)
    if blood_request:
        db.session.delete(blood_request)
        db.session.commit()
        flash("Blood request removed.", "success")
    else:
        flash("Request not found.", "danger")

    return redirect(url_for('admin_dashboard'))



@app.route("/admin-logout")
def admin_logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, host="0.0.0.0", port=10000,debug=True)
