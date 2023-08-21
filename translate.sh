echo "make sure you have installed requirements_translate.txt"
django-admin makemessages -l es -l en
python -m scripts.translate
python manage.py compilemessages 1>error_translate.txt
rm error_translate.txt