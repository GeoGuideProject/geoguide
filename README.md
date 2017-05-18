# [GeoGuide](https://geoguide.herokuapp.com)

## Quick Start

### Requirements (skip if Docker)

- [__Python >= 3__](https://www.python.org/downloads/) and `pip`
- [__Node.js >= 6__](https://nodejs.org/en/) and `npm`
  - it's highly recommended install with [`nvm`](https://github.com/creationix/nvm)

### Basics (skip if Docker)

Create and activate a virtualenv

```sh
$ sudo pip install virtualenv # if not installed
$ virtualenv env -p python3
$ source env/bin/activate
```

Install the required packages

```sh
$ pip install -r requirements-sqlite.txt
$ npm install
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

#### Docker

```sh
$ docker-compose run web python manage.py create_db
```

#### Or


```sh
$ python manage.py create_db
$ python manage.py db init
$ python manage.py db migrate
```

### Get a dataset

You can [download a .zip](https://github.com/GeoGuideProject/datasets/archive/master.zip) with all current supported datasets.

Feel free to try another dataset.

### Compile JavaScript and CSS (skip if Docker)

```sh
$ npm run build
```

### Run the Application

#### Docker

```sh
$ docker-compose up
```

So access the application at the address [http://localhost:8000/](http://localhost:8000/)

#### Or

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
