#!/usr/bin/env bash
NAME="cpm" # Name of the application
DJANGODIR=/code/cpm # Django project directory
USER=root # the user to run as
GROUP=root # the group to run as
NUM_WORKERS=1 # how many worker processes should Gunicorn spawn
DJANGO_WSGI_MODULE=config.wsgi # WSGI module name


echo "Starting $NAME as `whoami`"

# Activate the virtual environment
cd $DJANGODIR

export PYTHONPATH=$DJANGODIR:$PYTHONPATH
python manage.py makemigrations && \
  python manage.py migrate && \
  python manage.py collectstatic --noinput  && \
  python manage.py compress --force && \
  python manage.py build_index

# Start your Django Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)
exec gunicorn ${DJANGO_WSGI_MODULE}:application \
--name $NAME \
--workers $NUM_WORKERS \
--user=$USER --group=$GROUP \
--bind 0.0.0.0:8000 \
--log-level=debug \
--log-file=- \
--worker-class gevent \
--threads 2
