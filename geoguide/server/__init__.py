# geoguide/server/__init__.py


#################
#### imports ####
#################

import os
import logging
import jwt

from decouple import config

from flask import Flask, render_template
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_debugtoolbar import DebugToolbarExtension
from flask_sqlalchemy import SQLAlchemy
from flask_uploads import UploadSet, configure_uploads
from flask_cors import CORS
from flask_restful import abort


################
#### config ####
################

app = Flask(
    __name__,
    template_folder='../client/templates',
    static_folder='../client/static'
)


app_settings = config(
    'APP_SETTINGS', 'geoguide.server.config.ProductionConfig')
app.config.from_object(app_settings)
logging.basicConfig(filename='geoguide.log', level=logging.DEBUG)

####################
#### extensions ####
####################

login_manager = LoginManager()
login_manager.init_app(app)
bcrypt = Bcrypt(app)
toolbar = DebugToolbarExtension(app)
db = SQLAlchemy(app)
CORS(app)

###################
### flask-login ####
###################

from geoguide.server.models import User


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=int(user_id)).first()


@login_manager.request_loader
def load_user_from_request(request):
    header = request.headers.get('Authorization')
    if not header:
        return None
    prefix, token = header.split()
    if prefix.lower() != app.config.get('JWT_AUTH_HEADER_PREFIX').lower():
        return None
    try:
        payload = jwt.decode(token, app.config.get('SECRET_KEY'))
        return User.query.filter_by(email=payload['email']).first()
    except:
        return None


@login_manager.unauthorized_handler
def unauthorized():
    return abort(401)


###################
##### uploads #####
###################

datasets = UploadSet('datasets', ('csv',))
configure_uploads(app, (datasets))


###################
### blueprints ####
###################

from geoguide.server.main.views import main_blueprint
from geoguide.server.geoguide.views import geoguide_blueprint
from geoguide.server.user.views import user_blueprint

app.register_blueprint(main_blueprint)
app.register_blueprint(geoguide_blueprint)
app.register_blueprint(user_blueprint)

###################
####### api #######
###################

from geoguide.server.auth.resources import auth_blueprint

app.register_blueprint(auth_blueprint)


########################
#### error handlers ####
########################

# @app.errorhandler(401)
# def unauthorized_page(error):
#     return render_template("errors/401.html"), 401


# @app.errorhandler(403)
# def forbidden_page(error):
#     return render_template("errors/403.html"), 403


# @app.errorhandler(404)
# def page_not_found(error):
#     return render_template("errors/404.html"), 404


# @app.errorhandler(500)
# def server_error_page(error):
#     return render_template("errors/500.html"), 500
