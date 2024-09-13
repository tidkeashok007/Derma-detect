from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, TelField, DateField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email

class AddDoctorForm(FlaskForm):
    user_id = SelectField('User ID', choices=[], coerce=int, validators=[DataRequired()])  # Dynamically populated from User table
    name = StringField('Name', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    phone = TelField('Phone', validators=[DataRequired()])
    dob = DateField('Date of Birth', format='%Y-%m-%d', validators=[DataRequired()])
    specialization = SelectField('Specialization', choices=[
        ('Dermatopathologist ', 'Dermatopathologist'),
        ('Dermatologist', 'Dermatologist'),
        ('Oncologist ', 'Oncologist'),
        ('Mohs Surgeon', 'Mohs Surgeon')
    ], validators=[DataRequired()])
    qualification = StringField('Qualification', validators=[DataRequired()])
    address = TextAreaField('Address', validators=[DataRequired()])
    submit = SubmitField('Save Doctor')
