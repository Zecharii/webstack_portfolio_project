import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'supersecretkey')
    SQLALCHEMY_DATABASE_URI = os.getenv('JAWSDB_URL', 'mysql://root:Admin17017!@localhost/github_use')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
