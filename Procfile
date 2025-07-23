web: python manage.py migrate && python manage.py collectstatic --noinput && gunicorn citing_retracted.wsgi:application --bind 0.0.0.0:$PORT
worker: celery -A citing_retracted worker -l info
beat: celery -A citing_retracted beat -l info 