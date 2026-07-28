import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'motyl-secret-key-change-on-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Lista nicków z automatycznym uprawnieniem Admina (wpisane dokładnie tak, jak w logowaniu)
    ADMIN_USERS = ['@Ptychu99', 'M0tylisk0', 'admin', 'magda']
