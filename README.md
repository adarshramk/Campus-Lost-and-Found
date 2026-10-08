# Campus Lost & Found

A simple Flask + SQLite web application for college students to report lost/found items and help return them to their owners.

## Features

- Student registration and login
- Report a lost or found item
- Upload an item photo
- Search and filter reports
- View item details
- See the reporter's contact email
- Personal "My Reports" page
- Mark your own report as resolved
- SQLite database
- Password hashing
- Clean responsive UI

## Tech Stack

- Python
- Flask
- Flask-SQLAlchemy
- SQLite
- HTML
- CSS
- Vanilla JavaScript

## Run locally

### 1. Create a virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the application

```bash
python app.py
```

Open:

http://127.0.0.1:5000

The SQLite database is created automatically the first time the app starts.

## Suggested demo

1. Create account A.
2. Report a lost wallet.
3. Create account B in another browser/incognito window.
4. Report a found wallet.
5. Use search/filter to find reports.
6. Open an item to see the reporter's email.
7. Mark your own report as resolved.

## Project structure

```text
campus_lost_found/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── report.html
│   ├── item_detail.html
│   └── my_items.html
└── static/
    ├── style.css
    └── uploads/
        └── .gitkeep
```

## Important

This is intentionally a simple educational project. Before public deployment, add CSRF protection, stronger secret management, production configuration, email verification, stricter upload validation, rate limiting, and proper privacy controls.
