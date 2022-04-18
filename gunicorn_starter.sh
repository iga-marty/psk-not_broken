#!/bin/sh
gunicorn wsgi:app -w 4 --timeout 5 -b 0.0.0.0:5000