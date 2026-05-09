#!/bin/bash
# Start the Django development server with HTTPS
./venv/bin/python manage.py runserver_plus --cert-file cert.crt --key-file cert.key
