from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, TextAreaField, FileField
from wtforms.validators import DataRequired, Email, Length

class AppointmentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField('Phone', validators=[DataRequired(), Length(max=10)])
    age = StringField('Age', validators=[DataRequired(), Length(max=10)])
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female')], validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired(), Length(max=200)])
    specialization = SelectField('Specialization', validators=[DataRequired()])
    doctor = SelectField('Doctor', validators=[DataRequired()])
    date = SelectField('Date', validators=[DataRequired()])
    time_slot = SelectField('Time Slot', validators=[DataRequired()])
    file = FileField('Upload File(*pdf)')
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Submit')
