#! /bin/bash

Green='\e[32m'

printf $Green"*******************************\n"
printf $Green"*******************************\n"
printf $Green"Starting Development Enviroment\n"
printf $Green"*******************************\n"
printf $Green"*******************************\n"


if [ "$1" = 'runserver' ]; then
  python manage.py collectstatic --no-input
  python manage.py makemigrations notifications --no-input
  python manage.py migrate --no-input

  python manage.py runserver 0.0.0.0:$APP_PORT
elif [ "$1" = 'test' ]; then
    pytest
elif [ "$1" = 'manage' ]; then
  python manage.py "${@:2}"
elif [ "$1" = 'celery-beat' ]; then
  celery -A config.celery beat --loglevel=DEBUG
elif [ "$1" = 'celery-worker' ]; then
  celery -A config.celery worker --loglevel=DEBUG
else
  exec "$@"
fi

exit
