from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    user_code = db.Column(db.String(2), unique=True, nullable=False)
    pin = db.Column(db.String(4), nullable=False)
    balance = db.Column(db.Integer, default=100)
    is_admin = db.Column(db.Integer, default=0)

class ShopItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(200))
    icon = db.Column(db.String(10), default="🍹")

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    amount = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
