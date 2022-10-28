rm db_baaswebapp.sqlite3
python manage.py makemigrations
python manage.py migrate
python manage.py shell