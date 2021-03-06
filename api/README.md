# slqe
Capstone projejct
-------
Python 3.7
Django 2.1.15
Django Rest Framework 3.11.0
PyMySQL 0.9.3
django-cors-headers 3.2.1
------

-- Setup Django to connect with MySQL Database --

- Open project

- pip3 install djangorestframework (install django framework)

- pip3 install pymysql (install mysql)

- Change connection string in setting.py file ('DATABASES' part in file)

- pip3 install django-cors-headers (install CORS library)

- python manage.py migrate slqe (migrate table between model and database)

- python manage.py runserver 8080 (run server with 8080 ports)

- Example: http://localhost:8080/api/users (call API in Postman to get all user)




