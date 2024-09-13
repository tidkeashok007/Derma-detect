# app/routes/main_routes.py
from flask import Blueprint, render_template, flash, url_for, redirect
from app.forms.contact_form import ContactForm
from app import db,mail
from app.models.contact import Contact
from flask_mail import Mail, Message  # For sending emails
from flask_login import current_user
from app.models.doctor import Doctor


main_bp = Blueprint('main', __name__)

@main_bp.route('/', endpoint='index')
def index():
    doctors = Doctor.query.all() 
    return render_template('pages/index.html', active_page='index',doctors=doctors)

@main_bp.route('/about', endpoint='about')
def about():
    return render_template('pages/about.html', active_page='about')

@main_bp.route('/contact', methods=['GET', 'POST'], endpoint='contact')
def contact():
    form = ContactForm()

    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        phone = form.phone.data
        subject = form.subject.data
        message = form.message.data

        # Check if user is authenticated
        if current_user.is_authenticated:
            user_id = current_user.id
            contact_message = Contact(name=name, email=email, phone=phone, subject=subject, message=message, user_id=user_id)
        else:
            user_id = None
            contact_message = Contact(name=name, email=email, phone=phone, subject=subject, message=message, user_id=user_id)

        # Save to database
        db.session.add(contact_message)
        db.session.commit()

        # Send email to admin
        admin_msg = Message(subject,
                            sender=email,
                            recipients=['learnwithtidke@gmail.com'])  # Replace with your email
        admin_msg.body = f'''From: {name} <{email}>\nPhone: {phone}\n\nSubject: {subject}\n\nMessage: {message}'''
        try:
            mail.send(admin_msg)
        except Exception as e:
            flash(f'An error occurred while sending your message to the admin: {str(e)}', 'error')

        # Send confirmation email to user
        confirmation_msg = Message('Thank You for Contacting Derma Detect',
                                   sender='learnwithtidke@gmail.com',  # Replace with your email
                                   recipients=[email])
        confirmation_msg.body = f'''Dear {name},

Thank you for reaching out to Derma Detect. We have received your message and will get back to you soon.

Here are the details we received:
- **Phone**: {phone}
- **Subject**: {subject}
- **Message**: {message}

Best regards,
The Derma Detect Team'''

        try:
            mail.send(confirmation_msg)
            flash('Your message has been sent and saved. Thank you!', 'success')
        except Exception as e:
            flash(f'An error occurred while sending your confirmation email: {str(e)}', 'error')

        # Redirect to the index page
        return redirect(url_for('main.index'))

    return render_template('pages/contact.html', form=form, active_page='contact')
