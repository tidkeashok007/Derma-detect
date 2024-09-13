# app/routes/auth_routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
import re
import os
from app import db, mail
from app.models.user import User
from flask_mail import Mail, Message  # For sending emails
from app.forms.login_form import LoginForm
from app.forms.register_form import RegisterForm
from app.forms.reset_password_form import ResetPasswordForm
from app.forms.forgot_password import ForgotPasswordForm
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash  # For hashing passwords
from werkzeug.utils import secure_filename
from app.models.user import User, Role, Status  # Adjust import according to your project structure


auth_bp = Blueprint('auth', __name__)

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

@auth_bp.route('/register', methods=['GET', 'POST'], endpoint='register')
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        profile_image = form.profile_image.data  # This should be a file object, not a string
        name = form.name.data
        phone = form.phone.data
        email = form.email.data
        password = form.password.data

        PROFILE_FOLDER = os.path.join(current_app.root_path, 'static', 'uploads', 'user_profile')

        if not os.path.exists(PROFILE_FOLDER):
            os.makedirs(PROFILE_FOLDER)

        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('User already exists. Please log in.', 'danger')
            return redirect(url_for('auth.register'))

        profile_image_filename = None
        if profile_image:
            if allowed_file(profile_image.filename):
                profile_image_filename = secure_filename(profile_image.filename)
                profile_image_path = os.path.join(PROFILE_FOLDER, profile_image_filename)
                profile_image.save(profile_image_path)
            else:
                flash('Invalid file type. Only png, jpg, and jpeg are allowed.', 'danger')
                return redirect(url_for('auth.register'))

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
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed! Please try again.', 'danger')

    return render_template('pages/register.html', form=form)





@auth_bp.route('/login', methods=['GET', 'POST'], endpoint='login')
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()

        if user:
            # Check if the password matches
            if check_password_hash(user.password, password):
                # Check if the user's status is INACTIVE
                if user.status == Status.INACTIVE:
                    flash('Your account is inactive. Please contact support.', 'danger')
                    return redirect(url_for('auth.login'))
                
                # Log in the user if status is ACTIVE
                login_user(user)
                
                # Redirect based on the user's role
                if user.role == Role.ADMIN:
                    return redirect(url_for('admin.admin-dashboard'))
                elif user.role == Role.DOCTOR:
                    return redirect(url_for('doctor.doctor-dashboard'))
                else:
                    return redirect(url_for('main.index'))
            else:
                flash('Invalid password. Please try again.', 'danger')
        else:
            flash('No account found with that email. Please check your email or register.', 'danger')
            
    return render_template('pages/login.html', form=form)



# Route for logout page
@auth_bp.route('/logout', endpoint='logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        if user:
            token = user.get_reset_token()
            msg = Message('Password Reset Request',
                          sender='your_email@example.com',
                          recipients=[user.email])
            msg.body = f'''To reset your password, visit the following link:
{url_for('auth.reset_password', token=token, _external=True)}

If you did not make this request, simply ignore this email and no changes will be made.
'''
            mail.send(msg)
            flash('An email has been sent with instructions to reset your password.')
            return redirect(url_for('auth.login'))
        else:
            flash('This email is not registered.')
    return render_template('pages/forgot_password.html', form=form)


# Route for reset password
@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.verify_reset_token(token)  # Ensure this method is defined in the User model
    if not user:
        flash('That is an invalid or expired token')
        return redirect(url_for('auth.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)  # Ensure set_password method is defined in the User model
        db.session.commit()
        flash('Your password has been updated! You are now able to log in.')
        return redirect(url_for('auth.login'))

    return render_template('pages/reset_password.html', form=form)

