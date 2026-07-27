import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-tajne-haslo-imprezowe'
    DATABASE = os.path.join(os.path.dirname(__file__), 'database.db')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DATABASE
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ADMIN_USERS = ['admin', 'magda']
