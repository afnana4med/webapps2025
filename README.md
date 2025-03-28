# Webapps2025 Django Project

## Project Description
This is a user registration and payment web application built using Django and deployed on AWS EC2.

## Deployment Details
- **Server:** AWS EC2 Ubuntu 22.04
- **Backend:** Django 5.1.7
- **Database:** SQLite (for development)

## Steps to Run on EC2
1. SSH into the EC2 instance: ssh -i ~/Downloads/webapps2025.pem ubuntu@54.236.148.173
2. Activate virtual environment: cd ~/webapps2025 source venv/bin/activate
3. Run server: python manage.py runserver 0.0.0.0:8000
4. Access in browser: http://54.236.148.173:8000



