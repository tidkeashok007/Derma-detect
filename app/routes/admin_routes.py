from flask import Blueprint, render_template,abort, jsonify, request, redirect, url_for, flash, send_from_directory, current_app
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash  # For hashing passwords
from app.models.user import User
from app.models.contact import Contact
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.user import User, Role, Status  # Adjust import according to your project structure
from app.forms.add_doctor_form import AddDoctorForm
from app.forms.register_form import RegisterForm
from app.forms.add_slots_form import SlotForm
from app.forms.add_dates_form import DateForm
from app.models.date import Date
from app.models.slot import Slot
from app.models.doctor import Doctor  # Update with actual model import
from flask_mail import Mail, Message  # For sending emails
from app import db, mail
import os
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
from flask_wtf.csrf import validate_csrf
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import or_



admin_bp = Blueprint('admin', __name__)

# Doctor profile image configuration
DOCTOR_PROFILE_FOLDER = os.getenv('DOCTOR_PROFILE_FOLDER', 'static/doctorProfiles')
ALLOWED_PROFILE_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename, allowed_extensions):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


# ================== Admin Dashboard =========================
@admin_bp.route('/admin-dashboard', endpoint='admin-dashboard')
@login_required
def admin_dashboard():
    if current_user.role.value != 'admin':
        flash('You do not have permission to view this page.', 'warning')
        return redirect(url_for('main.index'))  # Redirect to index if not an admin
    
    contacts = Contact.query.all()
    appointments = Appointment.query.all()
    users = User.query.all()
    doctors = Doctor.query.all()
    
    # Calculate counts
    total_users = len(users)
    total_doctors = len([user for user in users if user.role.value == 'doctor'])
    total_patients = len([user for user in users if user.role.value == 'patient'])
    total_appointments = len(appointments)
    total_contacts = len(contacts)
    
    return render_template('admin/admin_dashboard.html',
                           active_page='admin-dashboard',
                           contacts=contacts,
                           appointments=appointments,
                           users=users,
                           doctors=doctors,
                           admins=[user for user in users if user.role.value == 'admin'],
                           total_users=total_users,
                           total_doctors=total_doctors,
                           total_patients=total_patients,
                           total_appointments=total_appointments,
                           total_contacts=total_contacts)


# =========================================Admin Doctors================================
@admin_bp.route('/admin-doctors-dash', endpoint='admin-doctors-dash')
@login_required
def admin_doctors_dash():
    if current_user.role.value != 'admin':
        flash('You do not have permission to view this page.', 'warning')
        return redirect(url_for('main.index'))  # Redirect to index if not an admin
    
    contacts = Contact.query.all() 
    appointments = Appointment.query.all() 
    doctors = Doctor.query.all() 
    users = User.query.all()  
    
    # Filter users to include only those with the role DOCTOR
    users = [user for user in users if user.role == Role.DOCTOR]
    schedules = Slot.query.join(Date).filter(Date.doctor_id.in_([doctor.id for doctor in doctors])).all()
    
    # for right corner profile icon
    users = User.query.all()

    # Filter users to include only those with the role DOCTOR but without a doctor profile
    incomplete_doctors = [user for user in users if user.role == Role.DOCTOR and user.doctor_profile is None]

    # Calculate counts
    total_contacts = len([contact for contact in contacts ])
    total_appointments = len([appointment for appointment in appointments ])
    total_doctors = len([user for user in users if user.role == Role.DOCTOR])
    total_active_doctors = len([user for user in users if user.role == Role.DOCTOR and user.status == Status.ACTIVE])
    total_inactive_doctors = len([user for user in users if user.role == Role.DOCTOR and user.status == Status.INACTIVE])

    
    return render_template('admin/admin_doctors_dash.html',
                           active_page='admin-doctors-dash',
                           contacts=contacts,
                           appointments=appointments,
                           users=users,
                           doctors=doctors,
                           schedules=schedules,
                           total_contacts=total_contacts,
                           total_appointments=total_appointments,
                           admins=[user for user in users if user.role.value == 'admin'],
                           total_doctors=total_doctors,
                           incomplete_doctors=incomplete_doctors,
                           total_active_doctors=total_active_doctors,
                           total_inactive_doctors=total_inactive_doctors)


