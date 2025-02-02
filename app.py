from flask import Flask, render_template, redirect, url_for, flash, session, request, jsonify
from config import Config
from models import db, User
from forms import RegistrationForm, LoginForm
from werkzeug.security import check_password_hash, generate_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
migrate = Migrate(app, db) 

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
        
        new_user = User(
            username=form.username.data, 
            email=form.email.data, 
            password=generate_password_hash(form.password.data)
        )
        db.session.add(new_user)
        db.session.commit()

        send_verification_email(new_user.email)
        
        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)


def send_verification_email(email):
    token = generate_email_token(email)
    msg = Message("Verify Your Email", sender="your_email@example.com", recipients=[email])
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

### ✅ API: User Login (Redirect to News Feed)
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and check_password_hash(user.password, form.password.data):
            session['user_id'] = user.id
            flash("Login successful!", "success")
            return redirect(url_for('news_feed', username=user.username))  # ✅ Fixed
        
        flash("Invalid credentials", "danger")
    
    return render_template('login.html', form=form)

### ✅ API: User Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
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

    notifications = []
    
    # ✅ Add email verification notification if the user is not verified
    if not user.email_verified:
        notifications.append("Please verify your email address. <a href='/resend_verification'>Resend</a>")

    notifications += ["New blood request in your area!", "Urgent O- needed!"]

    donation_requests = [
        {"id": 1, "blood_group": "A+", "location": "Dhaka", "contact": "017xxxxxxxx", "posted_by": "John Doe"},
        {"id": 2, "blood_group": "O-", "location": "Chittagong", "contact": "018xxxxxxxx", "posted_by": "Jane Smith"},
    ]

    return render_template('news_feed.html', username=username, user=user, notifications=notifications, donation_requests=donation_requests)

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



@app.route('/profile/<username>')
def profile(username):
    # Fetch user profile based on username
    return render_template('profile.html', username=username)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
