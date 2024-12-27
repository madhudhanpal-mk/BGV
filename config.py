import os

class Config:
    SECRET_KEY = os.urandom(24)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///bgv.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
