from flask import Flask, render_template, request, redirect, flash, url_for
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
def get_db_connection():
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='rendez_vous'
    )
    return connection

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a strong secret key
app.config["UPLOAD_FOLDER"]="uploads"
model = tf.keras.models.load_model('brain_tumor_model.h5',compile=False)
model.summary()
print('input shape is :',model.input_shape)


# Define the appointment form with validation
class AppointmentForm(FlaskForm):
    patient_name = StringField('Nom', validators=[DataRequired(), Length(min=5, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    time = TimeField('Heure de rendez-vous', validators=[DataRequired()])
    motif = TextAreaField('Motif', validators=[Length(max=200)])
    image = FileField('Image', validators=[FileRequired('dont forget the image'),FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')],)  # Add this line for image upload
    submit = SubmitField('Prendre rendez-vous')

# Page d'accueil
@app.route('/')
def index():
    form =AppointmentForm(meta={'csrf': False})
    return render_template('index.html',form=form)

# Route pour ajouter un rendez-vous
@app.route('/add-appointment', methods=['GET', 'POST'])
def add_appointment():
    print('test')
    form =AppointmentForm(meta={'csrf': False})
    print(form.validate_on_submit())
    if form.validate_on_submit():
        # Get validated form data
        nom = form.patient_name.data
        email = form.email.data
        date = form.date.data
        heur = form.time.data
        motif = form.motif.data
    else:
        return render_template('index.html',form=form)
        
        
    if form.image.data:
        file = form.image.data
        filename= secure_filename(file.filename)
        file_path= os.path.join(app.config['UPLOAD_FOLDER'], filename)

        file.save(file_path)

        image = Image.open(file_path).resize((224,224))
        image=np.array(image)/255.0
        image=np.expand_dims(image,axis=0)
        print(image.shape)
        prediction=model.predict(image)
        print('prediction vector is:',prediction)
        predicted_class=np.argmax(prediction)
        print(predicted_class)
      



        # Insert data into the database
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO rdv (nom, email, date, heure, motif,filename,predection) VALUES (%s, %s, %s, %s, %s,%s,%s)",
            (nom, email, date, heur, motif,filename,int(predicted_class))
        )
        connection.commit()
        cursor.close()
        connection.close()

        flash("Rendez-vous pris avec succès!", "success")
        return redirect(url_for('index'))

    return render_template('index.html',form=form)

# Route pour afficher la liste des rendez-vous
@app.route('/liste-rendezvous')
def liste_rendezvous():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM rdv")
    rendezvous_list = cursor.fetchall()
    cursor.close()
    connection.close()
    
    return render_template('list_rdv.html', rendezvous=rendezvous_list)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config["UPLOAD_FOLDER"])
    app.run(debug=True)

#{'glioma': 0, 'meningioma': 1, 'notumor': 2, 'pituitary': 3}
