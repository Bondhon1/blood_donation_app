from flask import Flask, render_template, redirect, url_for, flash, session, request, jsonify, abort
from config import Config
from models import db, User, BloodRequest, Admin, Divisions, Districts, Upazilas, Comment, BloodRequestUpvote, DonorApplication
from forms import RegistrationForm, LoginForm, BloodRequestForm, DonorApplicationForm
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
from datetime import datetime, timezone, UTC
from flask_login import current_user, login_required
import uuid


UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static/profile_pics')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config.from_object(Config)
db.init_app(app)
migrate = Migrate(app, db) 



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

@app.route('/news_feed/<username>')
def news_feed(username):
    if 'user_id' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))

    user = User.query.filter_by(id=session['user_id']).first()
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('login'))

    # ✅ Reset notifications for a fresh session
    if 'notifications' not in session:
        session['notifications'] = []

    notifications = session['notifications']

    # ✅ Remove email verification notification if already verified
    verification_message = "Please verify your email address. <a href='/resend_verification'>Resend</a>"
    if user.email_verified and verification_message in notifications:
        notifications.remove(verification_message)

    # ✅ Add email verification notification only if needed
    if not user.email_verified and verification_message not in notifications:
        notifications.append(verification_message)

    # ✅ Add new notifications (no duplicates)
    new_notifications = ["New blood request in your area!", "Urgent O- needed!"]
    for notif in new_notifications:
        if notif not in notifications:
            notifications.append(notif)

    # ✅ Store only unique notifications in session
    session['notifications'] = list(set(notifications))

    donation_requests = [
        {"id": 1, "blood_group": "A+", "location": "Dhaka", "contact": "017xxxxxxxx", "posted_by": "John Doe"},
        {"id": 2, "blood_group": "O-", "location": "Chittagong", "contact": "018xxxxxxxx", "posted_by": "Jane Smith"},
    ]

    return render_template('news_feed.html', username=username, user=user, donation_requests=donation_requests)

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
    form = BloodRequestForm()
    donor_application_form = DonorApplicationForm()

    return render_template('profile.html', user=user, blood_requests=blood_requests, divisions=divisions, form=form, donor_application_form=donor_application_form, donor=donor)

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

    return render_template(
        'profile.html', 
        user=user,  
        form=form,  
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
            "amount_needed": r.amount_needed,  # ✅ Blood bags needed
            "donors_needed": r.amount_needed,  # ✅ One donor per bag
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M"),
            "images": r.images.split(",") if r.images else [],
            "upvotes": r.upvote_count
        } for r in requests],
        "has_more": has_more
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
    comments = Comment.query.filter_by(blood_request_id=request_id).order_by(Comment.created_at.desc()).all()
    return jsonify({"comments": [{"username": c.user.username, "text": c.text} for c in comments]})

@app.route('/add_comment/<int:request_id>', methods=['POST'])
def add_comment(request_id):
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    data = request.json
    if not data.get("text"):
        return jsonify({"success": False, "error": "Empty comment"}), 400

    new_comment = Comment(user_id=session['user_id'], blood_request_id=request_id, text=data["text"])
    db.session.add(new_comment)
    db.session.commit()

    return jsonify({"success": True})
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




@app.route("/admin_login")
def admin_login_page():
    secret_code = request.args.get("code")

    # Check if the provided code matches the secret one
    if secret_code != Config.SECRET_ADMIN_CODE:
        abort(404)  # Show a 404 error page

    return render_template("admin_login.html")

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

    admin = Admin.query.filter_by(admin_id=session['admin_id']).first()  # ✅ Corrected

    if not admin:
        flash("Admin not found.", "danger")
        return redirect(url_for('admin_login'))

    return render_template("admin_dashboard.html", admin=admin)



@app.route("/admin-logout")
def admin_logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
