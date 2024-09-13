from flask_wtf import FlaskForm
from wtforms import SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired

class SlotForm(FlaskForm):
    date_id = SelectField('Date', coerce=int, validators=[DataRequired()])
    doctor_id = SelectField('Doctor', coerce=int, validators=[DataRequired()])
    
    # Checkbox fields for time slots
    slot_9_00_9_30 = BooleanField('9:00 AM to 9:30 AM')
    slot_9_30_10_00 = BooleanField('9:30 AM to 10:00 AM')
    slot_10_00_10_30 = BooleanField('10:00 AM to 10:30 AM')
    slot_10_30_11_00 = BooleanField('10:30 AM to 11:00 AM')
    slot_11_00_11_30 = BooleanField('11:00 AM to 11:30 AM')
    slot_11_30_12_00 = BooleanField('11:30 AM to 12:00 PM')
    slot_12_00_12_30 = BooleanField('12:00 PM to 12:30 PM')
    slot_12_30_1_00 = BooleanField('12:30 PM to 01:00 PM')
    slot_1_00_1_30 = BooleanField('01:00 PM to 01:30 PM')
    slot_1_30_2_00 = BooleanField('01:30 PM to 02:00 PM')
    slot_2_00_2_30 = BooleanField('02:00 PM to 02:30 PM')
    slot_2_30_3_00 = BooleanField('02:30 PM to 03:00 PM')
    slot_3_00_3_30 = BooleanField('03:00 PM to 03:30 PM')
    slot_3_30_4_00 = BooleanField('03:30 PM to 04:00 PM')
    slot_4_00_4_30 = BooleanField('04:00 PM to 04:30 PM')
    slot_4_30_5_00 = BooleanField('04:30 PM to 05:00 PM')
    
    submit = SubmitField('Add Slots')
