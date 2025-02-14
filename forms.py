from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField, IntegerField, TextAreaField, FileField, MultipleFileField, FloatField
from wtforms.validators import DataRequired, Email, EqualTo, Length

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
class BloodRequestForm(FlaskForm):
    patient_name = StringField("Patient's Name", validators=[DataRequired(), Length(min=2, max=100)])
    gender = SelectField("Gender", choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], validators=[DataRequired()])
    required_date = DateField("Required Date", validators=[DataRequired()], format='%Y-%m-%d')
    blood_group = SelectField("Blood Group", choices=[
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-')
    ], validators=[DataRequired()])
    amount_needed = FloatField("Amount Needed (in bags)", validators=[DataRequired()])  # ✅ Changed from IntegerField
    hospital_name = StringField("Hospital Name", validators=[DataRequired(), Length(min=2, max=255)])
    urgency_status = SelectField("Urgency Status", choices=[("Normal", "Normal"), ("Urgent", "Urgent"), ("Critical", "Critical")], validators=[DataRequired()])
    reason = TextAreaField("Reason for Request", validators=[DataRequired(), Length(min=5, max=500)])
    images = MultipleFileField("Upload Supporting Documents (Optional)")  # ✅ Now supports multiple images
