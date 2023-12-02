from flask import Flask, flash, render_template, request, redirect, url_for, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
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
        if not re.match(
            r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$", password
        ):
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

    user_id = session['user_id']  # Get the current user's ID from the session

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Determine the user type (performer or organization)
    cursor.execute("SELECT UserType FROM Users WHERE UserID = ?", (user_id,))
    # Assuming UserType is in the first column
    user_type = cursor.fetchone()[0]

    if user_type == 'musician':
        # Fetch performance requests
        cursor.execute("""
            SELECT e.EventID, e.Date, e.Time, e.Venue, e.Description, e.Status
            FROM Events e
            WHERE e.Status = 'pending'  -- assuming 'open' status indicates available for performers
        """)

        events = cursor.fetchall()
        conn.close()

        return render_template('home.html', events=events)
    elif user_type == 'organization':
        # Render organization dashboard
        return render_template('organization.html')
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
    except sqlite3.Error as e:
        print(e)
        flash("An error occurred while fetching confirmed events.")
    finally:
        conn.close()

    return render_template('organization.html', confirmed_events=confirmed_events)



if __name__ == '__main__':
    app.run(debug=True)
