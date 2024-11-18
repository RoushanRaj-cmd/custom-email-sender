from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class ScheduledEmail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    scheduled_time = db.Column(db.DateTime, nullable=False)
    company_name = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, queued, sent, failed

    def __repr__(self):
        return f'<ScheduledEmail {self.email} at {self.scheduled_time}>'