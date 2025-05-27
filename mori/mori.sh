#!/bin/bash
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc"  -delete
python manage.py makemigrations
python manage.py makemigrations morisite
python manage.py migrate
python manage.py runserver 0.0.0.0:8000