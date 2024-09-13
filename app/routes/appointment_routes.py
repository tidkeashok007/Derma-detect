from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, current_app
from flask_login import login_required, current_user
from app import db, mail
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.date import Date
from app.models.slot import Slot
from app.models.user import User
from app.forms.appointment_form import AppointmentForm
from werkzeug.utils import secure_filename
from flask_mail import Message
import os

appointment_bp = Blueprint('appointment', __name__)

# File upload configuration
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@appointment_bp.route('/appointment', methods=['GET', 'POST'])
@login_required
def appointment():
    form = AppointmentForm()

    # Populate specialization dropdown
    form.specialization.choices = [(spec.specialization, spec.specialization) for spec in db.session.query(Doctor.specialization).distinct()]

    # Set doctor choices dynamically based on selected specialization
    if form.specialization.data:
        form.doctor.choices = [(doctor.id, doctor.name) for doctor in Doctor.query.filter_by(specialization=form.specialization.data).all()]
    else:
        form.doctor.choices = []

    # Set date and time slot choices dynamically
    if form.doctor.data:
        form.date.choices = [(date.id, date.date.strftime('%Y-%m-%d')) for date in Date.query.filter_by(doctor_id=form.doctor.data).all()]
    else:
        form.date.choices = []

    if form.date.data:
        form.time_slot.choices = [(slot.id, slot.time_slot) for slot in Slot.query.filter_by(date_id=form.date.data,status=1).all()]
    else:
        form.time_slot.choices = []

    if form.validate_on_submit():
        file = request.files.get('file')
        filename = None

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Use current_app to get the upload folder
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'appointments')
            file_path = os.path.join(upload_folder, filename)

            # Ensure the upload folder exists
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            file.save(file_path)

        appointment = Appointment(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            age=form.age.data,
            gender=form.gender.data,
            address=form.address.data,
            specialization=form.specialization.data,
            doctor_id=form.doctor.data,
            date_id=form.date.data,
            time_slot_id=form.time_slot.data,
            file=filename,
            message=form.message.data,
            user_id=current_user.id
        )
        db.session.add(appointment)

        # Set the selected slot's status to 0 to make it unavailable
        slot = Slot.query.get(form.time_slot.data)
        if slot:
            slot.status = 0
            db.session.commit()

            # Check if all slots for the selected date are booked (status=0)
            all_slots_booked = Slot.query.filter_by(date_id=form.date.data, status=1).count() == 0
            if all_slots_booked:
                date = Date.query.get(form.date.data)
                if date:
                    date.status = 0
                    db.session.commit()

                     # Send email to the user
        user_msg = Message('Appointment Confirmation', sender=current_app.config['MAIL_USERNAME'], recipients=[form.email.data])
        user_msg.body = f"""Dear {form.name.data},

Thank you for booking an appointment with us.

Here are the details of your appointment:
- Name: {form.name.data}
- Email: {form.email.data}
- Phone: {form.phone.data}
- Age: {form.age.data}
- Gender: {form.gender.data}
- Address: {form.address.data}
- Specialization: {form.specialization.data}
- Doctor: {form.doctor.data}
- Date: {form.date.data}
- Time Slot: {form.time_slot.data}
- Message: {form.message.data}

Best regards,
The Derma Detect Team"""

        if filename:
            with open(file_path, 'rb') as fp:
                user_msg.attach(filename, 'application/pdf', fp.read())

        mail.send(user_msg)

        # Send email to the admin
        admin_msg = Message('New Appointment Request', sender=current_app.config['MAIL_USERNAME'], recipients=['learnwithtidke@gmail.com'])  # Replace with admin email
        admin_msg.body = f"""New appointment request received:

- Name: {form.name.data}
- Email: {form.email.data}
- Phone: {form.phone.data}
- Age: {form.age.data}
- Gender: {form.gender.data}
- Address: {form.address.data}
- Specialization: {form.specialization.data}
- Doctor: {form.doctor.data}
- Date: {form.date.data}
- Time Slot: {form.time_slot.data}
- Message: {form.message.data}
- User ID: {current_user.id}
"""


        
        if filename:
            with open(file_path, 'rb') as fp:
                admin_msg.attach(filename, 'application/pdf', fp.read())

        mail.send(admin_msg)

        flash('Appointment request sent successfully!', 'success')
        return redirect(url_for('main.index'))
    # Retrieve all appointments for the current user
    user_appointments = Appointment.query.filter_by(user_id=current_user.id).all()
    return render_template('pages/appointment.html', form=form, active_page='appointment',user_appointments=user_appointments)


# it will show this file in where we want to see
@appointment_bp.route('/uploads/<filename>')
def uploaded_file(filename):
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'appointments')
    return send_from_directory(upload_folder, filename)

@appointment_bp.route('/get_doctors/<specialization>', methods=['GET'])
def get_doctors(specialization):
    doctors = Doctor.query.filter_by(specialization=specialization).all()
    doctor_list = [{'id': doctor.id, 'name': doctor.name} for doctor in doctors]
    return jsonify(doctor_list)

@appointment_bp.route('/get_dates/<doctor_id>', methods=['GET'])
def get_dates(doctor_id):
    dates = Date.query.filter_by(doctor_id=doctor_id,status=1).all()
    date_list = [{'id': date.id, 'date': date.date.strftime('%Y-%m-%d')} for date in dates]
    return jsonify(date_list)

@appointment_bp.route('/get_time_slots/<date_id>', methods=['GET'])
def get_time_slots(date_id):
    slots = Slot.query.filter_by(date_id=date_id,status=1).all()
    slot_list = [{'id': slot.id, 'time_slot': slot.time_slot} for slot in slots]
    return jsonify(slot_list)


# @appointment_bp.route('/uploads/<filename>', endpoint='uploaded_file')
# def uploaded_file(filename):
#     return send_from_directory(current_app.config['APPOINTMENT_FOLDER'], filename)
