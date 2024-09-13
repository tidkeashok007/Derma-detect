from app import db
from datetime import datetime

class CaseReport(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    report_pdf = db.Column(db.String(256), nullable=False)
    report_description = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.user_id'), nullable=False)

    user = db.relationship('User', backref=db.backref('case_reports', lazy=True))
    appointment = db.relationship('Appointment', backref=db.backref('case_reports', lazy=True))
    doctor = db.relationship('Doctor', backref=db.backref('case_reports', lazy=True))
