import mysql.connector
import bcrypt
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Function to connect to MySQL database (without selecting a specific database for now)
def get_db_connection():
    connection = mysql.connector.connect(
        host=os.getenv('MYSQL_HOST'),
        user=os.getenv('MYSQL_USER'),
        password='',#os.getenv('MYSQL_PASSWORD'),
        
    )
    return connection

# Function to create the database and tables, and an admin account
def initialize_db():
    connection = get_db_connection()
    cursor = connection.cursor()

    # Check if the database exists, if not, create it
    cursor.execute("SHOW DATABASES LIKE %s", (os.getenv('MYSQL_DATABASE'),))
    database_exists = cursor.fetchone()

    if not database_exists:
        print(f"Database '{os.getenv('MYSQL_DATABASE')}' does not exist. Creating database...")
        cursor.execute(f"CREATE DATABASE {os.getenv('MYSQL_DATABASE')}")
        print(f"Database '{os.getenv('MYSQL_DATABASE')}' created successfully.")
    else:
        print(f"Database '{os.getenv('MYSQL_DATABASE')}' already exists.")

    # Select the database to use
    connection.database = database=os.getenv('MYSQL_DATABASE')

    # Create the 'auth' table with ENUM for role
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS auth (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(100) NOT NULL,
        password VARCHAR(255) NOT NULL,
        role ENUM('admin', 'doctor', 'nurse') NOT NULL
    )
    """)

    # Create the 'rdv' table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rdv (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nom VARCHAR(100) NOT NULL,
        email VARCHAR(100) NOT NULL,
        date DATE NOT NULL,
        heure TIME NOT NULL,
        motif VARCHAR(255) NOT NULL,
        filename VARCHAR(255) NOT NULL,
        predection VARCHAR(50) NOT NULL
    )
    """)

    # Check if the admin account exists
    cursor.execute("SELECT * FROM auth WHERE username = %s", ('admin',))
    admin = cursor.fetchone()

    if not admin:
        # Create an admin account with hashed password
        password = 'admin'
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("INSERT INTO auth (username, password, role) VALUES (%s, %s, %s)",
                       ('admin', hashed_password, 'admin'))
        connection.commit()
        print("Admin account created successfully.")

    # Close the cursor and connection
    cursor.close()
    connection.close()
    print("Database initialization complete.")

if __name__ == '__main__':
    initialize_db()
