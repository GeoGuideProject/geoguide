# geohighlight/server/models.py

import datetime
from geohighlight.server import app, db


class Dataset(db.Model):

    __tablename__ = 'datasets'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    number_of_rows = db.Column(db.Integer)
    filename = db.Column(db.String(40), nullable=False)
    latitude_attr = db.Column(db.String(50))
    longitude_attr = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, nullable=False)


    def __init__(self, title, filename, number_of_rows=None, latitude_attr=None, longitude_attr=None):
        self.title = title
        self.filename = filename
        self.number_of_rows = number_of_rows
        self.latitude_attr = latitude_attr
        self.longitude_attr = longitude_attr
        self.created_at = datetime.datetime.now()


    def __repr__(self):
        return '<Dataset {}>'.format(self.filename)
