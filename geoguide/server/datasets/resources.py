import jwt
import arrow

from flask import Blueprint

from flask_restful import Api, Resource, marshal_with, reqparse, abort, fields
from flask_login import current_user, login_required

from geoguide.server import app, db
from geoguide.server.models import Dataset, AttributeType

datasets_blueprint = Blueprint('api_datasets', __name__)
api = Api(datasets_blueprint, prefix='/api', catch_all_404s=True)


attribute_fields = {
    'description': fields.String,
    'type': fields.String(attribute=lambda x: x.type.name),
    'visible': fields.Boolean
}


dataset_fields = {
    'id': fields.String(attribute=lambda x: x.filename.rsplit('.')[0]),
    'title': fields.String,
    'filename': fields.String,
    'latitude_attr': fields.String,
    'longitude_attr': fields.String,
    'created_at': fields.DateTime(dt_format='iso8601'),
    'indexed_at': fields.DateTime(dt_format='iso8601'),
    'attributes': fields.List(fields.Nested(attribute_fields))
}


class DatasetBaseResource(Resource):

    def get_dataset(self, uuid):
        filename = '{}.csv'.format(uuid)
        return Dataset.query.filter_by(user_id=current_user.id, filename=filename).first_or_404()

    def get_datasets(self):
        return Dataset.query.filter_by(user_id=current_user.id).all()


class DatasetDetail(DatasetBaseResource):

    @marshal_with(dataset_fields)
    @login_required
    def get(self, uuid):
        return self.get_dataset(uuid)


class DatasetList(DatasetBaseResource):

    @marshal_with(dataset_fields)
    @login_required
    def get(self):
        return self.get_datasets()


api.add_resource(DatasetDetail, "/datasets/<string:uuid>")
api.add_resource(DatasetList, "/datasets")