# status convertion active to inactive, for Doctors Registered with Incomplete Profiles.
@admin_bp.route('/toggle_status_doctors/<int:user_id>',endpoint='toggle_status_doctors')
@login_required
def toggle_status(user_id):
    if current_user.role.value != 'admin':
        flash('You do not have permission to perform this action.', 'warning')
        return redirect(url_for('main.index'))  # Redirect to index if not an admin
    
    user = User.query.get_or_404(user_id)
    
    # Toggle between ACTIVE and INACTIVE
    if user.status == Status.ACTIVE:
        user.status = Status.INACTIVE
    else:
        user.status = Status.ACTIVE
    
    db.session.commit()
    flash(f"Status for {user.name} has been updated to {user.status.name}.", "success")
    return redirect(url_for('admin.admin-doctors-dash'))  # Redirect back to the doctors dashboard


# add doctor route
@admin_bp.route('/add-doctor', methods=['GET', 'POST'], endpoint='add-doctor')
@login_required
def add_doctor():
    if current_user.role != Role.ADMIN:
        flash('You do not have permission to view this page.', 'warning')
        return redirect(url_for('main.index'))

    form = AddDoctorForm()

    # Load doctor choices if not already loaded
    if not form.user_id.choices:
        # Get IDs of users who are already in the Doctor table
        existing_doctor_ids = {doctor.user_id for doctor in Doctor.query.all()}

        form.user_id.choices = [
            (user.id, f'{user.name} (User ID: {user.id})')
            for user in User.query
                .filter_by(role=Role.DOCTOR, status=Status.ACTIVE)
                .filter(User.id != current_user.id)  # Exclude the current user
                .filter(User.id.notin_(existing_doctor_ids))  # Exclude users already in Doctor table
                .all()
        ]

    if form.validate_on_submit():
        try:
            # Check if a doctor with the same ID already exists
            existing_doctor = Doctor.query.filter_by(user_id=form.user_id.data).first()
            if existing_doctor:
                # Update existing doctor details
                existing_doctor.name = form.name.data
                existing_doctor.email = form.email.data
                existing_doctor.phone = form.phone.data
                existing_doctor.dob = form.dob.data
                existing_doctor.specialization = form.specialization.data
                existing_doctor.qualification = form.qualification.data
                existing_doctor.address = form.address.data
            else:
                # Create a new doctor object
                new_doctor = Doctor(
                    user_id=form.user_id.data,  # Corrected to `form.user_id.data`
                    name=form.name.data,
                    email=form.email.data,
                    phone=form.phone.data,
                    dob=form.dob.data,
                    specialization=form.specialization.data,
                    qualification=form.qualification.data,
                    address=form.address.data
                )
                db.session.add(new_doctor)

            db.session.commit()
            flash('Doctor saved successfully!', 'success')
            return redirect(url_for('admin.admin-doctors-dash'))
        except Exception as e:
            db.session.rollback()  # Rollback in case of an error
            flash(f'Error saving doctor: {str(e)}', 'warning')
            print(f'Error saving doctor: {str(e)}')  # Print error for debugging
    users = User.query.all()
    admins = [user for user in users if user.role == Role.ADMIN]
    return render_template('admin/add_doctor.html', form=form,users=users,admins=admins)



# for fatchin users details in add-doctor-page like name, email, phone
@admin_bp.route('/get-user-details/<int:user_id>')
def get_user_details(user_id):
    if current_user.role != Role.ADMIN:
        flash('You do not have permission to view this page.', 'warning')
        return redirect(url_for('main.index'))
    user = User.query.get(user_id)
    if user:
        return jsonify({
            'name': user.name,
            'email': user.email,
            'phone': user.phone
        })
    else:
        return jsonify({'error': 'User not found'}), 404


# add dates route
@admin_bp.route('/add-date', methods=['GET', 'POST'],endpoint='add-date')
def add_date():
    if current_user.role != Role.ADMIN:
        flash('You do not have permission to view this page.', 'warning')
        return redirect(url_for('main.index'))

    form = DateForm()
    
    # Fetch doctors to populate the dropdown list
    form.doctor_id.choices = [(doctor.id, doctor.name) for doctor in Doctor.query.all()]

    if form.validate_on_submit():
        # Process the form data
        doctor_id = form.doctor_id.data
        date = form.date.data
        status = form.status.data


        # Create a new schedule
        new = Date(
            doctor_id=doctor_id,
            date=date,
            status=status
        )

        # Add to the database
        db.session.add(new)
        db.session.commit()

        flash('Schedule added successfully!', 'success')
        return redirect(url_for('admin.admin-doctors-dash'))
    # for right corner profile icon
    users = User.query.all()
    admins = [user for user in users if user.role == Role.ADMIN]
    return render_template('admin/add_dates.html', active_page='add-date',form=form,admins=admins)


