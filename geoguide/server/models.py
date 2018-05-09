# geoguide/server/models.py

import datetime
import enum
from geoguide.server import app, db, bcrypt
from sqlalchemy_utils import ChoiceType
from flask_login import current_user
from geoalchemy2 import Geometry


class User(db.Model):

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    registered_on = db.Column(db.DateTime, nullable=False)
    admin = db.Column(db.Boolean, nullable=False, default=False)
    datasets = db.relationship('Dataset', backref='user', cascade='all, delete-orphan')

    def __init__(self, email, password, admin=False):
        self.email = email
        self.password = bcrypt.generate_password_hash(
            password, app.config.get('BCRYPT_LOG_ROUNDS')
        ).decode('utf-8')
        self.registered_on = datetime.datetime.now()
        self.admin = admin

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    def __repr__(self):
        return '<User {0}>'.format(self.email)


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
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


    def __init__(self, title, filename, number_of_rows=None, latitude_attr=None, longitude_attr=None):
        self.title = title
        self.filename = filename
        self.number_of_rows = number_of_rows
        self.latitude_attr = latitude_attr
        self.longitude_attr = longitude_attr
        self.created_at = datetime.datetime.now()
        self.user_id = current_user.id


    def __repr__(self):
        return '<Dataset {}>'.format(self.filename)


class AttributeType(enum.Enum):
    datetime = 1
    number = 2
    text = 3
    categorical_number = 4
    categorical_text = 5


class Attribute(db.Model):

    __tablename__ = 'attributes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    description = db.Column(db.String(50), nullable=False)
    type = db.Column(ChoiceType(AttributeType, impl=db.Integer()))
    dataset_id = db.Column(db.Integer, db.ForeignKey('datasets.id'), nullable=False)
    visible = db.Column(db.Boolean, default=True)

    def __init__(self, description, type, dataset_id, visible=True):
        self.description = description
        self.type = type
        self.dataset_id = dataset_id
        self.visible = visible

    def __repr__(self):
        return '<Attribute {}>'.format(self.description)


class Session(db.Model):

    __tablename__ = 'sessions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    dataset_id = db.Column(db.Integer, db.ForeignKey('datasets.id'))

    def __init__(self, dataset):
        self.user_id = current_user.id
        self.created_at = datetime.datetime.now()
        self.dataset_id = dataset.id

    def __repr__(self):
        return '<Session {}>'.format(self.created_at)


class Polygon(db.Model):

    __tablename__ = 'polygons'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    geom =  db.Column(Geometry('POLYGON'))
    created_at = db.Column(db.DateTime, nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)
    iteration = db.Column(db.Integer)

    def __init__(self, geom, iteration):
        from geoguide.server.services import current_session

        self.geom = geom
        self.iteration = iteration
        self.session_id = current_session().id
        self.created_at = datetime.datetime.now()


    def __repr__(self):
        return '<Polygon {}>'.format(self.id)


class IDR(db.Model):

    __tablename__ = 'idrs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    geom =  db.Column(Geometry('POLYGON'))
    created_at = db.Column(db.DateTime, nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)
    iteration = db.Column(db.Integer)

    def __init__(self, geom, iteration):
        from geoguide.server.services import current_session

        self.geom = geom
        self.iteration = iteration
        self.session_id = current_session().id
        self.created_at = datetime.datetime.now()

    def __repr__(self):
        return '<IDR {}>'.format(self.id)

