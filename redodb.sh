rm *.sqlite3
rm trialapp/migrations/0001_initial.py
python manage.py makemigrations
python manage.py migrate
python manage.py shell
