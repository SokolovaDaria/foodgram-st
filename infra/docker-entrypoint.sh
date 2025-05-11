
echo "Waiting for postgres..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done
echo "PostgreSQL started"

echo "Applying database migrations..."
python backend/manage.py migrate --noinput

echo "Collecting static files..."
python backend/manage.py collectstatic --noinput --clear


echo "Starting Gunicorn..."
exec gunicorn foodgram.wsgi:application --bind 0.0.0.0:8000 --workers 3