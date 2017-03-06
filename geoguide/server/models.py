# geoguide/server/models.py

import datetime
import enum
from geoguide.server import app, db
from sqlalchemy_utils import ChoiceType


class Dataset(db.Model):

    __tablename__ = 'datasets'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    number_of_rows = db.Column(db.Integer)
    filename = db.Column(db.String(40), nullable=False)
    latitude_attr = db.Column(db.String(50))
    longitude_attr = db.Column(db.String(50))
    attributes = db.relationship('Attribute', backref='dataset', cascade='all, delete-orphan')
    created_at = db.Column(db.DateTime, nullable=False)
    indexed_at = db.Column(db.DateTime)


    def __init__(self, title, filename, number_of_rows=None, latitude_attr=None, longitude_attr=None):
        self.title = title
        self.filename = filename
        self.number_of_rows = number_of_rows
        self.latitude_attr = latitude_attr
        self.longitude_attr = longitude_attr
        self.created_at = datetime.datetime.now()


    def __repr__(self):
        return '<Dataset {}>'.format(self.filename)


class AttributeType(enum.Enum):
    datetime = 1


class Attribute(db.Model):

    __tablename__ = 'attributes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    description = db.Column(db.String(50), nullable=False)
    type = db.Column(ChoiceType(AttributeType, impl=db.Integer()))
    dataset_id = db.Column(db.Integer, db.ForeignKey('datasets.id'), nullable=False)

    def __init__(self, description, type, dataset_id):
        self.description = description
        self.type = type
        self.dataset_id = dataset_id

    def __repr__(self):
        return '<Attribute {}>'.format(self.description)
