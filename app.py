# Import necessary modules
from flask import Flask, flash, render_template, request, redirect, url_for, session, send_from_directory
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import secrets
import sqlite3
import re
import os

# Initialize a Flask application instance
app = Flask(__name__)

# Generate a random 32-character hexadecimal string as a secret key
secret_key = secrets.token_hex(16)
app.secret_key = secret_key  # Set the secret key for the Flask application

# Define the path to the SQLite database file
DATABASE = '/Users/laptopcartuser/vscode/crescendo/crescendo.db'


# Define a route for the landing page
@app.route('/')
def landingpage():
    # Render and return the 'landingpage.html' template
    return render_template('landingpage.html')


# Define a route for user registration with support for GET and POST methods
@app.route('/register', methods=['GET', 'POST'])
def register():
    # Check if the request method is POST (form submission)
    if request.method == 'POST':
        # Retrieve form data
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        # Expecting 'musician' or 'organization'
        user_type = request.form['user_type']
        # Optional profile information
        profile_info = request.form.get('profile_info', '')

        # Username validation: No spaces and must be alphanumeric
        if " " in username or not re.match(r"^\w+$", username):
            return "Username must not contain spaces and must be alphanumeric", 400

        # Password validation: Minimum 8 characters, must include a number and an uppercase letter
        if not re.match(r"^(?=.*[A-Z])(?=.*\d).{8,}$", password):
            return "Password must be at least 8 characters long, contain a number and an uppercase letter", 400

        # Hash the password for secure storage
        hashed_password = generate_password_hash(password)

        # Connect to the database
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        try:
            # Check if the username or email already exists in the database
            cursor.execute(
                "SELECT * FROM Users WHERE Username = ? OR Email = ?", (username, email))
            if cursor.fetchone():
                return "Username or email already exists", 400

            # Insert the new user into the database
            cursor.execute("INSERT INTO Users (Username, Password, Email, UserType, ProfileInformation) VALUES (?, ?, ?, ?, ?)",
                           (username, hashed_password, email, user_type, profile_info))
            conn.commit()  # Commit the changes to the database
        except sqlite3.Error as e:
            print(e)  # Print the error for debugging
            return "An error occurred", 500  # Return an error response
        finally:
            conn.close()  # Close the database connection

        # Redirect the user to the login page upon successful registration
        return redirect(url_for('login'))

    # Render and return the 'register.html' template for GET requests
    return render_template('register.html')


# Define a route for login (with support for both GET and POST methods)
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Check if the request method is POST (form submission)
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Connect to the database
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # Fetch the user record from the database
        try:
            cursor.execute("SELECT * FROM Users WHERE username=?", (username,))
            user = cursor.fetchone()
            # Check if the user exists and the password is correct
            if user and check_password_hash(user[2], password):
                session['user_id'] = user[0]  # Store user ID in session
                session['user_type'] = user[4]
                # Redirect to home page after successful login
                return redirect(url_for('home'))
            else:
                # Return an error message if the username or password is incorrect
                error_message = "Invalid username or password."
                # Render and return 'login.html' template with an error message
                return render_template('login.html', error=error_message)
        except sqlite3.Error as e:
            # Return an error message if an error occurs while fetching the user record
            print(e)
            error_message = "A database error occurred."
            return render_template('login.html', error=error_message)
        finally:
            conn.close()
    else:
        # Render and return the 'login.html' template for GET requests
        return render_template('login.html')


# Define a route for the home page (Performer Dashboard)
@app.route('/home')
def home():
    # Check if the user ID is stored in the session
    if 'user_id' not in session:
        print("User ID not in session")
        return redirect(url_for('login'))
    else:
        # User ID is stored in the session
        # Debugging purposes
        print(f"User ID in session: {session['user_id']}")

    # Fetch the user record from the database
    user_id = session['user_id']
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Determine the user type (performer or organization)
    cursor.execute("SELECT UserType FROM Users WHERE UserID = ?", (user_id,))
    user_type = cursor.fetchone()[0]

    if user_type == 'musician':
        # Fetch available events for musicians
        cursor.execute("""
            SELECT e.EventID, e.Date, e.Time, e.Venue, e.Description, e.Status, 
                   (SELECT Username FROM Users WHERE UserID = e.OrganizerUserID) as OrganizerName
            FROM Events e
            WHERE e.Status = 'pending'
        """)
        available_events = cursor.fetchall()

        # Fetch confirmed events for musicians
        cursor.execute("""
            SELECT e.EventID, e.Date, e.Time, e.Venue, e.Description,
                   (SELECT Username FROM Users WHERE UserID = e.OrganizerUserID) as OrganizerName
            FROM Events e
            JOIN Bookings b ON e.EventID = b.EventID
            WHERE b.MusicianUserID = ? AND b.Status = 'confirmed'
        """, (user_id,))
        confirmed_events = cursor.fetchall()

        conn.close()
        # Check if there is a notification message in the session
        notification = session.pop('event_notification', None)
        # Render and return the 'home.html' template passing in the events, confirmed_events, and notification parameters
        return render_template('home.html', events=available_events, confirmed_events=confirmed_events, notification=notification)

    elif user_type == 'organization':
        # Render organization dashboard
        return redirect(url_for('organization'))

    else:
        # Handle other user types (if any) or unexpected cases
        return "Unsupported user type", 400


