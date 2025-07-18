# Vehicle Parking App

This is a Flask-based multi-user web application that manages vehicle parking for vehicles. It allows users to book parking spots and administrators to manage multiple parking lots. The application is built using Python, Flask, Jinja2, HTML/CSS/Bootstrap for frontend, and SQLite for the database. 

---

## 🔧 Tech Stack

- **Backend**: Python, Flask, Flask-SQLAlchemy
- **Frontend**: HTML, CSS, Jinja2
- **Database**: SQLite (Auto-generated via code)
- **Authentication**: Simple session-based login system

---
## Steps of Setup
- Create Virtual Environment:
- Ensures isolated Python environment:
```bash
python -m venv venv 
```
- Activate Virtual Environment:
```bash 
venv/scripts/activate
```
- Run this in the folder containing requirements.txt
```bash 
pip install -r "requirements.txt" 
```
- Then run a app using below command (Note: --reload is optional)
```bash
flask --app app run --reload 
```

## Folder structure
parking_app_23f2005464
    │   app.py
    │   Readme.md
    │   Report.docx
    │   requirements.txt
    │
    ├───controllers
    │       admin.py
    │       authentication.py
    │       user.py
    │
    ├───instance
    │       parking_app.db
    │
    ├───models
    │       model.py
    │
    ├───static
    │       diagonal-black-white-empty-car-parking-city-background_199726-5263.avif
    │       download.png
    │       erdiagram.png
    │       home.css
    │       login_style.css
    │       register.css
    │
    └───templates
            add_lot_form.html
            admin_home.html
            admin_search.html
            admin_spot_data.html
            admin_summary.html
            booking_form.html
            edit_admin_profile.html
            edit_lot_form.html
            edit_profile_user.html
            error.html
            forgot_pwd.html
            home.html
            landing_page.html
            login.html
            payment.html
            register.html
            spot_data.html
            success.html
            users_data.html
            user_summary.html





## Database  Entity Relationship Diagram :
![Er diagram](static\erdiagram.png)