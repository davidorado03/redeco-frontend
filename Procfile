release: python manage.py collectstatic --noinput && python manage.py migrate
web: gunicorn frontend_redeco.wsgi:application
