from flask_wtf import FlaskForm
from wtforms import SelectField, DateField, BooleanField, SubmitField
from wtforms.validators import DataRequired

class DateForm(FlaskForm):
    doctor_id = SelectField('Doctor', choices=[], coerce=int, validators=[DataRequired()])
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    status = SelectField('Status', choices=[(1, 'Active'), (0, 'Inactive')], coerce=int, validators=[DataRequired()])
    submit = SubmitField('Add Date')