# add slots route
@admin_bp.route('/add-slot', methods=['GET', 'POST'], endpoint='add-slot')
def add_slots():
    if current_user.role != Role.ADMIN:
        flash('You do not have permission to view this page.', 'warning')
        return redirect(url_for('main.index'))

    form = SlotForm()

    # Populate doctor and date dropdowns
    form.doctor_id.choices = [(doctor.id, doctor.name) for doctor in Doctor.query.all()]
    form.date_id.choices = [(date.id, date.date.strftime('%Y-%m-%d')) for date in Date.query.all()]

    if form.validate_on_submit():
        doctor_id = form.doctor_id.data
        date_id = form.date_id.data

        # List to hold the selected time slots
        selected_slots = []

        # Check each slot field, and if selected, add to the list
        if form.slot_9_00_9_30.data:
            selected_slots.append('9:00-9:30')
        if form.slot_9_30_10_00.data:
            selected_slots.append('9:30-10:00')
        if form.slot_10_00_10_30.data:
            selected_slots.append('10:00-10:30')
        if form.slot_10_30_11_00.data:
            selected_slots.append('10:30-11:00')
        if form.slot_11_00_11_30.data:
            selected_slots.append('11:00-11:30')
        if form.slot_11_30_12_00.data:
            selected_slots.append('11:30-12:00')
        if form.slot_12_00_12_30.data:
            selected_slots.append('12:00-12:30')
        if form.slot_12_30_1_00.data:
            selected_slots.append('12:30-01:00')
        if form.slot_1_00_1_30.data:
            selected_slots.append('01:00-01:30')
        if form.slot_1_30_2_00.data:
            selected_slots.append('01:30-02:00')
        if form.slot_2_00_2_30.data:
            selected_slots.append('02:00-02:30')
        if form.slot_2_30_3_00.data:
            selected_slots.append('02:30-03:00')
        if form.slot_3_00_3_30.data:
            selected_slots.append('03:00-03:30')
        if form.slot_3_30_4_00.data:
            selected_slots.append('03:30-04:00')
        if form.slot_4_00_4_30.data:
            selected_slots.append('04:00-04:30')
        if form.slot_4_30_5_00.data:
            selected_slots.append('04:30-05:00')

        # Iterate through the selected time slots and create Slot entries
        for time_slot in selected_slots:
            new_slot = Slot(
                doctor_id=doctor_id,
                date_id=date_id,
                time_slot=time_slot,
                status=True  # Default status set to True (Active)
            )
            db.session.add(new_slot)

        db.session.commit()

        flash('Slots added successfully!', 'success')
        return redirect(url_for('admin.admin-doctors-dash'))
    users = User.query.all()
    admins = [user for user in users if user.role == Role.ADMIN]
    return render_template('admin/add_slots.html',active_page='add-slot', form=form,admins=admins)

# get dates inside add-slots page 
@admin_bp.route('/api/get-dates/<int:doctor_id>')
def get_dates(doctor_id):
    if current_user.role != Role.ADMIN:
        flash('You do not have permission to view this page.', 'warning')
        return redirect(url_for('main.index'))
    # Query to get dates associated with the given doctor_id
    dates = Date.query.filter_by(doctor_id=doctor_id, status=True).all()

    # Prepare the response data
    date_list = [{'id': date.id, 'date': date.date.strftime('%Y-%m-%d')} for date in dates]

    return jsonify({'dates': date_list})


# when click slot=>staus button it will show appointment details
@admin_bp.route('/appointment-details/<int:appointment_id>')
@login_required
def appointment_details(appointment_id):
    if current_user.role != Role.ADMIN:
        flash('You do not have permission to view this page.', 'warning')
        return redirect(url_for('main.index'))
    appointment = Appointment.query.get_or_404(appointment_id)

    appointment_data = {
        "id": appointment.id,
        "user_id": appointment.user_id,
        "name": appointment.name,
        "email": appointment.email,
        "phone": appointment.phone,
        "age": appointment.age,
        "gender": appointment.gender,
        "address": appointment.address,
        "specialization": appointment.specialization,
        "message": appointment.message,
    }
    
    return jsonify(appointment_data)

