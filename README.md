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
 

## Requirements
- Docker
- docker compose

## Getting started
Build the docker container and run the container for the first time
```docker compose up```

Rebuild the container after adding any new packages
``` docker compose up --build```

The run command script creates a super-user with username & password picked from `.env` file
