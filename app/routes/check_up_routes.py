from flask import Blueprint, render_template, redirect, url_for, flash, request, session, send_file, send_from_directory, current_app
from app.forms.image_upload_form import ImageUploadForm
from flask_login import login_required, current_user
import os
import tensorflow as tf
import numpy as np
import re
import base64
from datetime import datetime
from io import BytesIO
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from werkzeug.utils import secure_filename
from app import db

check_up_bp = Blueprint('check_up', __name__)

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

# Load the pre-trained model without requiring the dataset
cnn = tf.keras.models.load_model('app/models/trained_skin_disease_model.keras')

# You can hardcode or load class names from the model directly if needed
class_names = ['actinic keratosis', 'basal cell carcinoma', 'dermatofibroma', 'melanoma', 'nevus', 'pigmented benign keratosis', 'seborrheic keratosis', 'squamous cell carcinoma', 'vascular lesion', 'choose proper skin image']  # Replace with actual class names

@check_up_bp.route('/check-up', methods=['GET', 'POST'])
@login_required
def check_up():
    form = ImageUploadForm()
    image_url = None
    model_prediction = None

    CHECK_MY_SKIN_FOLDER = os.path.join(current_app.root_path, 'static', 'uploads', 'check_my_skin')
    if not os.path.exists(CHECK_MY_SKIN_FOLDER):
        os.makedirs(CHECK_MY_SKIN_FOLDER)

    if request.method == 'POST':
        image = request.files.get('image') or request.form.get('image')
        if not image:
            flash('No image provided', 'danger')
            return redirect(request.url)

        if isinstance(image, str):  # It's a data URL
            try:
                data_url_pattern = re.compile(r'^data:image/(png|jpg|jpeg);base64,')
                match = data_url_pattern.match(image)
                if match:
                    extension = match.group(1)
                    data = re.sub(data_url_pattern, '', image)
                    image_data = base64.b64decode(data)
                    filename = 'captured_image.' + extension
                    image_path = os.path.join(CHECK_MY_SKIN_FOLDER, filename)
                    with open(image_path, 'wb') as f:
                        f.write(image_data)
                else:
                    flash('Invalid data URL', 'danger')
                    return redirect(request.url)
            except Exception as e:
                flash(f'Error handling data URL: {e}', 'danger')
                return redirect(request.url)
        else:  # It's a file upload
            if image.filename == '':
                flash('No selected file', 'danger')
                return redirect(request.url)

            if allowed_file(image.filename):
                filename = secure_filename(image.filename)
                image_path = os.path.join(CHECK_MY_SKIN_FOLDER, filename)
                image.save(image_path)
            else:
                flash('Invalid file type. Only PNG, JPG, and JPEG are allowed.', 'danger')
                return redirect(request.url)

        try:
            # Process the image and make a prediction
            image = tf.keras.preprocessing.image.load_img(image_path, target_size=(128, 128))
            input_arr = tf.keras.preprocessing.image.img_to_array(image)
            input_arr = np.array([input_arr])
            predictions = cnn.predict(input_arr)

            # Set a threshold for low confidence predictions
            confidence_threshold = 0.5  # You can adjust this based on your model's performance
            result_index = np.argmax(predictions[0])
            confidence_score = np.max(predictions[0])

            if confidence_score < confidence_threshold:
                model_prediction = "choose proper skin image"
            else:
                model_prediction = class_names[result_index]

            # Generate the image URL
            image_url = url_for('check_up.send_image', filename=filename)

            session['image_path'] = image_path
            session['model_prediction'] = model_prediction

            return render_template('pages/check-up.html', form=form, image_path=image_url, model_prediction=model_prediction)
        except Exception as e:
            flash(f'Error processing the image: {e}', 'danger')
            return redirect(request.url)

    return render_template('pages/check-up.html', form=form, active_page='check_up')


@check_up_bp.route('/download_result')
@login_required
def download_result():
    image_path = session.get('image_path')
    model_prediction = session.get('model_prediction')

    if not image_path or not model_prediction:
        flash('No results to download.')
        return redirect(url_for('check_up.check_up'))

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Draw a border
    c.setStrokeColor(colors.black)
    c.setLineWidth(3)
    c.rect(20, 20, width - 40, height - 40)

    # Clinic Name
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2, height - 50, "Derma Detect")

    # Clinic Address
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height - 70, "A108 Adam Street, Calicut, IN 535022")

    # Date
    c.setFont("Helvetica", 12)
    c.drawRightString(width - 50, height - 90, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Horizontal line
    c.setLineWidth(1)
    c.line(50, height - 100, width - 50, height - 100)

    # Logo
    logo_path = os.path.join(current_app.root_path, 'static', 'admin-dash', 'img', 'logo-small.png')
    if os.path.exists(logo_path):
        c.drawImage(logo_path, 195, height - 55, width=25, height=25)

    # Add image if it exists
    if image_path:
        img_reader = ImageReader(image_path)
        img_width, img_height = img_reader.getSize()
        aspect_ratio = img_width / img_height
        img_display_width = 200
        img_display_height = img_display_width / aspect_ratio
        c.drawImage(img_reader, width / 2 - img_display_width / 2, height - 160 - img_display_height, width=img_display_width, height=img_display_height)

    # Predicted Disease
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 160 - img_display_height - 50, "Predicted Disease:")
    c.setFont("Helvetica", 14)
    c.drawString(200, height - 160 - img_display_height - 50, model_prediction)

    # Patient Name
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 160 - img_display_height - 80, "Patient Name:")
    c.setFont("Helvetica", 14)
    c.drawString(200, height - 160 - img_display_height - 80, current_user.name)

    # Patient Email
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 160 - img_display_height - 110, "Patient Email:")
    c.setFont("Helvetica", 14)
    c.drawString(200, height - 160 - img_display_height - 110, current_user.email)

    # Horizontal line after email
    c.line(50, height - 160 - img_display_height - 130, width - 50, height - 160 - img_display_height - 130)

    # Web Prediction
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 160 - img_display_height - 160, "Web Prediction:")
    c.setFont("Helvetica", 14)
    c.drawString(200, height - 160 - img_display_height - 160, model_prediction)

    # Watermark
    c.saveState()
    c.setFont("Helvetica", 40)
    c.setFillGray(0.5, 0.5)
    c.translate(width / 2, height / 2)
    c.rotate(45)
    for x in range(-int(width), int(width), 300):
        for y in range(-int(height), int(height), 200):
            c.drawCentredString(x, y, "Derma Detect")
    c.restoreState()

    # Save the PDF
    c.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='result.pdf', mimetype='application/pdf')


@check_up_bp.route('/static/uploads/check_my_skin/<filename>')
def send_image(filename):
    return send_from_directory(os.path.join(current_app.root_path, 'static', 'uploads', 'check_my_skin'), filename)
