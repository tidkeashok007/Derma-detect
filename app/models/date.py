from app import db

class Date(db.Model):
    __tablename__ = 'dates'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)  # Foreign key reference to Doctors
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Boolean, default=True, nullable=False)  # Status field to indicate availability

    doctor = db.relationship('Doctor', backref=db.backref('dates', lazy=True))
