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

from functools import wraps
import bcrypt
import requests
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from datetime import datetime
load_dotenv()
# Function to connect to MySQL database
def get_db_connection():
    connection = mysql.connector.connect(
        host=os.getenv('MYSQL_HOST'),
        user=os.getenv('MYSQL_USER'),
        password='',#os.getenv('MYSQL_PASSWORD'),
        database=os.getenv('MYSQL_DATABASE')
    )
    return connection

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')  
app.config['WTF_CSRF_ENABLED'] = False
app.config["UPLOAD_FOLDER"] = os.getenv('UPLOAD_FOLDER')
model = tf.keras.models.load_model('my_model.keras', compile=False)
prediction_map = {0: 'glioma', 1: 'meningioma', 2: 'notumor', 3: 'pituitary'}

# Define the appointment form with validation
class AppointmentForm(FlaskForm):
    patient_name = StringField('Name', validators=[DataRequired(), Length(min=5, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    time = TimeField('Appointment time', validators=[DataRequired()])
    motif = TextAreaField('Reason', validators=[Length(max=200)])
    image = FileField('Image', validators=[FileRequired('Dont forget the image'), FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')])
    submit = SubmitField('Make an appointment')




def login_required(roles=None):
    """
    This decorator will check if the user is logged in and optionally check their role.
    :param roles: List of roles (e.g., ['admin', 'doctor']). 
                  If None, any logged-in user can access the route.
    :return: Redirects to login page if the user is not authenticated or does not have the required role.
    """
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            if 'username' not in session:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for('login'))
            
            if roles and session.get('role') not in roles:
                flash("You do not have the permission to access this page.", "danger")
                return redirect(url_for('throwError'))  # Redirect to the main page or an appropriate page

            return func(*args, **kwargs)
        return wrapped
    return decorator
@app.route("/error",methods=['GET'])
def throwError():
    return render_template("error.html")

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

        if user and bcrypt.checkpw(password.encode('utf-8'),user['password'].encode('utf-8')):  # Check password (you should use hashed passwords in real-world apps)
            session['username'] = username
            session['role'] = user['role']
            return render_template('main.html')  # Render the main page if logged in
        else:
            # Show error message on failed login
            return render_template('login.html', error="Invalid username or password")
    
    return render_template('login.html')

# Route for adding an appointment
@app.route('/add-appointment', methods=['GET', 'POST'])
@login_required(roles=['admin', 'nurse'])  

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
            return redirect(url_for('add_appointment'))
    
    return render_template('index.html', form=form)

# Route to view all rendezvous
@app.route('/liste-rendezvous', methods=['GET'])
@login_required(roles=['admin', 'nurse','doctor'])
def liste_rendezvous():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Get the prediction filter and search query from the request
    prediction_filter = request.args.get('prediction', '')
    search_query = request.args.get('search', '')
    future_appointments = request.args.get('future_appointments', 'false') == 'true'
    query = "SELECT * FROM rdv WHERE 1=1"
    params = []

    if prediction_filter and prediction_filter != 'All':
        query += " AND predection = %s"
        params.append(prediction_filter)

    if search_query:
        query += " AND nom LIKE %s"
        params.append(f"%{search_query}%")

     # Filter by future appointments if the checkbox is checked
    if future_appointments:
        current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Current date and time
        query += " AND CONCAT(date, ' ', heure) > %s"
        params.append(current_datetime)

    query += " ORDER BY date, heure"
    cursor.execute(query, tuple(params))
    rendezvous_list = cursor.fetchall()
    cursor.close()
    connection.close()

    predictions = ['All'] + list(prediction_map.values())

    return render_template('list_rdv.html', rendezvous=rendezvous_list, predictions=predictions, search_query=search_query, prediction_filter=prediction_filter,future_appointments=future_appointments)

@app.route('/uploads/<filename>')
@login_required(roles=['admin', 'nurse'])
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/create-account', methods=['GET', 'POST'])
@login_required(roles=['admin'])  
def create_account():
    if request.method == 'POST':
        # Get form data
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        if(role not in ['admin','doctor','nurse']):
            return redirect("/error")
        # Insert the new account data into the 'auth' table
        connection = get_db_connection()
        cursor = connection.cursor()
        hash=bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())
        hash_str=hash.decode('utf-8')
        cursor.execute(
            "INSERT INTO auth (username, password, role) VALUES (%s, %s, %s)",
            (username,hash_str , role)
        )
        connection.commit()
        cursor.close()
        connection.close()

        flash("Account created successfully!", "success")
        return redirect('/')  # Redirect to the main page after account creation

    return render_template('create_account.html')

@app.route('/logout', methods=['POST'])
@login_required(roles=['admin', 'nurse','doctor'])  
def logout():
    # Clear the session data
    session.pop('username', None)
    session.pop('role', None)
    return redirect('/')  # Redirect to the login page


# Route for the dashboard where admin can manage appointments
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required(roles=['admin'])  
def dashboard():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Clear past appointments
    if request.method == 'POST' and 'clear_past' in request.form:
        cursor.execute("DELETE FROM rdv WHERE date < CURDATE()")
        connection.commit()
    # Get search query from the request
    search_query = request.args.get('search', '').strip()

    # SQL query: filter by name or fetch all if no search query
    if search_query:
        cursor.execute("SELECT * FROM rdv WHERE nom LIKE %s", (f"%{search_query}%",))
    else:
        cursor.execute("SELECT * FROM rdv")
    
    appointments = cursor.fetchall()


    cursor.close()
    connection.close()

    return render_template('dashboard.html', appointments=appointments, search_query=search_query)


# Route to edit an appointment
@app.route('/edit-appointment/<int:id>', methods=['GET', 'POST'])
@login_required(roles=['admin'])  
def edit_appointment(id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Fetch the appointment data
    cursor.execute("SELECT * FROM rdv WHERE id = %s", (id,))
    appointment = cursor.fetchone()
    
    if not appointment:
        flash("Appointment not found.", "danger")
        return redirect('/dashboard')

    # If form is submitted
    if request.method == 'POST':
        nom = request.form['nom']
        email = request.form['email']
        date = request.form['date']
        heur = request.form['heur']
        motif = request.form['motif']
        
        # Update the appointment in the database
        cursor.execute("""
            UPDATE rdv SET nom = %s, email = %s, date = %s, heure = %s, motif = %s
            WHERE id = %s
        """, (nom, email, date, heur, motif, id))
        connection.commit()

        flash("Appointment updated successfully!", "success")
        return redirect('/dashboard')

    cursor.close()
    connection.close()

    return render_template('edit_appointment.html', appointment=appointment)

# Route to delete an appointment
@app.route('/delete-appointment/<int:id>', methods=['POST'])
@login_required(roles=['admin'])  
def delete_appointment(id):
    connection = get_db_connection()
    cursor = connection.cursor()

    # Delete the appointment from the database
    cursor.execute("DELETE FROM rdv WHERE id = %s", (id,))
    connection.commit()

    cursor.close()
    connection.close()

    flash("Appointment deleted successfully!", "success")
    return redirect('/dashboard')



if __name__ == '__main__':
   if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config["UPLOAD_FOLDER"])
   app.run(debug=True)
   pass
