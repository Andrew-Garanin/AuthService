#!/bin/sh

set -e

echo "Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."

python -c "
import socket
import time
import os

host = os.environ.get('DB_HOST', 'db')
port = int(os.environ.get('DB_PORT', 5432))

while True:
    try:
        sock = socket.create_connection((host, port), timeout=1)
        sock.close()
        print('PostgreSQL is ready')
        break
    except (socket.error, socket.timeout):
        time.sleep(0.5)
"

echo "Ensuring migration packages..."
mkdir -p /app/auth_api/migrations
touch /app/auth_api/migrations/__init__.py
touch /app/auth_api/__init__.py

echo "Contents of /app/auth_api/migrations:"
ls -la /app/auth_api/migrations/

echo "Checking Python can see migrations:"
python -c "from django.db.migrations.loader import MigrationLoader; print('Django OK')" || true

echo "Making migrations for auth_api..."
python manage.py makemigrations auth_api

echo "Applying migrations..."
python manage.py migrate

echo "Loading fixtures..."
python manage.py loaddata auth_api/fixtures/initial_data.json || true

echo "Creating test users..."
python manage.py create_test_users || true

echo "Adding ACL deny..."
python manage.py add_acl_deny || true

echo "Starting server..."
exec "$@"
