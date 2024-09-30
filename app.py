from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import cv2
import face_recognition
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, storage

# Initialize Flask app
app = Flask(__name__)

# Update this with your Firebase credentials and storage bucket
cred = credentials.Certificate("newjason-4da8b-firebase-adminsdk-dbm2h-cc50ee8292.json")  # <--- Update this
firebase_admin.initialize_app(cred, {
    'storageBucket': 'gs://newjason-4da8b.appspot.com'  # <--- Update this
})


# Path to store attendance images
image_folder = 'attendance_images'
if not os.path.exists(image_folder):
    os.makedirs(image_folder)

# Firebase storage bucket
bucket = storage.bucket()


# Load known face images and encode them
def load_known_faces():
    known_face_encodings = []
    known_face_names = []

    for filename in os.listdir("known_faces"):
        image = face_recognition.load_image_file(f"known_faces/{filename}")
        encoding = face_recognition.face_encodings(image)[0]
        known_face_encodings.append(encoding)
        known_face_names.append(filename.split(".")[0])
    
    return known_face_encodings, known_face_names


# Route for the homepage
@app.route('/')
def index():
    return render_template('index.html')


# Route to handle image upload and recognition
@app.route('/upload_image', methods=['POST'])
def upload_image():
    file = request.files['image']
    image_path = os.path.join(image_folder, 'latest_capture.jpg')
    file.save(image_path)

    # Process the image to detect faces
    known_face_encodings, known_face_names = load_known_faces()
    image = face_recognition.load_image_file(image_path)
    face_encodings = face_recognition.face_encodings(image)

    if len(face_encodings) > 0:
        # Compare with known faces
        matches = face_recognition.compare_faces(known_face_encodings, face_encodings[0])
        name = "Unknown"
        if True in matches:
            first_match_index = matches.index(True)
            name = known_face_names[first_match_index]

        # Save image to Firebase Storage
        upload_to_firebase(image_path, name)

        return jsonify({"message": f"{name} recognized and saved."})
    else:
        return jsonify({"message": "No faces detected."})


# Function to upload image to Firebase Storage
def upload_to_firebase(image_path, name):
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    blob = bucket.blob(f'attendance/{name}_{timestamp}.jpg')
    blob.upload_from_filename(image_path)


# Route to display attendance
@app.route('/attendance')
def attendance():
    # Get list of images from Firebase
    blobs = bucket.list_blobs(prefix='attendance/')
    image_urls = [blob.generate_signed_url(expiration=3600) for blob in blobs]
    return render_template('attendance.html', image_urls=image_urls)


# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
