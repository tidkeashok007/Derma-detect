from flask import Blueprint, render_template, request,current_app, redirect, url_for, flash, jsonify,abort,send_file, send_from_directory
from flask_login import login_required, current_user
from app.models.user import User, Role, Status  # Adjust import according to your project structure
from app.models.case_report import CaseReport
from app.forms.add_case_report_form import CaseReportForm
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.date import Date
from app.models.slot import Slot
from sqlalchemy import or_
from app import db, mail
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user
import os
from datetime import datetime


doctor_bp = Blueprint('doctor', __name__)

# Doctor dashboard route===========================
@doctor_bp.route('/doctor/doctor-dashboard', endpoint='doctor-dashboard')
@login_required
def doctor_dashboard():
    if current_user.role != Role.DOCTOR:
        flash('You do not have permission to view this page.', 'warning')
        return redirect(url_for('main.index'))

    user = User.query.get(current_user.id)
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()  
    dates = Date.query.filter_by(doctor_id=doctor.id).all()  
    slots = Slot.query.filter_by(doctor_id=doctor.id).all()  

    if user is None or doctor is None:
        flash('User or Doctor details not found.', 'warning')
        return redirect(url_for('main.index'))  

    return render_template('doctor/doctor_dashboard.html', active_page='doctor-dashboard',
                           user=user, doctor=doctor, dates=dates, slots=slots)


# doctor appointment page==============================
@doctor_bp.route('/doctor/doctor-appointments', endpoint='doctor-appointments')
@login_required
def doctor_appointments():
    if current_user.role != Role.DOCTOR:
        flash('You do not have permission to view this page.', 'warning')
        return redirect(url_for('main.index'))
    # Fetch appointments only for the current doctor
    appointments = Appointment.query.filter_by(doctor_id=current_user.doctor_profile.id).all()
    return render_template('doctor/doctor_appointments.html', active_page='doctor-appointments',appointments=appointments)


# Doctor case report page===========================
@doctor_bp.route('/doctor/patient-details', endpoint='patient-details')
@login_required
def patient_details():
    if current_user.role != Role.DOCTOR:
        flash('You do not have permission to view this page.', 'warning')
        return redirect(url_for('main.index'))
    
    # Capture the search query
    query = request.args.get('query', '')

    # Exclude roles and statuses
    excluded_roles = [Role.DOCTOR, Role.ADMIN]
    excluded_status = 'deactivate'

    # Base query to fetch users excluding certain roles and statuses
    users_query = User.query.filter(
        User.id != current_user.id,
        User.role.notin_(excluded_roles),
        User.status != excluded_status
    )

    # If there's a search query, filter the users based on it
    if query:
        search = f"%{query}%"
        users_query = users_query.filter(
            or_(
                User.id.like(search),
                User.name.like(search),
                User.email.like(search),
                User.phone.like(search)
            )
        )

    # Execute the query
    users = users_query.all()

    return render_template('doctor/doctor_patient_details.html', active_page='patient-details', user=current_user, users=users)


# for see case Reports====================
@doctor_bp.route('/doctor/see-case-reports/<int:user_id>', methods=['GET'])
@login_required
def see_case_reports(user_id):
    if current_user.role != Role.DOCTOR:
        flash('You do not have permission to view this page.', 'warning')
        return redirect(url_for('main.index'))
    user = User.query.get_or_404(user_id)

    appointments = Appointment.query.filter_by(user_id=user_id).all()
    
    return render_template('doctor/doctor_see_case_reports.html', active_page='see-case-reports',user=user, appointments=appointments)


@doctor_bp.route('/uploads/case_reports/<filename>')
def uploaded_file(filename):
    PROFILE_FOLDER = os.path.join(current_app.root_path, 'static', 'uploads', 'case_reports')
    return send_from_directory(PROFILE_FOLDER, filename)

# ================================================================================
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@doctor_bp.route('/doctor/add-case-reports', endpoint="add-case-reports", methods=['GET', 'POST'])
@login_required
def add_case_reports():
    if current_user.role != Role.DOCTOR:
        flash('You do not have permission to view this page.', 'danger')
        return redirect(url_for('main.index'))

    form = CaseReportForm()
    form.doctor_id.data = current_user.id  # Set doctor_id to the current user's ID

    # Populate form choices for the dropdowns
    form.user_id.choices = [(user.id, user.name) for user in User.query.filter_by(role='user').all()]
    # Filter out appointment IDs that already have a case report
    existing_appointments = [cr.appointment_id for cr in CaseReport.query.with_entities(CaseReport.appointment_id).all()]
    available_appointments = Appointment.query.filter_by(user_id=form.user_id.data).filter(Appointment.id.notin_(existing_appointments)).all()

    form.appointment_id.choices = [(appointment.id, f"Appointment ID: {appointment.id}") for appointment in available_appointments]

    if form.validate_on_submit():
        user_id = form.user_id.data
        appointment_id = form.appointment_id.data
        report_description = form.report_description.data
        report_pdf = form.report_pdf.data

        # Save the uploaded PDF file
        if report_pdf and allowed_file(report_pdf.filename):
            filename = secure_filename(report_pdf.filename)
            PROFILE_FOLDER = os.path.join(current_app.root_path, 'static', 'uploads', 'case_reports')

            if not os.path.exists(PROFILE_FOLDER):
                os.makedirs(PROFILE_FOLDER)

            file_path = os.path.join(PROFILE_FOLDER, filename)
            report_pdf.save(file_path)
        else:
            flash('Invalid file format. Only PDF files are allowed.', 'danger')
            return redirect(url_for('doctor.add-case-reports'))

        # Create and save CaseReport
        case_report = CaseReport(
            user_id=user_id,
            appointment_id=appointment_id,
            doctor_id=current_user.id,
            report_description=report_description,
            report_pdf=filename
        )
        db.session.add(case_report)
        db.session.commit()
        flash('Case report added successfully.', 'success')
        return redirect(url_for('doctor.patient-details'))

    return render_template('doctor/doctor_add_case_reports.html',active_page='add-case-reports', form=form)

@doctor_bp.route('/doctor/get-users', methods=['GET'])
@login_required
def get_users():
    if current_user.role != Role.DOCTOR:
        return jsonify({'error': 'Unauthorized'}), 403
    return jsonify()

@doctor_bp.route('/doctor/appointments/<int:user_id>', methods=['GET'])
@login_required
def get_appointments(user_id):
    if current_user.role != Role.DOCTOR:
        return jsonify({'error': 'Unauthorized'}), 403

    # Filter out appointment IDs that already have a case report
    existing_appointments = [cr.appointment_id for cr in CaseReport.query.with_entities(CaseReport.appointment_id).all()]
    available_appointments = Appointment.query.filter_by(user_id=user_id).filter(Appointment.id.notin_(existing_appointments)).all()

    appointment_list = [(appointment.id, f"Appointment ID: {appointment.id}") for appointment in available_appointments]
    return jsonify(appointment_list)

