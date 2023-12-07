# Crescendo Project Design Document

## Overview
Crescendo is a web-based platform designed to connect musicians with organizations for performance events (specifically oriented for my hometown Fresno, CA). This is my design document outlining the technical implementation of Crescendo, focusing on its architecture, database design, and the "under-the-hood" development of each page.

## Technical Stack
- **Frontend:** HTML (+ Jinja2), CSS (Bootstrap), JavaScript
- **Backend:** Python (Flask)
- **Database:** SQLite3

## Architecture
Crescendo follows the MVC (Model-View-Controller) architecture:
- **Model:** Represents the database schema, including tables for users, events, bookings, and event images.
- **View:** HTML templates with embedded Jinja2 templating for dynamic content rendering.
- **Controller:** Flask routes handling HTTP requests and business logic via <i>app.py</i>.

## Database Design (SQLite3)
The database (`crescendo.db`) consists of four primary tables:
- **Users:** Stores user information, including username/password, type (musician or organization), user email, and a self-set profile description.
- **Events:** Contains details about performance events, including the EventID, the Organizer (ID), Event Date, Event Time, Venue, Event Description, and its Status (confirmed/pending).
- **Bookings:** Tracks applications and confirmations for events. Utilizes BookingID, EventID, MusicianUserID, Status, RequestDate, and ConfirmationDate columns to handle user bookings.
- **EventImages:** Stores images related to events for the gallery feature, logging the ImageID, EventID, MusicianID, ImagePath, and the Event Name for display.

## Key Features

### User Authentication
Implemented using Flask's session management. Passwords are hashed for security.

### Dynamic Dashboards
- **Musician Dashboard:** Displays available and confirmed events. Uses Flask and SQLite commands in `app.py` to fetch relevant data.
- **Organization Dashboard:** Allows event management and displays bookings.

### Event Management
Organizations can create, edit, and delete events, updating the `Events` table. Deleting an event triggers a cascade delete in related tables to maintain database integrity.

### Application System
Musicians can apply for events which updates the `Bookings` table and changes the event status.

### Gallery
A public feature showcasing event images, which implements a JOIN query to fetch data from the `Events` and `EventImages` tables.

## Design Decisions

### Choice of Python and Flask
Python and Flask were the simplest and most straightforward choices for my tech stack, given my rudimentary experience with any other language. Flask's debug mode also allowed for quick and efficient development + debugging of web features.

### SQLite Database
I chose SQLite for its ease of integration with Flask. Crescendo doesn't need a complex database system as its user base will be small at first, and so we avoid the overhead of a larger database system through SQLite.

We can also **JOIN** operations in SQL queries to efficiently combine data from our tables.

### Bootstrap for UI
Bootstrap provided a responsive design framework (I am familiar with) that gave simple UI aesthetic, without having to incorporate extremely complex CSS.

### Security Considerations
- Password hashing using `werkzeug.security` for user security.
- Flask session management for secure user authentication.
- Input validation to prevent SQL injection and maintain data integrity.

## Technical Implementation
All of the `.html` pages use `Bootstrap 5.2.0` elements, a custom stylesheet (`style.css`), a custom `Quicksand` font imported from <i>Google Fonts</i>, and extend upon `layout.html` using `Jinja2` for a responsive and consistent layout.

---
# Main Routes and HTML Pages

## layout.html
All of my `.html` pages extended upon `layout.html` using `Jinja2`. I chose to abstract all of the common components into `layout.html` for consistency across all pages (since each page utilizes the same style references and needs a navigation bar), as well as for ease of maintenance.

#### HTML Structure and Meta Tags
- `layout.html` contains the standard HTML5 doctype, language attributes, meta tags (`UTF-8`), and viewport settings for proper text encoding and responsive design.

#### External Resources and Stylesheets
- Bootstrap CSS (version 5.2.0)
- A Bootstrap JavaScript bundle for interactive components
- FontAwesome icons
- Crescendo's custom stylesheet (`style.css`)
- The connected 'Playpen Sans' and 'Quicksand' custom Google Fonts

