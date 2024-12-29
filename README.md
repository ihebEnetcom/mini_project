# Hospital Rendezvous Management System

This project is a web-based application for managing hospital appointments (rendezvous) and includes an AI-powered brain tumor prediction feature. The application is built using Flask for the back end, HTML and CSS for the front end, and MySQL for database management via an external provider.

## Important Note

This project has been built using **Python version 3.12.3**.\
If you encounter any issues, especially with the AI model, please ensure you are using this version of Python.

## Features

1. **Patient Management**:

   - Add new patient information, including:
     - Name
     - Telephone
     - Brain scan image (grayscale)
   - View a list of all patients stored in the database.

2. **Brain Tumor Prediction**:

   - Upload a grayscale brain scan image for AI-based tumor prediction. Images are stored using an external API.

3. **Authentication and Authorization**:

   - **Authentication**: Users must log in to access the system.
   - **Authorization**: Role-based access control to ensure that only users with appropriate roles can access specific routes (e.g., admin, nurse, doctor).
   - **Middleware and Session**: Authentication and authorization are implemented using middleware and session management to secure routes and ensure only authorized users can perform specific tasks.

## Technology Stack

- **Frontend**: HTML, CSS
- **Backend**: Flask (Python)
- **Database**: External MySQL Provider
- **AI Model**: Predicts brain tumors from grayscale images.
- **Authentication**: Middleware and session management for secure login and role-based access control.

## Database Structure

- **Database Name**: `rendez_vous`
- **Table Name**: `rdv`
- **Columns**:
  - `id` (Primary Key, Auto-increment)
  - `nom` (TEXT)
  - `email` (TEXT)
  - `date` (DATE)
  - `heure` (TIME)
  - `motif` (TEXT)
  - `filename` (TEXT)
  - `predection` (TEXT)

### Authentication Table Structure

- **Table Name**: `auth`
- **Columns**:
  - `id` (Primary Key, Auto-increment)
  - `username` (VARCHAR) - Unique identifier for user login
  - `password` (VARCHAR) - Hashed password for secure storage
  - `role` (VARCHAR) - User role (e.g., `admin`, `nurse`, `doctor`)

Example SQL for `auth` table:

```sql
CREATE TABLE auth (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(100) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL
);
```

## Routes

1. **Authentication Routes**:

   - `/` (Login): Allows users to log in with their credentials.
   - `/logout`: Logs out the current user and clears the session.

2. **Patient Management Routes**:

   - `/add-appointment`: Add new patient details and submit brain scan images for AI prediction (accessible by `admin` and `nurse` roles).
   - `/liste-rendezvous`: View a list of all appointments (accessible by `admin`, `nurse`, and `doctor` roles).

3. **Admin Routes**:

   - `/create-account`: Create new user accounts (accessible by `admin` role).
   - `/dashboard`: View and manage appointments (accessible by `admin` role).
   - `/edit-appointment/<id>`: Edit an existing appointment (accessible by `admin` role).
   - `/delete-appointment/<id>`: Delete an appointment (accessible by `admin` role).

## Setup Instructions

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/ihebEnetcom/mini_project
   cd mini_project
   ```

2. **Set Up the Database**:

   - Use your external MySQL provider to set up the database.
   - Create a database named `rendez_vous`.
   - Create a table named `rdv` with the following structure:
     ```sql
     CREATE TABLE rdv (
       id INT AUTO_INCREMENT PRIMARY KEY,
       nom TEXT,
       email TEXT,
       date DATE,
       heure TIME,
       motif TEXT,
       filename TEXT,
       predection TEXT
     );
     ```
   - Create the `auth` table for user authentication as shown above.

   - **Note**: If you do not wish to use a local MySQL setup, consider using services like [FreeSQLDatabase](https://www.freesqldatabase.com/) for free online MySQL hosting.

3. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application**:

   ```bash
   python app.py
   ```

5. **Access the Application**:
   Open your browser and go to `http://127.0.0.1:5000`.

## Authentication and Authorization Details

### Authentication

- Implemented using **session management** for secure login.
- Users must log in with valid credentials, which are stored in the `auth` table in the database.
- **Session-based Authentication**: On successful login, a session is created for the user.

### Authorization

- Role-based access control (RBAC) is implemented using custom **middleware** (Flask decorators) to protect routes.
- Different user roles (e.g., `admin`, `nurse`, `doctor`) have specific permissions to access certain routes.
- The `@login_required` decorator ensures that only authenticated users with the correct roles can access protected routes.

Example middleware implementation:

```python
def login_required(roles=None):
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            if 'username' not in session:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for('login'))
            if roles and session.get('role') not in roles:
                flash("You do not have the permission to access this page.", "danger")
                return redirect(url_for('throwError'))
            return func(*args, **kwargs)
        return wrapped
    return decorator
```

## AI Model Details

- The AI model predicts the presence of brain tumors from grayscale MRI images.
- The model is integrated into the `/add-appointment` route, where uploaded images are processed, and predictions are made.
- Uploaded images are stored securely using an external API.

### Image Storage with ImageBB API

- **Image Storage**: Instead of storing images locally, the application uses the ImageBB API to securely store and retrieve uploaded brain scan images.
- **How it Works**:
  - Images are uploaded to ImageBB through their API.
  - A link to the stored image is returned and stored in the database (`filename` column).
  - This approach ensures efficient and scalable image management.
- **Integration**:
  - The API key for ImageBB is stored in the `.env` file for security.

Example `.env` file configuration:

```env
IMAGEBB_API_KEY=your_imagebb_api_key
```

- Code Example for Image Upload:

```python
import requests

def upload_image_to_imagebb(image_path):
    url = "https://api.imgbb.com/1/upload"
    payload = {
        "key": os.getenv('IMAGEBB_API_KEY')
    }
    with open(image_path, "rb") as image_file:
        response = requests.post(url, payload, files={"image": image_file})
    if response.status_code == 200:
        return response.json()["data"]["url"]
    else:
        raise Exception("Failed to upload image")
```

### Prediction Categories

1. **Glioma**
2. **Meningioma**
3. **No Tumor**
4. **Pituitary**

## Secure Data Storage

- Sensitive data, such as database credentials and secret keys, are stored in an `.env` file for security.
- Example `.env` file:

```env
SECRET_KEY=your_secret_key
DATABASE_USER=your_username
DATABASE_PASSWORD=your_password
DATABASE_HOST=external_mysql_host
DATABASE_NAME=rendez_vous
IMAGEBB_API_KEY=your_imagebb_api_key
```

- To use the `.env` file, install the `python-dotenv` package and load it as follows:

```python
from dotenv import load_dotenv
import os

load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')
DATABASE_HOST = os.getenv('DATABASE_HOST')
IMAGEBB_API_KEY = os.getenv('IMAGEBB_API_KEY')
```

## Future Improvements

- Enhance AI model accuracy with a larger dataset.
- Improve the UI for a better user experience.
- Add email notifications for appointment confirmations.
