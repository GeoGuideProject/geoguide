# [GeoGuide](https://geoguide.herokuapp.com)

## Quick Start

### Basics

Create and activate a virtualenv

```sh
$ sudo pip install virtualenv # if not installed
$ virtualenv env -p python3
$ source env/bin/activate
```

Install the requirements

```sh
$ pip install -r requirements-sqlite.txt
```

### Set Environment Variables

```sh
$ cp .env.example .env
```

Generate a new APP_KEY

```sh
$ python generate_key.py
```

Copy and paste at APP_KEY in `.env` file

### Create DB

```sh
$ python manage.py create_db
$ python manage.py db init
$ python manage.py db migrate
```

### Run the Application

```sh
$ python manage.py runserver
```

So access the application at the address [http://localhost:5000/](http://localhost:5000/)

> Want to specify a different port?

> ```sh
> $ python manage.py runserver -h 0.0.0.0 -p 8080
> ```

### Testing

Without coverage:

```sh
$ python manage.py test
```

With coverage:

```sh
$ python manage.py cov
```
