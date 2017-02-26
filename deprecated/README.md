# GeoGuide

#### Use python 3.X.X

#### To run the tool, first install all requirements using pip, Then run gunicorn web server or app.py:

```shell
#Instaling requirements:

pip install -r requirements.txt

#Running the server:

gunicorn wsgi:app
#or
python app.py

```

#### Deploy:
 The branch "deploy" is set to auto deploy on Heroku.
