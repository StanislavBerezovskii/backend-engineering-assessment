# Backend Engineering Assessment: REST API Quiz for Oper 
[![Python](https://img.shields.io/badge/-Python-464646?style=flat&logo=Python&logoColor=56C0C0&color=008080)](https://www.python.org/)
[![Django](https://img.shields.io/badge/-Django-464646?style=flat&logo=Django&logoColor=56C0C0&color=008080)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/-Django%20REST%20Framework-464646?style=flat&logo=Django%20REST%20Framework&logoColor=56C0C0&color=008080)](https://www.django-rest-framework.org/)
[![JWT](https://img.shields.io/badge/-JWT-464646?style=flat&color=008080)](https://jwt.io/)


This is a small Django REST API project designed for the technical assessment at Oper.
The project features a Quiz web application fully implemented via REST FRAMEWORK viewsets.
Admins can create quizzes, questions, and answers in the admin panel, while users can take
part in the qiuzzes via the demo frontend platform and view the results.

The project also includes API endpoints for user signup and JWT Token authorization with
Email - based verification system.

## Installation:
1. Fork and clone the repository:

2. Install (if you do not already have it) pipenv and install project requirements with it:
```
pip install pipenv
cd path/to/your/project
pipenv install
```
3. Make sure to inspect the demo .env file in the root directory of the project with the following content
   You can use the provided demo sqlite database and .env data (below) or generate your own:
```
DJANGO_SUPERUSER_PASSWORD="Localsuperus3rsecretpasswhere!"
DJANGO_SUPERUSER_USERNAME="candidate"
DJANGO_SUPERUSER_EMAIL="canddiate@example.com"

JWT_TOKEN = "Bearer...'

```
4. Make migrations and migrate the database (if you do not wish to use demo):
```
python manage.py makemigrations
python manage.py migrate
```
5. Create superuser for access to admin panel:
```
python manage.py createsuperuser
```
6. Create some test quizzes, questions and answers in the Admin Panel

7. Run the project in development mode:
```
python manage.py runserver
```
8. Create a test user with a POST request to the signup API:
```
(POST) http://127.0.0.1:8000/api/auth/signup/
```
9. Get a JWT token for the new user and paste it into the .env file:
```
(POST) http://127.0.0.1:8000/api/auth/token/
```
10. Access the demo fronend with:
```
http://127.0.0.1:8000/quizzes/
```

## Requirements
- Docker
- docker compose

## Getting started
Build the docker container and run the container for the first time
```docker compose up```

Rebuild the container after adding any new packages
``` docker compose up --build```

The run command script creates a super-user with username & password picked from `.env` file
