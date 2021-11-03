#! /bin/bash

Cyan='\e[36m'
Red='\e[31m'

printf $Red"*******************************\n"
printf $Red"*******************************\n"
printf $Red"Starting Production Enviroment\n"
printf $Red"*******************************\n"
printf $Red"*******************************\n"


if [ "$1" = 'runserver' ]; then
  # In real production run this manually
  # --no-input (answer "yes" to everything)
  python manage.py collectstatic --no-input
  python manage.py makemigrations notifications --no-input
  python manage.py migrate --no-input


  gunicorn --bind 0.0.0.0:$APP_PORT \
    --capture-output                \
    --access-logfile '-'            \
    --error-logfile '-'             \
    config.wsgi:application
elif [ "$1" = 'test' ]; then
    python manage.py collectstatic --no-input
    python manage.py makemigrations notifications --no-input
    python manage.py migrate --no-input

    pytest
elif [ "$1" = 'manage' ]; then
  python manage.py "${@:2}"
else
  exec "$@"
fi

exit
