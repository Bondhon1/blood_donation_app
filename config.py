
import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SECRET_ADMIN_CODE = os.environ.get("SECRET_ADMIN_CODE")

    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,
        "pool_recycle": 1800,
        "pool_pre_ping": True,
        "connect_args": {
            "options": "-c statement_timeout=5000"
        }
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = (os.environ.get("MAIL_DEFAULT_SENDER"), MAIL_USERNAME)
