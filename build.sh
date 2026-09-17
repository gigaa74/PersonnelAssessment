#!/usr/bin/env bash
set -o errexit

python -m pip install .
python manage.py collectstatic --no-input
python manage.py migrate --no-input
python manage.py bootstrap_admin

