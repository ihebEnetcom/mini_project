from flask import Flask, render_template, request, redirect, flash, url_for, session
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TimeField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length
import mysql.connector
import tensorflow as tf
import numpy as np
from werkzeug.utils import secure_filename
from PIL import Image
import os
from flask_wtf.file import FileField, FileRequired, FileAllowed
from flask import send_from_directory

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
tf.config.set_visible_devices([], 'GPU')

# Function to connect to MySQL database
def get_db_connection():
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='rendez_vous'
    )
    return connection

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a strong secret key
app.config["UPLOAD_FOLDER"] = "uploads"
model = tf.keras.models.load_model('my_model.keras', compile=False)
model.summary()
print('Input shape is:', model.input_shape)
prediction_map = {0: 'glioma', 1: 'meningioma', 2: 'notumor', 3: 'pituitary'}

# Define the appointment form with validation
class AppointmentForm(FlaskForm):
    patient_name = StringField('Nom', validators=[DataRequired(), Length(min=5, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    time = TimeField('Heure de rendez-vous', validators=[DataRequired()])
    motif = TextAreaField('Motif', validators=[Length(max=200)])
    image = FileField('Image', validators=[FileRequired('Dont forget the image'), FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')])
    submit = SubmitField('Prendre rendez-vous')

# Route for the login page
@app.route('/', methods=['GET', 'POST'])
def login():
    # If the user is already logged in, redirect to the appointment page
    if 'username' in session:
        return render_template('main.html')  # Render the main page if logged in

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check credentials in the database
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM auth WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user and user['password'] == password:  # Check password (you should use hashed passwords in real-world apps)
            session['username'] = username
            session['role'] = user['role']
            return render_template('main.html')  # Render the main page if logged in
        else:
            # Show error message on failed login
            return render_template('login.html', error="Invalid username or password")
    
    return render_template('login.html')

# Route for adding an appointment
@app.route('/add-appointment', methods=['GET', 'POST'])
def add_appointment():
    # Check if the user is logged in and has a role
    if 'username' not in session:
        return redirect('/')  # Redirect to login if not logged in
    
    form = AppointmentForm(meta={'csrf': False})
    if form.validate_on_submit():
        # Get form data
        nom = form.patient_name.data
        email = form.email.data
        date = form.date.data
        heur = form.time.data
        motif = form.motif.data

        if form.image.data:
            file = form.image.data
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            image = Image.open(file_path).resize((150, 150))
            image = np.array(image) / 255.0
            image = np.expand_dims(image, axis=0)
            prediction = model.predict(image)
            predicted_class = np.argmax(prediction)

            # Insert data into the database
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO rdv (nom, email, date, heure, motif, filename, predection) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (nom, email, date, heur, motif, filename, prediction_map[int(predicted_class)])
            )
            connection.commit()
            cursor.close()
            connection.close()

            flash("Rendez-vous pris avec succès!", "success")
            return redirect(url_for('index'))

    return render_template('index.html', form=form)

# Route to view all rendezvous
@app.route('/liste-rendezvous', methods=['GET'])
def liste_rendezvous():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Get the prediction filter and search query from the request
    prediction_filter = request.args.get('prediction', '')
    search_query = request.args.get('search', '')

    query = "SELECT * FROM rdv WHERE 1=1"
    params = []

    if prediction_filter and prediction_filter != 'All':
        query += " AND predection = %s"
        params.append(prediction_filter)

    if search_query:
        query += " AND nom LIKE %s"
        params.append(f"%{search_query}%")

    cursor.execute(query, tuple(params))
    rendezvous_list = cursor.fetchall()
    cursor.close()
    connection.close()

    predictions = ['All'] + list(prediction_map.values())

    return render_template('list_rdv.html', rendezvous=rendezvous_list, predictions=predictions, search_query=search_query, prediction_filter=prediction_filter)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/create-account', methods=['GET', 'POST'])
def create_account():
    if request.method == 'POST':
        # Get form data
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        # Insert the new account data into the 'auth' table
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "INSERT INTO auth (username, password, role) VALUES (%s, %s, %s)",
            (username, password, role)
        )
        connection.commit()
        cursor.close()
        connection.close()

        flash("Account created successfully!", "success")
        return redirect('/')  # Redirect to the main page after account creation

    return render_template('create_account.html')


if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config["UPLOAD_FOLDER"])
    app.run(debug=True)
