#!/bin/sh
gunicorn wsgi:app -w 2 --timeout 10 -b 0.0.0.0:5000