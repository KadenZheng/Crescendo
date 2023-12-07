# Crescendo

## Introduction
Crescendo is a web-based application designed to build connections between young musicians and organizations in the Fresno community. The platform enables organizations to request performances from local talent and manage event details, while offering musicians the opportunity to showcase their artistry and engage in community events.

## Technologies
- **Backend:** Python, Flask
- **Database:** SQLite
- **Frontend:** HTML (+ Jinja2), CSS (Bootstrap), JavaScript

## Features
- **User Registration and Authentication:** Separate registration processes for musicians and organizations with secure login functionality.
- **Profile Management:** Musicians and organizations can create and edit their profiles with personal information and contact details.
- **Profile Viewing:** Organizations can view the profiles of musicians registered for their events.
- **Event Management:** Organizations can request new performance events, while musicians can view available events and apply for them.
- **Gallery:** A dedicated page showcasing images from past events (uploaded by the musicians), highlighting the community's engagements.
- **Responsive Design:** The website is fully responsive and can be accessed on various devices and screen sizes.


## Installation and Setup
### Prerequisites
- Python 3.8 or higher
- Flask
- SQLite

To set up the Crescendo project on your local machine, follow these steps:
```bash
git clone https://github.com/KadenZheng/crescendo.git

cd crescendo
```

## Usage
To run the application, in your terminal, either run:
```bash
python app.py
```
or
```bash
flask run
```
# Crescendo Usage Guide

## Table of Contents
- [Registration](#registration)
- [Login](#login)
- [Dashboard](#dashboard)
  - [Musician Dashboard](#musician-dashboard)
  - [Organization Dashboard](#organization-dashboard)
- [Event Management](#event-management)
- [Applying for Events](#applying-for-events)
- [Gallery](#gallery)

## Registration
To use Crescendo, users must first register an account. There are two types of users: musicians and organizations.

### Steps for Registration:
1. Navigate to the **Register** page from the main menu.
2. Fill in the required fields:
   - Username (must be unique)
   - Email Address
   - Password
   - User Type (Musician or Organization)
   - Profile Information (optional)
3. Click the **Register** button to create your account.

## Login
Registered users can log in to access their personalized dashboard.

### Steps for Login:
1. Go to the **Login** page.
2. Enter your Username and Password.
3. Click the **Login** button.

## Dashboard
Upon logging in, users are directed to their respective dashboards.

### Musician Dashboard
Musicians can view available performance events and their confirmed events.

#### Features:
- **Available Performance Events:** List of events seeking musicians. Musicians can apply for these events.
- **Confirmed Performance Events:** Shows the musician's confirmed performances and allows them to upload images for the event.

### Organization Dashboard
Organizations can manage events and view confirmed applications from musicians.

#### Features:
- **Request Event:** Organizations can create new performance requests.
- **Confirmed Performance Events:** View and manage events that have been confirmed with musicians.

## Profile Management
Users can update their profile information.

### Steps to Update Profile:
1. Ensure you are logged in.
2. Click on the **Profile** option in the Navigation Bar.
3. Edit your profile and contact information.
4. Save changes.

## Event Management
Organizations can create and manage events.

### Creating an Event:
1. From the organization dashboard, click on **Request Event**.
2. Fill in the event details: Date, Time, Venue, and Description.
3. Submit the event request.

### Managing Events:
- **View Event:** View details of existing events, including the musician.
- **View Musician:** Click on the musician's name to view their profile description and contact information.
- **Delete Event:** Remove an event. This will notify relevant musicians if they have applied.

## Applying for Events
Musicians can apply for available events.

### Steps to Apply:
1. From the musician dashboard, view the **Available Performance Events**.
2. Click **Apply** on the event you are interested in.
3. Confirm your application.

## Gallery
The gallery showcases images from past events.

### Viewing the Gallery:
1. Click on the **Gallery** link in the navigation bar.
2. Browse through event images and details.


# Crescendo Video Presentation
Please use the following link to view a three minute summary and walkthrough of **Crescendo**!

**https://www.youtube.com/watch?v=vyZ7MXfDJ-8**

---
---

**Note:** Crescendo was created by Kaden Zheng for the 2023 Fall CS50 Final Project. I would love to turn this into something used by my community, so if you have any bug reports, questions, or concerns, please contact KadenZheng@college.harvard.edu. Thank you for using Crescendo!