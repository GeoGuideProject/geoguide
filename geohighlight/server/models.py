# geohighlight/server/models.py

import datetime
from geohighlight.server import app, db


class Dataset(db.Model):

    __tablename__ = 'datasets'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    number_of_rows = db.Column(db.Integer)
    filename = db.Column(db.String(40), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)


    def __init__(self, title, filename, number_of_rows=None):
        self.title = title
        self.filename = filename
        if number_of_rows is not None:
            self.number_of_rows = number_of_rows
        self.created_at = datetime.datetime.now()


    def __repr__(self):
        return '<Dataset {}>'.format(self.sha1)
