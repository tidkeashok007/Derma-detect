from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from sqlalchemy import Column, String, Integer, Enum
from enum import Enum as PyEnum

class Role(PyEnum):
    USER = 'user'
    DOCTOR = 'doctor'
    ADMIN = 'admin'

class Status(PyEnum):
    INACTIVE = 0
    ACTIVE = 1

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    profile_image = db.Column(db.String(256), nullable=True)  # Path to profile image
    name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(256), nullable=False)
    role = Column(Enum(Role), default=Role.USER)  # Dropdown options: 'user', 'doctor', 'admin'
    status = Column(Enum(Status), nullable=False, default=Status.ACTIVE)  # Dropdown options: 0, 1

  
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def get_reset_token(self, expires_sec=300):
        s = Serializer(current_app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)
