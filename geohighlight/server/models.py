# geohighlight/server/models.py

import datetime
from geohighlight.server import app, db


class Dataset(db.Model):

    __tablename__ = 'datasets'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    filename = db.Column(db.String(40), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)


    def __init__(self, filename):
        self.filename = filename
        self.created_at = datetime.datetime.now()


    def __repr__(self):
        return '<Dataset {}>'.format(self.sha1)
