from app import db

class Slot(db.Model):
    __tablename__ = 'slots'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    date_id = db.Column(db.Integer, db.ForeignKey('dates.id'), nullable=False)
    time_slot = db.Column(db.String(20), nullable=False)  # Time slot string
    status = db.Column(db.Boolean, default=True, nullable=False)

    # Relationships
    date = db.relationship('Date', backref=db.backref('slots', lazy=True))
    doctor = db.relationship('Doctor', backref=db.backref('slots', lazy=True))