# ================================Admin users Details====================================
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


@admin_bp.route('/admin-users', methods=['GET', 'POST'], endpoint='admin-users')
@login_required
def admin_users():
    if current_user.role.value != 'admin':
        flash('You do not have permission to view this page.', 'warning')
        return redirect(url_for('main.index'))  # Redirect to index if not an admin
    search_term = request.args.get('query', '')  # Get search term from query parameters
    if search_term:
        users = User.query.filter(
            (User.id.like(f'%{search_term}%')) |
            (User.name.ilike(f'%{search_term}%')) |
            (User.email.ilike(f'%{search_term}%')) |
            (User.phone.like(f'%{search_term}%'))
        ).all()
    else:
        users = User.query.all()
    form = RegisterForm()  # Instantiate the form here

    if form.validate_on_submit():
        # Handle form submission for adding a new user
        profile_image = form.profile_image.data
        name = form.name.data
        phone = form.phone.data
        email = form.email.data
        password = form.password.data

        PROFILE_FOLDER = os.path.join(current_app.root_path, 'static', 'uploads', 'user_profile')

        if not os.path.exists(PROFILE_FOLDER):
            os.makedirs(PROFILE_FOLDER)

        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('User already exists. Please log in.', 'warning')
            return redirect(url_for('admin.admin-users'))

        profile_image_filename = None
        if profile_image:
            if allowed_file(profile_image.filename):
                profile_image_filename = secure_filename(profile_image.filename)
                profile_image_path = os.path.join(PROFILE_FOLDER, profile_image_filename)
                profile_image.save(profile_image_path)
            else:
                flash('Invalid file type. Only png, jpg, and jpeg are allowed.', 'warning')
                return redirect(url_for('admin.admin-users'))

        new_user = User(
            profile_image=profile_image_filename,
            name=name,
            phone=phone,
            email=email,
            password=generate_password_hash(password),
            role=Role.USER,
            status=Status.ACTIVE
        )

        try:
            db.session.add(new_user)
            db.session.commit()

            msg = Message('Welcome to Derma Detect',
                          sender='learnwithtidke@gmail.com',
                          recipients=[email])
            msg.body = f"Hi {name},\n\nYou have successfully registered.\n\nEmail: {email}\nPassword: {password}"
            mail.send(msg)

            flash('Registration successful! Please check your email for your credentials.', 'success')
            return redirect(url_for('admin.admin-users'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed! Please try again.', 'warning')
    
    # Fetch all users from the database
    users = User.query.all()
    # for right corner profile icon
    admins = [user for user in users if user.role == Role.ADMIN]
    return render_template('admin/admin_users_dash.html', active_page='admin-users',admins=admins, users=users,form=form)


# delete-user in users page
@admin_bp.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role.value != 'admin':
        flash('You do not have permission to perform this action.', 'warning')
        return redirect(url_for('main.index'))
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User has been deleted successfully.', 'success')
    return redirect(url_for('admin.admin-users'))


# update user details in users table
@admin_bp.route('/update_user/<int:user_id>', methods=['POST'])
@login_required
def update_user(user_id):
    # Ensure the current user has the right to perform this action
    if current_user.role.value != 'admin':
        flash('You do not have permission to perform this action.', 'warning')
        return redirect(url_for('main.index'))

    # Fetch the user to be updated
    user = User.query.get_or_404(user_id)

    # Retrieve data from form
    name = request.form.get('name')
    phone = request.form.get('phone')
    email = request.form.get('email')
    role = request.form.get('role')
    status = request.form.get('status')

    # Update user details
    if name:
        user.name = name
    if phone:
        user.phone = phone
    if email:
        user.email = email
    if role:
        # Ensure role is valid
        if role.upper() in Role.__members__:
            user.role = Role[role.upper()]
        else:
            flash('Invalid role selected.', 'warning')
            return redirect(url_for('admin.admin-users'))
    if status:
        # Ensure status is valid
        if status.upper() in Status.__members__:
            user.status = Status[status.upper()]
        else:
            flash('Invalid status selected.', 'warning')
            return redirect(url_for('admin.admin-users'))

    # Commit changes to the database
    try:
        db.session.commit()
        flash('User details updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Update failed. Please try again.', 'danger')

    return redirect(url_for('admin.admin-users'))

# status convertion active to inactive, for users.
@admin_bp.route('/toggle_status_users/<int:user_id>', endpoint='toggle_status_users')
@login_required
def toggle_status(user_id):
    if current_user.role.value != 'admin':
        flash('You do not have permission to perform this action.', 'warning')
        return redirect(url_for('main.index'))  # Redirect to index if not an admin

    user = User.query.get_or_404(user_id)
    
    # Check if the current user is trying to change their own status
    if current_user.id == user_id:
        flash('You cannot change your own status.', 'warning')
        return redirect(url_for('admin.admin-users'))  # Redirect back to the admin users page

    # Toggle between ACTIVE and INACTIVE
    if user.status == Status.ACTIVE:
        user.status = Status.INACTIVE
    else:
        user.status = Status.ACTIVE
    
    db.session.commit()
    flash(f"Status for user {user.name} has been updated to {user.status.name}.", "success")
    return redirect(url_for('admin.admin-users'))  # Redirect back to the admin users page



# ====================================Admin Contacts============================
@admin_bp.route('/admin-contacts',endpoint='admin-contacts')
@login_required
def admin_contacts():
    if current_user.role.value != 'admin':
        flash('You do not have permission to view this page.', 'warning')
        return redirect(url_for('main.index'))  # Redirect to index if not an admin
    contacts = Contact.query.all()
    # Fetch all users from the database
    # for right corner profile icon
    users = User.query.all()
    admins = [user for user in users if user.role == Role.ADMIN]
    return render_template('admin/admin_contacts_dash.html', active_page='admin-contacts', contacts=contacts,users=users,admins=admins)


# delete-contacts in contact page
@admin_bp.route('/delete-contact/<int:contact_id>', methods=['POST'])
@login_required
def delete_contact(contact_id):
    if current_user.role.value != 'admin':
        flash('You do not have permission to perform this action.', 'warning')
        return redirect(url_for('main.index'))
    contact = Contact.query.get_or_404(contact_id)
    db.session.delete(contact)
    db.session.commit()
    flash('Contact has been deleted successfully.', 'success')
    return redirect(url_for('admin.admin-contacts'))


# ==============================Admin Appointment====================================
@admin_bp.route('/admin-appointments', endpoint='admin-appointments')
@login_required
def admin_appointments():
    if current_user.role != Role.ADMIN:
        flash('You do not have permission to view this page.', 'warning')
        return redirect(url_for('main.index'))
    appointments = Appointment.query.all()
    # for right corner profile icon
    users = User.query.all()
    admins = [user for user in users if user.role == Role.ADMIN]
    return render_template('admin/admin_appointments_dash.html', active_page='admin-appointments', admins=admins, appointments=appointments)





# ===========================Admin case report page===========================
@admin_bp.route('/admin/patient-details', endpoint='patient-details')
@login_required
def patient_details():
    if current_user.role != Role.ADMIN:
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
    users1 = users_query.all()
    
    # for right corner profile icon
    users = User.query.all()
    admins = [user for user in users if user.role == Role.ADMIN]

    return render_template(
        'admin/admin_patient_details.html', 
        active_page='patient-details', 
        user=current_user, 
        users=users, 
        users1=users1, 
        admins=admins
    )

# for see case Reports====================
@admin_bp.route('/admin/see-case-reports/<int:user_id>', methods=['GET'])
@login_required
def see_case_reports(user_id):
    if current_user.role != Role.ADMIN:
        flash('You do not have permission to view this page.', 'warning')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)
    appointments = Appointment.query.filter_by(user_id=user_id).all()
    # for right corner profile icon
    users = User.query.all()
    admins = [user for user in users if user.role == Role.ADMIN]

    return render_template(
        'admin/admin_see_case_reports.html', 
        active_page='see-case-reports', 
        user=user, 
        appointments=appointments,
        users=users,
        admins=admins
    )


@admin_bp.route('/uploads/case_reports/<filename>')
def uploaded_file(filename):
    PROFILE_FOLDER = os.path.join(current_app.root_path, 'static', 'uploads', 'case_reports')
    return send_from_directory(PROFILE_FOLDER, filename)