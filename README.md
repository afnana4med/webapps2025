# WebApps 2025 – Django Project

This is a Django-based web application developed for WebApps 2025 coursework. It includes user registration, login, payment module, and external API integration.

---

## 🚀 Features

- User authentication
- Payment app
- Currency API integration
- Bootstrap 5 UI using crispy forms
- Admin panel

---

## ⚙️ Technologies Used

- Django 5.1.7
- Python 3.12 (or 3.10+ recommended for SSL)
- SQLite (for dev)
- Bootstrap 5
- PDFKit
- REST Framework

---

## 🖥️ Local Setup Instructions

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/webapps2025.git
cd webapps2025

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Or venv\Scripts\activate on Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Apply migrations
python manage.py makemigrations
python manage.py migrate

# 5. Create a superuser
python manage.py createsuperuser

# 6. Run the development server
python manage.py runserver

## 📽️ Project Walkthrough Video

Watch the demo:

[▶️ Click to watch the demo video](demo.mp4)