#### Title Tag with Jinja2 Templating
- The `<title>` tag dynamically sets the page title using Jinja2's `{% block title %}` which allows each child template to define its unique title.

#### Navigation Bar
- A **brand logo** linking to the landing page.
- **Conditionally Rendered Links** ensure that if the user is logged in, links to the gallery, user profile, and logout are shown. Otherwise, options for gallery, registration, and login are available.
- **Custom classes** for a gradient fade and custom link colors.

#### Main Content Area
- A main container (`<main>`) is defined with padding and text-centering classes (for consistency) where child templates can inject their specific content using `{% block content %}` 



## register.html
Redirects to `login.html` upon successful registration.

1. **Form Submission**: The form uses a POST method to securely transmit data to the server, aligning with the `register` route in `app.py`. It also requires users to satisfy username, password, and email validation (no duplicates, minimum eight characters, alphanumeric, etc.), implemented via `regex`.
2. **Password Hashing**: Upon successful validation, the password is hashed using `werkzeug.security's` `generate_password_hash` before storing it in the database.
3. **Database Storage**: The  username/password, type (musician or organization), user email, and a self-set profile description is stored in the `Users` table by connecting to `crescendo.db` using `sqlite3.connect(DATABASE)` in the `\register` route of `app.py`.

## login.html
Upon successful authentication, the user is redirected to the home page (`home.html`), with their user ID and type stored in Flask's `session`.

1. **Flask Integration**: The login form is created using HTML `<form>` tags with indicated input fields for the username/password. The form's `action` attribute is set to `{{ url_for('login') }}`, linking it to the `login` route defined in `app.py`. This integration facilitates the POST request handling upon form submission.

2. **Backend Authentication**: In `app.py`, the `login` route utilizes `sqlite3.connect(DATABASE)` to connect to the database and fetch the user records if the validation is correct, using the `check_password_hash` function from `werkzeug.security`. If login credentials are incorrect, an error message is displayed.

3. **Navigation Link to Registration**: For new users, the page includes a link to the registration page (`register.html`).

## home.html

If the `user_type == "musician"` for the logged-in user, `home.html` serves as their Performance Dashboard, where they can apply for an event in which case they are redirected to `apply_for_event.html`. 

If the `user_type == "organization"`, they are redirected to `organization.html`.

---

<i>I chose routing `home.html` in this manner to avoid writing a separate route just to redirect to a performer dashboard or an organization dashboard. Setting `home.html` as the "default" performer dashboard inherently covers the first case.</i>

---

- **Session Management**: We first verify if the `user_id` is stored in the Flask session. If the `user_id` is not found in the session, indicating an unauthenticated or logged-out user, the route redirects to the login page using `redirect(url_for('login'))`.
- **User Type Determination**: After connecting to `crescendo.db` using `sqlite3.connect(DATABASE)`, the route queries the `Users` table to determine the `user_type` of the logged-in user based on their `user_id`. This information dictates the subsequent data retrieval and rendering logic.

- **Routing for Musicians**: 
  - If `user_type == "musician"`, the route fetches `pending` events from the `Events` and `Bookings` tables using a WHERE clause such as `... WHERE e.Status = 'pending'`.
  - The route uses a uses an `INNER JOIN` to combine rows from the `Events` and `Bookings` tables based on the `EventID`, ensuring that only those events are selected where the musician (identified by `MusicianUserID` in the `Bookings` table) has a confirmed status (`'confirmed'` in the `Status` column of the `Bookings` table).
  - **Notification**: The route checks for the presence of an `event_notification` in the session to update the performer if the organizer cancels an event.

  - **Template Rendering**: Using Flask's `render_template`, the route dynamically renders the `home.html` template to display the <i>Musician Dashboard</i> that includes lists of available and confirmed events, along with any notifications (all fetched above).

- **Routing for Organizations**: 
  - If `user_type == "organization"`, the route redirects them to a separate organization dashboard route (`/organization`) using `redirect(url_for('organization'))`.

## organization.html
`organization.html` serves as the Organization Dashboard from which organizations can request and manage performance events, as well as view performer profiles via `profile.html`.