# Define a route for applying for an event with GET and POST support
@app.route('/apply_for_event/<int:event_id>', methods=['GET', 'POST'])
def apply_for_event(event_id):
    # Check if the user ID is stored in the session
    if 'user_id' not in session:
        flash("Please log in to apply for events.")
        return redirect(url_for('login'))

    # Fetch the user record from the database
    user_id = session['user_id']

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Check if the user has already applied for the event
    if request.method == 'POST':
        try:
            # Update status in the Events table
            cursor.execute(
                "UPDATE Events SET Status = 'confirmed' WHERE EventID = ?", (event_id,))

            # Insert into Bookings table and set status as 'confirmed'
            cursor.execute("INSERT INTO Bookings (EventID, MusicianUserID, Status, RequestDate) VALUES (?, ?, 'confirmed', CURRENT_DATE)",
                           (event_id, user_id))

            conn.commit()
            flash("Application submitted successfully!")
        except sqlite3.Error as e:
            # Return an error message if an error occurs while fetching the user record
            print(e)
            flash("An error occurred while submitting the application.")
        finally:
            conn.close()

        return redirect(url_for('home'))

    # Fetch event details to display
    cursor.execute("SELECT * FROM Events WHERE EventID = ?", (event_id,))
    event = cursor.fetchone()
    conn.close()
    # Render and return the 'apply_for_event.html' template passing in the events parameter
    return render_template('apply_for_event.html', event=event)


# Define a route for logging out
@app.route('/logout')
def logout():
    # Remove the user ID from the session
    session.pop('user_id', None)
    # Redirect to the landing page
    return redirect(url_for('landingpage'))


# Define a route for requesting events with support for POST
@app.route('/request_event', methods=['POST'])
def request_event():
    # Check if the user ID is stored in the session
    if 'user_id' not in session:
        flash("Please log in to request events.")
        return redirect(url_for('login'))

    # Fetch the user record from the database
    user_id = session['user_id']

    # Retrieve form data
    date = request.form['date']
    time = request.form['time']
    venue = request.form['venue']
    description = request.form['description']

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    #  Insert the new event into the database
    try:
        cursor.execute("""
            INSERT INTO Events (OrganizerUserID, Date, Time, Venue, Description, Status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        """, (user_id, date, time, venue, description))
        conn.commit()
        flash("Event request submitted successfully!")
    except sqlite3.Error as e:
        # Return an error message if an error occurs while fetching the user record
        print(e)
        flash("An error occurred while submitting the event request.")
    finally:
        conn.close()
        # Redirect to the organization home page
    return redirect(url_for('organization'))


# Define a route for viewing organization events / organization home page
@app.route('/organization')
def organization():
    # Check if the user ID is stored in the session
    if 'user_id' not in session:
        flash("Please log in to view this page.")
        return redirect(url_for('login'))

    # Fetch the user record from the database
    user_id = session['user_id']
    print(f"User ID in organization route: {user_id}")  # Debugging statement

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # Fetch confirmed events for the logged-in organization
    cursor.execute("SELECT * FROM Users WHERE UserID = ?", (user_id,))
    user_record = cursor.fetchone()
    if not user_record:
        flash("User record not found.")
        return redirect(url_for('login'))

    # Fetch confirmed events for the logged-in organization
    try:
        cursor.execute("""
            SELECT e.EventID, e.Date, e.Time, e.Venue, e.Description, u.UserID, u.Username
            FROM Events e
            JOIN Bookings b ON e.EventID = b.EventID AND b.Status = 'confirmed'
            JOIN Users u ON b.MusicianUserID = u.UserID
            WHERE e.OrganizerUserID = ?
        """, (user_id,))
        confirmed_events = cursor.fetchall()
    except sqlite3.Error as e:
        # Return an error message if an error occurs while fetching the user record
        print(e)
        flash("An error occurred while fetching confirmed events.")
    finally:
        conn.close()

    # Render organization dashboard
    return render_template('organization.html', confirmed_events=confirmed_events)


