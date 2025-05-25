#!/bin/bash

# Миграции
python manage.py migrate --noinput

# Сбор статики
python manage.py collectstatic --noinput

# Запуск Gunicorn с правильным модулем
exec gunicorn foodgramAPI.wsgi:application --bind 0.0.0.0:8000 --workers 3
