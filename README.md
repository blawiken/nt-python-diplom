# Start project

## Local
```
> git clone https://github.com/blawiken/nt-python-diplom
> cd orders
> python -m venv .venv
> .\.venv\Scripts\activate
> pip install -r requirements.txt
> python manage.py makemigrations
> python manage.py migrate
> python manage.py runserver
```
[127.0.0.1:8000/api/](http://127.0.0.1:8000/api/)


## Docker
```docker-compose up --build```

[localhost:8000/api/](http://localhost:8000/api/)


## .env file
Don't forget to fill out the .env file.