from app import db

class Doctor(db.Model):
    __tablename__ = 'doctors'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign key reference to User
    name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(15), nullable=True)
    dob = db.Column(db.Date, nullable=True)
    specialization = db.Column(db.String(50), nullable=True)
    qualification = db.Column(db.String(50), nullable=True)
    address = db.Column(db.Text, nullable=True)
    
    # Relationship to User
    user = db.relationship('User', backref=db.backref('doctor_profile', uselist=False))
    

    def __repr__(self):
        return f'<Doctor {self.name,self}>'
