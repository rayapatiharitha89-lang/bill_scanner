from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Receipt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    store_name = db.Column(db.String(100))
    date = db.Column(db.String(50))
    total = db.Column(db.Float)
    raw_text = db.Column(db.Text)
    scanned_at = db.Column(db.DateTime, default=datetime.utcnow)

class ReceiptItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    receipt_id = db.Column(db.Integer, db.ForeignKey('receipt.id'))
    name = db.Column(db.String(200))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)