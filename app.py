from flask import Flask, flash, render_template, request, redirect, url_for, session, send_from_directory
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import re
import os

app = Flask(__name__)
app.secret_key = '123456789'  # Replace with a random secret key

DATABASE = '/Users/laptopcartuser/vscode/crescendo/crescendo.db'


@app.route('/')
def landingpage():
    return render_template('landingpage.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        user_type = request.form['user_type']  # 'musician' or 'organization'
        profile_info = request.form.get('profile_info', '')

        # Validate username (no spaces, unique)
        if " " in username or not re.match(r"^\w+$", username):
            return "Username must not contain spaces and must be alphanumeric", 400

        # Validate password (one number, one uppercase, etc.)
        if not re.match(r"^(?=.*[A-Z])(?=.*\d).{8,}$", password):
            return "Password must be at least 8 characters long, contain a number and an uppercase letter", 400

        # Hash the password
        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        try:
            # Check if username or email already exists
            cursor.execute(
                "SELECT * FROM Users WHERE Username = ? OR Email = ?", (username, email))
            if cursor.fetchone():
                return "Username or email already exists", 400

            # Insert new user
            cursor.execute("INSERT INTO Users (Username, Password, Email, UserType, ProfileInformation) VALUES (?, ?, ?, ?, ?)",
                           (username, hashed_password, email, user_type, profile_info))
            conn.commit()
        except sqlite3.Error as e:
            print(e)
            return "An error occurred", 500
        finally:
            conn.close()

        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM Users WHERE username=?", (username,))
            user = cursor.fetchone()
            if user and check_password_hash(user[2], password):
                session['user_id'] = user[0]  # Store user ID in session
                session['user_type'] = user[4]
                print(f"User type set in session: {session['user_type']}")
                print(f"User ID set in session: {session['user_id']}") 
                # Redirect to home page after successful login
                return redirect(url_for('home'))
            else:
                error_message = "Invalid username or password."
                return render_template('login.html', error=error_message)
        except sqlite3.Error as e:
            print(e)
            error_message = "A database error occurred."
            return render_template('login.html', error=error_message)
        finally:
            conn.close()
    else:
        return render_template('login.html')


@app.route('/success')
def success():
    return render_template('home.html')


@app.route('/home')
def home():
    if 'user_id' not in session:
        print("User ID not in session")
        return redirect(url_for('login'))
    else:
        print(f"User ID in session: {session['user_id']}")

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

        # Fetch confirmed events for the logged-in musician
        cursor.execute("""
            SELECT e.EventID, e.Date, e.Time, e.Venue, e.Description, 
                   (SELECT Username FROM Users WHERE UserID = e.OrganizerUserID) as OrganizerName
            FROM Events e
            JOIN Bookings b ON e.EventID = b.EventID
            WHERE b.MusicianUserID = ? AND b.Status = 'confirmed'
        """, (user_id,))
        confirmed_events = cursor.fetchall()

        conn.close()
        return render_template('home.html', events=available_events, confirmed_events=confirmed_events)

    elif user_type == 'organization':
        # Render organization dashboard
        return redirect(url_for('organization'))

    else:
        # Handle other user types (if any) or unexpected cases
        return "Unsupported user type", 400



@app.route('/apply_for_event/<int:event_id>', methods=['GET', 'POST'])
def apply_for_event(event_id):
    if 'user_id' not in session:
        flash("Please log in to apply for events.")
        return redirect(url_for('login'))

    user_id = session['user_id']

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

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
            print(e)
            flash("An error occurred while submitting the application.")
        finally:
            conn.close()

        return redirect(url_for('home'))

    # Fetch event details to display
    cursor.execute("SELECT * FROM Events WHERE EventID = ?", (event_id,))
    event = cursor.fetchone()
    conn.close()

    return render_template('apply_for_event.html', event=event)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    # You can add more session variables to clear, if needed
    return redirect(url_for('landingpage'))


@app.route('/request_event', methods=['POST'])
def request_event():
    if 'user_id' not in session:
        flash("Please log in to request events.")
        return redirect(url_for('login'))

    user_id = session['user_id']

    date = request.form['date']
    time = request.form['time']
    venue = request.form['venue']
    description = request.form['description']

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO Events (OrganizerUserID, Date, Time, Venue, Description, Status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        """, (user_id, date, time, venue, description))
        conn.commit()
        flash("Event request submitted successfully!")
    except sqlite3.Error as e:
        print(e)
        flash("An error occurred while submitting the event request.")
    finally:
        conn.close()

    return redirect(url_for('organization'))


@app.route('/organization')
def organization():
    if 'user_id' not in session:
        flash("Please log in to view this page.")
        return redirect(url_for('login'))

    user_id = session['user_id']
    print(f"User ID in organization route: {user_id}")  # Debugging statement

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Users WHERE UserID = ?", (user_id,))
    user_record = cursor.fetchone()
    if not user_record:
        flash("User record not found.")
        return redirect(url_for('login'))
    print(f"User record: {user_record}")  # Debugging statement


    try:
        cursor.execute("""
            SELECT e.EventID, e.Date, e.Time, e.Venue, e.Description, 
                   (SELECT Username FROM Users WHERE UserID = b.MusicianUserID)
            FROM Events e
            LEFT JOIN Bookings b ON e.EventID = b.EventID AND b.Status = 'confirmed'
            WHERE e.OrganizerUserID = ? AND e.Status = 'confirmed'
        """, (user_id,))
        confirmed_events = cursor.fetchall()
        print("--------CONFIRMED EVENTS--------")
        print(confirmed_events)
    except sqlite3.Error as e:
        print(e)
        flash("An error occurred while fetching confirmed events.")
    finally:
        conn.close()

    return render_template('organization.html', confirmed_events=confirmed_events)

# Assuming you have a directory named 'uploads' in your static folder
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload/<int:event_id>', methods=['GET', 'POST'])
def upload_file(event_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    uploaded_file_url = None
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['file']
        
        # If the user does not select a file, browser submits an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Save the relative path (from 'static') in the database
            db_file_path = os.path.join('uploads', filename)

            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO EventImages (EventID, MusicianUserID, ImagePath) VALUES (?, ?, ?)", 
                            (event_id, session['user_id'], db_file_path))
                conn.commit()
            except sqlite3.Error as e:
                print(e)
                flash("An error occurred while saving the file information.")
            finally:
                conn.close()

            uploaded_file_url = url_for('uploaded_file', filename=filename)

    return render_template('upload.html', event_id=event_id, uploaded_file_url=uploaded_file_url)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/gallery')
def gallery():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ei.ImagePath, e.Date, e.Venue, u.Username
        FROM EventImages ei
        JOIN Events e ON ei.EventID = e.EventID
        JOIN Users u ON ei.MusicianUserID = u.UserID
    """)
    images = cursor.fetchall()
    conn.close()
    return render_template('gallery.html', images=images)



if __name__ == '__main__':
    app.run(debug=True)
