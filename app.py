from flask import Flask, render_template, redirect, url_for, flash, session, request, jsonify
from config import Config
from models import db, User
from forms import RegistrationForm, LoginForm
from werkzeug.security import check_password_hash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter((User.username == form.username.data) | (User.email == form.email.data)).first()
        
        if existing_user:
            if existing_user.username == form.username.data:
                flash("Username is already taken.", "danger")
            elif existing_user.email == form.email.data:
                flash("Email is already in use.", "danger")
            return redirect(url_for('register'))
        
        new_user = User(username=form.username.data, email=form.email.data, password=form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)


@app.route('/check_user', methods=['POST'])
def check_user():
    data = request.json
    username = data.get("username")
    email = data.get("email")

    user_exists = User.query.filter((User.username == username) | (User.email == email)).first()
    
    response = {"exists": False}

    if user_exists:
        response["exists"] = True
        if user_exists.username == username:
            response["message"] = "Username is already taken."
        elif user_exists.email == email:
            response["message"] = "Email is already in use."

    return jsonify(response)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            session['user_id'] = user.id
            flash("Login successful!", "success")
            return redirect(url_for('home'))
        flash("Invalid credentials", "danger")
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Logged out successfully!", "info")
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
