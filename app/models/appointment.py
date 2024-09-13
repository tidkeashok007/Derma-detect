from app import db

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(10), nullable=False)
    age = db.Column(db.String(10), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    date_id = db.Column(db.Integer, db.ForeignKey('dates.id'), nullable=False)
    time_slot_id = db.Column(db.Integer, db.ForeignKey('slots.id'), nullable=False)
    file = db.Column(db.String(100))
    message = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Ensure this line exists

    doctor = db.relationship('Doctor', backref=db.backref('appointments', lazy=True))
    date = db.relationship('Date', backref=db.backref('appointments', lazy=True))
    time_slot = db.relationship('Slot', backref=db.backref('appointments', lazy=True))
    user = db.relationship('User', backref='appointments')
    