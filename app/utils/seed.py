import os
from app import db
from app.models.user import User, Role, Status
from werkzeug.security import generate_password_hash
from flask import current_app
from shutil import copyfile

def allowed_file(filename):
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def seed_users():
    """Seeds an admin user in the database."""
    PROFILE_FOLDER = os.path.join(current_app.root_path, 'static', 'uploads', 'user_profile')

    if not os.path.exists(PROFILE_FOLDER):
        os.makedirs(PROFILE_FOLDER)

    # Check if admin user already exists
    email = 'admin@gmail.com'
    admin_user = User.query.filter_by(email=email).first()

    if not admin_user:
        # Set default profile image (optional)
        default_profile_image = 'default_admin.jpg'
        profile_image_filename = None
        if allowed_file(default_profile_image):
            profile_image_filename = default_profile_image
            profile_image_path = os.path.join(PROFILE_FOLDER, profile_image_filename)

            # Copy default admin profile image if it doesn't exist in the target directory
            source_image_path = os.path.join(current_app.root_path, 'static', 'default', default_profile_image)
            if not os.path.exists(profile_image_path):
                copyfile(source_image_path, profile_image_path)

        # Create an admin user
        new_admin = User(
            profile_image=profile_image_filename,
            name='Admin',
            phone='1234567890',
            email=email,
            password=generate_password_hash('12345678'),
            role=Role.ADMIN,
            status=Status.ACTIVE
        )

        db.session.add(new_admin)
        db.session.commit()
        print("Admin user created successfully!")
    else:
        print("Admin user already exists.")
