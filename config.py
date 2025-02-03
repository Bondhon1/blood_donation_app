
class Config:
    SECRET_KEY = 'your_secret_key'
    SQLALCHEMY_DATABASE_URI = 'contact me for the database link'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = 'contact me for the email'
    MAIL_PASSWORD = 'contact me'  # Use App Password, not your Gmail password
    MAIL_DEFAULT_SENDER = ('Lifedrop - Blood donation system', MAIL_USERNAME)