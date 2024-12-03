Hospital Rendezvous Management System
This project is a web-based application for managing hospital appointments (rendezvous) and includes an AI-powered brain tumor prediction feature. The application is built using Flask for the back end, HTML and CSS for the front end, and MySQL for database management via XAMPP.

Features
Patient Management:
Add new patient information, including:
Name
Telephone
Brain scan image (grayscale)
View a list of all patients stored in the database.
Brain Tumor Prediction:
Upload a grayscale brain scan image for AI-based tumor prediction.
Technology Stack
Frontend: HTML, CSS
Backend: Flask (Python)
Database: MySQL (using XAMPP services)
AI Model: Predicts brain tumors from grayscale images.
Database Structure
Database Name: rendez_vous
Table Name: rdv
Columns:
id (Primary Key, Auto-increment)
name (VARCHAR)
telephone (VARCHAR)
image_path (VARCHAR) - Path to the uploaded brain scan image
Additional fields as needed for patient information
Routes
/add_patient:
Form to input patient details (name, telephone, brain image, etc.).
Saves the information to the rdv table.
/list_patients:
Displays all patients stored in the database.
Setup Instructions
Clone the Repository:

bash
Copy code
git clone <repository-url>
cd hospital-rendezvous-system
Set Up the Database:

Open XAMPP and start Apache and MySQL.
Create a database named rendez_vous in phpMyAdmin.
Create a table named rdv with the structure described above.
Install Dependencies:

bash
Copy code
pip install -r requirements.txt
Run the Application:

bash
Copy code
flask run
Access the Application: Open your browser and go to http://127.0.0.1:5000.

AI Model Details
The AI model is trained to predict the presence of brain tumors from grayscale MRI images.
It is integrated into the /add_patient route to process uploaded images.
Future Improvements
Add authentication for secure access.
Enhance AI model accuracy with a larger dataset.
Improve the UI for better user experience.
