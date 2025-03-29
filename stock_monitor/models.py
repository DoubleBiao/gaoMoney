from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class StockScan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    symbol = db.Column(db.String(10), nullable=False)
    name = db.Column(db.String(100))
    price = db.Column(db.Float)
    volume = db.Column(db.Integer)
    market_cap = db.Column(db.Float)
    volume_ratio = db.Column(db.Float)  # Current volume / Average volume

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.strftime('%Y-%m-%d %H:%M:%S'),
            'symbol': self.symbol,
            'name': self.name,
            'price': self.price,
            'volume': self.volume,
            'market_cap': self.market_cap,
            'volume_ratio': self.volume_ratio
        }

class MarketStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_open = db.Column(db.Boolean, nullable=False)
    next_open_date = db.Column(db.DateTime)
    message = db.Column(db.String(200))

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.strftime('%Y-%m-%d %H:%M:%S'),
            'is_open': self.is_open,
            'next_open_date': self.next_open_date.strftime('%Y-%m-%d') if self.next_open_date else None,
            'message': self.message
        } 