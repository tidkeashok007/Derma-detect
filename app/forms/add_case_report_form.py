from flask_wtf import FlaskForm
from wtforms import SelectField, TextAreaField, FileField, SubmitField, IntegerField
from wtforms.validators import DataRequired
from flask_wtf.file import FileAllowed

class CaseReportForm(FlaskForm):
    user_id = SelectField('Patient ID', coerce=int, validators=[DataRequired()])
    appointment_id = SelectField('Appointment ID', coerce=int, validators=[DataRequired()])
    report_description = TextAreaField('Report Description', validators=[DataRequired()])
    report_pdf = FileField('Upload Report PDF', validators=[DataRequired(), FileAllowed(['pdf'], 'PDF files only!')])
    doctor_id = IntegerField('Doctor ID', validators=[DataRequired()])  # Automatically filled based on the logged-in doctor
    submit = SubmitField('Submit Case Report')
