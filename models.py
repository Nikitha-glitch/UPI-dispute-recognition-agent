from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    mpin_hash = db.Column(db.String(128), nullable=False)
    balance = db.Column(db.Float, default=10000.0) # Starting mock balance

class Transaction(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    receiver_upi = db.Column(db.String(100), nullable=False)
    merchant_id = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), default='PENDING') # PENDING, SUCCESS, FAILED
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('transactions', lazy=True))

class Dispute(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(36), db.ForeignKey('transaction.id'), nullable=False)
    merchant_txn_id = db.Column(db.String(50), nullable=True)
    receiver_txn_id = db.Column(db.String(50), nullable=True)
    dispute_status = db.Column(db.String(100), nullable=False) # 'Dispute Resolved', 'Refund Initiated'
    resolved_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    transaction = db.relationship('Transaction', backref=db.backref('dispute_history', lazy=True))
