# baasweb

## Production and Development Environment
Use prod or dev to indicate the environment. Configuration are defined on baaswebapp folder on the files dev.py and prod.py

Notice that manage.py is using the dev.py while wsgi is using the prod.py

This can be overwritten by using the --settings=baaswebapp.[prod|dev]

For instance to run the server from command line pointing to production:
python manage.py runserver --settings=baaswebapp.prod

Same applies to db migrations:
python manage.py makemigrations  --settings=baaswebapp.prod

Because manage.py is using dev, the run commands on the visual study is by default calling dev
