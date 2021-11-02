#! /bin/bash


# In real production run this manually
# --no-input (answer "yes" to everything)
python manage.py collectstatic --no-input
python manage.py makemigrations notifications --no-input
python manage.py migrate --no-input

gunicorn --bind 0.0.0.0:$APP_PORT \
  --capture-output                \
  --access-logfile '-'            \
  --errror-logfile '-'            \
  config.wsgi:application