@app.route('/delete_event/<int:event_id>', methods=['POST'])
def delete_event(event_id):
    # Ensure the user is logged in and has the appropriate user type
    if 'user_id' not in session or session.get('user_type') != 'organization':
        flash("Unauthorized access.")
        return redirect(url_for('login'))

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    try:
        # Retrieve event details before deletion
        cursor.execute(
            "SELECT Date, Time, Venue, Description FROM Events WHERE EventID = ?", (event_id,))
        event = cursor.fetchone()

        if event:
            # Delete the event from Bookings and Events tables
            cursor.execute(
                "DELETE FROM Bookings WHERE EventID = ?", (event_id,))
            cursor.execute("DELETE FROM Events WHERE EventID = ?", (event_id,))

            # Create a notification message with event details
            notification_msg = f"Event on {event[0]} at {
                event[1]} ({event[2]}) has been cancelled."
            session['event_notification'] = notification_msg

            conn.commit()
            flash("Event deleted successfully.")
        else:
            flash("Event not found.")
    except sqlite3.Error as e:
        # Return an error message if an error occurs while fetching the user record
        print(e)
        flash("An error occurred while deleting the event.")
    finally:
        conn.close()

    # Redirect to the organization home page
    return redirect(url_for('organization'))


# Reference the directory named 'uploads' in the 'static' folder
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Configure the upload folder
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    # Check if the file extension is allowed
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Define a route for uploading files
@app.route('/upload/<int:event_id>', methods=['GET', 'POST'])
def upload_file(event_id):
    # Check if the user ID is stored in the session
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Fetch the user record from the database
    uploaded_file_url = None
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        # Retrieve the file from the request
        file = request.files['file']

        # If the user does not select a file, browser submits an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        # If the file is valid, save it to the upload folder
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Save the relative path (from 'static') in the database
            db_file_path = os.path.join('uploads', filename)

            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            # Insert the new event image into the database
            try:
                cursor.execute("INSERT INTO EventImages (EventID, MusicianUserID, ImagePath) VALUES (?, ?, ?)",
                               (event_id, session['user_id'], db_file_path))
                conn.commit()
            except sqlite3.Error as e:
                # Return an error message if an error occurs while saving the image
                print(e)
                flash("An error occurred while saving the file information.")
            finally:
                conn.close()
            uploaded_file_url = url_for('uploaded_file', filename=filename)

    # Render and return the 'upload.html' template with the event_id and uploaded_file_url parameters
    return render_template('upload.html', event_id=event_id, uploaded_file_url=uploaded_file_url)


# Define a route for uploading file/image
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    # Logic to display the uploaded file
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# Define a route for the gallery
@app.route('/gallery')
def gallery():
    # Fetch the user record from the database
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ei.ImagePath, e.Date, e.Venue, u.Username
        FROM EventImages ei
        JOIN Events e ON ei.EventID = e.EventID
        JOIN Users u ON ei.MusicianUserID = u.UserID
    """)
    # Assign the images parameter to the list of images returned by the query
    images = cursor.fetchall()
    conn.close()
    # Render and return the 'gallery.html' template with the images parameter
    return render_template('gallery.html', images=images)


@app.route('/update_profile', methods=['GET', 'POST'])
def update_profile():
    # Ensure the user is logged in
    if 'user_id' not in session:
        flash("Please log in to update your profile.")
        return redirect(url_for('login'))

    # Handle the GET request (display the form with current user data)
    if request.method == 'GET':
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        try:
            # Fetch the current user's data
            cursor.execute(
                "SELECT Username, Email, UserType, ProfileInformation FROM Users WHERE UserID = ?", (session['user_id'],))
            user_data = cursor.fetchone()
        except sqlite3.Error as e:
            print(e)
            flash("An error occurred while fetching user data.")
            return redirect(url_for('home'))
        finally:
            conn.close()

        if user_data:
            user = {
                'username': user_data[0],
                'email': user_data[1],
                'user_type': user_data[2],
                'profile_info': user_data[3]
            }
            return render_template('profile_edit.html', user=user)
        else:
            flash("User not found.")
            return redirect(url_for('home'))

    # Handle the POST request (update user data)
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        user_type = request.form['user_type']
        profile_info = request.form.get('profile_info', '')

        # Perform your validation here (if necessary)
        # ...

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        try:
            # Update user information in the database
            cursor.execute("""
                UPDATE Users SET Username = ?, Email = ?, UserType = ?, ProfileInformation = ?
                WHERE UserID = ?
            """, (username, email, user_type, profile_info, session['user_id']))
            conn.commit()
            flash("Profile updated successfully!")
        except sqlite3.Error as e:
            print(e)
            flash("An error occurred while updating the profile.")
        finally:
            conn.close()

        return redirect(url_for('home'))


@app.route('/profile/<int:user_id>')
def view_profile(user_id):
    # Ensure the user is logged in
    if 'user_id' not in session:
        flash("Please log in to view profiles.")
        return redirect(url_for('login'))

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT Username, Email, UserType, ProfileInformation FROM Users WHERE UserID = ?", (user_id,))
        user_data = cursor.fetchone()
    except sqlite3.Error as e:
        print(e)
        flash("An error occurred while fetching user data.")
        return redirect(url_for('organization'))
    finally:
        conn.close()

    if user_data:
        user = {
            'username': user_data[0],
            'email': user_data[1],
            'user_type': user_data[2],
            'profile_info': user_data[3]
        }
        return render_template('profile.html', user=user)
    else:
        flash("User not found.")
        return redirect(url_for('organization'))


# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)
