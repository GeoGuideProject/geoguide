import jwt
import arrow

from flask import Blueprint

from flask_restful import Api, Resource, marshal_with, reqparse, abort, fields
from flask_login import current_user, login_required

from geoguide.server import app, db
from geoguide.server.models import User

auth_blueprint = Blueprint('api_auth', __name__)
api = Api(auth_blueprint, prefix='/api', catch_all_404s=True)

user_fields = {
    'email': fields.String,
}

token_fields = {
    'access_token': fields.String
}


class UserBaseResource(Resource):

    def get_user(self, email):
        user = User.query.filter_by(email=email).first_or_404()
        return user

    def is_email_already_registered(self, email):
        user = User.query.filter_by(email=email).first()
        return user is not None


class UserDetail(UserBaseResource):

    put_parser = reqparse.RequestParser()
    put_parser.add_argument('email', type=str)
    put_parser.add_argument('cur_password', type=str)
    put_parser.add_argument('new_password', type=str)

    @marshal_with(user_fields)
    @login_required
    def get(self):
        return current_user

    @login_required
    def delete(self):
        db.session.delete(current_user)
        db.session.commit()
        return {}, 204

    @marshal_with(user_fields)
    @login_required
    def put(self):
        args = self.put_parser.parse_args()
        # Update password if current one matches
        if None not in [args['cur_password'], args['new_password']]:
            if current_user.check_password(args['cur_password']):
                current_user.set_password(args['new_password'])
            else:
                abort(400, message='Invalid password')
        if args['email'] is not None:
            current_user.email = args['email']
        db.session.add(current_user)
        db.session.commit()
        return current_user, 200


class UserRegister(UserBaseResource):

    parser = reqparse.RequestParser()
    parser.add_argument('email', type=str)
    parser.add_argument('password', type=str, required=True)
    parser.add_argument('confirm_password', type=str, required=True)

    @marshal_with(user_fields)
    def post(self):
        parsed_args = self.parser.parse_args()
        if self.is_email_already_registered(parsed_args['email']):
            abort(400, message='Email already registered.')
        if parsed_args['password'] != parsed_args['confirm_password']:
            abort(400, message='Passwords does not match.')

        user = User(
            parsed_args['email'],
            parsed_args['password'],
        )
        db.session.add(user)
        db.session.commit()
        return user, 201


class AuthToken(UserBaseResource):

    token_parser = reqparse.RequestParser()
    token_parser.add_argument('email', type=str)
    token_parser.add_argument('password', type=str)

    @marshal_with(token_fields)
    def post(self):
        args = self.token_parser.parse_args()
        user = self.get_user(args['email'])
        if user.check_password(args['password']):
            iat = arrow.utcnow()
            token = jwt.encode({
                'email': user.email,
                'orig_iat': iat.timestamp,
                'iat': iat.timestamp,
                'exp': iat.replace(seconds=app.config.get('JWT_EXPIRATION_SECONDS')).timestamp
            }, app.config.get('SECRET_KEY'), algorithm=app.config.get('JWT_ALGORITHM'))
            return {'access_token': token.decode('utf-8')}, 200
        else:
            abort(401, message='Invalid credentials')


class AuthRefreshToken(UserBaseResource):
    token_parser = reqparse.RequestParser()
    token_parser.add_argument('token', type=str)

    @marshal_with(token_fields)
    def post(self):
        args = self.token_parser.parse_args()
        try:
            payload = jwt.decode(args['token'], app.config.get('SECRET_KEY'))
        except:
            payload = None
        if payload is not None:
            iat = arrow.utcnow()
            orig_iat = arrow.get(payload['orig_iat'])
            exp_orig_iat = orig_iat.replace(
                seconds=app.config.get('JWT_REFRESH_EXPIRATION_SECONDS'))
            if exp_orig_iat.timestamp > iat.timestamp:
                token = jwt.encode({
                    'email': payload['email'],
                    'orig_iat': orig_iat.timestamp,
                    'iat': iat.timestamp,
                    'exp': iat.replace(seconds=app.config.get('JWT_EXPIRATION_SECONDS')).timestamp
                }, app.config.get('SECRET_KEY'), algorithm=app.config.get('JWT_ALGORITHM'))
                return {'access_token': token.decode('utf-8')}, 200
        abort(401, message='Invalid token')


api.add_resource(AuthToken, '/token')
api.add_resource(AuthRefreshToken, '/token/refresh')
api.add_resource(UserDetail, '/me')
api.add_resource(UserRegister, '/register')