#### Session Verification and User Validation.
- **Session Check**: We perform the same authentication check as in `home.html`.
- **User Record Retrieval**: Utilizing `sqlite3.connect(DATABASE)`, a query to the `Users` table retrieves the record of the currently logged-in user.

#### Database Query for Confirmed Events: #### 
- <b>Joining Tables:</b> The query uses `JOIN` clauses to link the `Events`, `Bookings` and `Users` tables to consolidate confirmed event information with their corresponding musicians.
- <b>Selecting Data:</b> The `EventID`, `Date`, `Time`, `Venue`, `Description` columns are selected from the `Events` table, and `Username` from the `Users` table.

- <b>Filtering:</b> Then, the `WHERE` clause filters events based on two conditions:
    - The `OrganizerUserID` in the `Events` table must match the logged-in user's ID, ensuring that only events organized by this user are fetched.

    - The `Status` in the `Bookings` table is checked to be 'confirmed', which filters out any events that are not yet finalized.

**Data Presentation**: The route finally renders `organization.html`, passing the fetched events data.

**Deleting Events:** Once events conclude, organizations may delete the events via the `confirmDeletion(eventId)` Javascript function. This calls the `delete_event` route which performs a cascade delete in the `Events` and `Bookings` tables to remove the event for all users and organizations.

**Musician Details:** If an organization user clicks on a musician's name, they are redirected to `profile.html` via `href="{{ url_for('view_profile'...` and the `view_profile` route in `app.py` to view the musician's details.

## gallery.html
`gallery.html` is designed to showcase images from various events, linking them to their respective events and musicians. It is accessible to anyone, regardless of authentication.

---

I chose to make `gallery.html` accessible to all regardless of authentication so the public can use it as a log (and appreciation) for both the performers and the organizations they performed for!

---

- The core functionality of the `/gallery` route relies on a SQL query that uses `JOIN` to consolidate information fron the `Events` and the `Users`, to retrieve the event dates, venues, and usernames. 
- The query also fetches the `ImagePath` from the `EventImages` table, which is stored in the `images` variable, to be passed into `gallery.html`.


# Minor Routes and HTML Pages

### Logout Route
The `/logout` route facilitates user logout. Upon triggering this route, the user's session data is cleared using `session.pop('user_id', None)`.

### Apply for Event Route 
The (`/apply_for_event/<int:event_id>`) route allows musicians to apply for events. When the POST request is received, it checks if the user is logged in and then updates the `Events` table to change the event status to 'confirmed'. It also inserts a record into the `Bookings` table, marking the booking status as 'confirmed'. The user is then redirected to their home page.

### Request Event Route (`/request_event`)
Organizations use this route to request new events. The POST request retrieves the request event's form data and executes an INSERT operation into the `Events` table with the status set as 'pending'. The user is then redirected to the organization dashboard.

### Update Profile (`/update_profile`)
This route serves both GET and POST requests for user profile updates.
- The GET request fetches current user data from the `Users` table and displays it in a form for the user to update. 

- The POST request updates the user information based on the submitted form data using `UPDATE` operations in SQLite3.

### Upload File (`/upload/<int:event_id>`)
This route allows musicians to upload event-related images through this route. The POST request handles file uploads by checking the file's validity and saving it to a designated upload directory (`static/images`). The file path is then inserted into the `EventImages` table in the database for display in `gallery.html`.

### `landingpage.html`

This page is the hub for Crescendo, featuring a primary catchphrase and a simple login form, with a highlight for Crescendo's three key functionalities below.
- The `landing-top` class defines a flex container, dividing the area into two main sections: one for the primary text, and the other for a simple login form.
- The features section highlight the three key functionalities of the platform in three columns: talent matchmaking, performance scheduling, and a harmonic gallery.

---
---
**Note:** Crescendo was created by Kaden Zheng for the 2023 Fall CS50 Final Project. I would love to turn this into something used by my community, so if you have any bug reports, questions, or concerns, please contact KadenZheng@college.harvard.edu. Thank you for using Crescendo!